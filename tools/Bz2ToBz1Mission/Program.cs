using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using BZNParser;
using BZNParser.Battlezone;
using BZNParser.Battlezone.GameObject;
using BZNParser.Reader;

CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;

Options? options;
try
{
    options = Options.Parse(args);
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.Message);
    return 1;
}

if (options is null)
{
    return 1;
}

Directory.CreateDirectory(options.OutputDirectory);

var trnDimensions = options.TrnPath is null ? null : TrnDimensions.Load(options.TrnPath);
var sourceWidth = options.SourceWidth ?? trnDimensions?.Width ?? throw new InvalidOperationException("A source width is required. Pass --source-width or --trn.");
var sourceDepth = options.SourceDepth ?? trnDimensions?.Depth ?? throw new InvalidOperationException("A source depth is required. Pass --source-depth or --trn.");
var targetWidth = options.TargetWidth ?? sourceWidth * (10f / 8f);
var targetDepth = options.TargetDepth ?? sourceDepth * (10f / 8f);
var scaleX = targetWidth / sourceWidth;
var scaleZ = targetDepth / sourceDepth;

var hints = RunWithOptionalConsoleSuppression(options.Verbose, () =>
{
    var parserAssemblyDirectory = Path.GetDirectoryName(typeof(BZNFileBattlezone).Assembly.Location)
        ?? throw new InvalidOperationException("Unable to locate the BZNParser assembly directory.");
    var originalCurrentDirectory = Environment.CurrentDirectory;
    Environment.CurrentDirectory = parserAssemblyDirectory;
    try
    {
        return BattlezoneBZNHints.BuildHintsBZ2();
    }
    finally
    {
        Environment.CurrentDirectory = originalCurrentDirectory;
    }
});

if (hints is null)
{
    Console.Error.WriteLine("Failed to build BZ2 parser hints.");
    return 1;
}

var bzn = RunWithOptionalConsoleSuppression(options.Verbose, () =>
{
    using var file = File.OpenRead(options.InputBznPath);
    using var reader = new BZNStreamReader(file, options.InputBznPath);
    return new BZNFileBattlezone(reader, Hints: hints);
});

var entities = bzn.Entities
    .Select(entity => entity.gameObject)
    .Where(entity => entity is not null)
    .Cast<Entity>()
    .Select(entity => ConvertedEntity.From(entity, scaleX, scaleZ, options.OdfDirectory))
    .ToList();

var inputName = Path.GetFileNameWithoutExtension(options.InputBznPath);
var reportPath = Path.Combine(options.OutputDirectory, $"{inputName}_bz1_entities.tsv");
var skeletonPath = Path.Combine(options.OutputDirectory, $"{inputName}_bz1_skeleton.txt");
var missingOdfsPath = Path.Combine(options.OutputDirectory, $"{inputName}_missing_odfs.txt");

WriteReport(reportPath, entities);
WriteSkeleton(skeletonPath, inputName, entities);
WriteMissingOdfs(missingOdfsPath, entities, options.OdfDirectory);

Console.WriteLine($"Input: {options.InputBznPath}");
Console.WriteLine($"Output directory: {options.OutputDirectory}");
Console.WriteLine($"Source dimensions: {FormatFloat(sourceWidth)} x {FormatFloat(sourceDepth)}");
Console.WriteLine($"Target dimensions: {FormatFloat(targetWidth)} x {FormatFloat(targetDepth)}");
Console.WriteLine($"Scale: X={FormatFloat(scaleX)} Z={FormatFloat(scaleZ)}");
Console.WriteLine($"Entities written: {entities.Count}");
Console.WriteLine($"Report: {reportPath}");
Console.WriteLine($"Skeleton: {skeletonPath}");
if (options.OdfDirectory is not null)
{
    var missingCount = entities.Count(entity => entity.OdfExists == false);
    Console.WriteLine($"Missing ODF report: {missingOdfsPath} ({missingCount} missing)");
}

return 0;

static void WriteReport(string path, IReadOnlyList<ConvertedEntity> entities)
{
    var builder = new StringBuilder();
    builder.AppendLine("seqNo\tPrjID\tClassLabel\tteam\tlabel\tisUser\todfExists\torigPosX\torigPosY\torigPosZ\tbz1PosX\tbz1PosY\tbz1PosZ\torigTransformX\torigTransformY\torigTransformZ\tbz1TransformX\tbz1TransformY\tbz1TransformZ");

    foreach (var entity in entities)
    {
        builder
            .Append(entity.SeqNo).Append('\t')
            .Append(entity.PrjId).Append('\t')
            .Append(entity.ClassLabel).Append('\t')
            .Append(entity.Team).Append('\t')
            .Append(entity.Label).Append('\t')
            .Append(entity.IsUser ? "1" : "0").Append('\t')
            .Append(entity.OdfExists?.ToString() ?? string.Empty).Append('\t')
            .Append(FormatFloat(entity.OriginalPos.x)).Append('\t')
            .Append(FormatFloat(entity.OriginalPos.y)).Append('\t')
            .Append(FormatFloat(entity.OriginalPos.z)).Append('\t')
            .Append(FormatFloat(entity.ConvertedPos.x)).Append('\t')
            .Append(FormatFloat(entity.ConvertedPos.y)).Append('\t')
            .Append(FormatFloat(entity.ConvertedPos.z)).Append('\t')
            .Append(FormatFloat(entity.OriginalTransform.posit.x)).Append('\t')
            .Append(FormatFloat(entity.OriginalTransform.posit.y)).Append('\t')
            .Append(FormatFloat(entity.OriginalTransform.posit.z)).Append('\t')
            .Append(FormatFloat(entity.ConvertedTransform.posit.x)).Append('\t')
            .Append(FormatFloat(entity.ConvertedTransform.posit.y)).Append('\t')
            .Append(FormatFloat(entity.ConvertedTransform.posit.z)).AppendLine();
    }

    File.WriteAllText(path, builder.ToString(), Encoding.ASCII);
}

static void WriteSkeleton(string path, string inputName, IReadOnlyList<ConvertedEntity> entities)
{
    var builder = new StringBuilder();
    builder.AppendLine("version [1] =");
    builder.AppendLine("2016");
    builder.AppendLine("binarySave [1] =");
    builder.AppendLine("false");
    builder.AppendLine($"msn_filename = {inputName}_bz1_skeleton.bzn");
    builder.AppendLine("seq_count [1] =");
    builder.AppendLine(entities.Count.ToString(CultureInfo.InvariantCulture));
    builder.AppendLine("missionSave [1] =");
    builder.AppendLine("true");
    builder.AppendLine($"TerrainName = {inputName}");
    builder.AppendLine("size [1] =");
    builder.AppendLine(entities.Count.ToString(CultureInfo.InvariantCulture));

    foreach (var entity in entities)
    {
        builder.AppendLine("[GameObject]");
        builder.AppendLine("PrjID [1] =");
        builder.AppendLine(entity.PrjId);
        builder.AppendLine("seqno [1] =");
        builder.AppendLine(entity.SeqNo.ToString(CultureInfo.InvariantCulture));
        builder.AppendLine("pos [1] =");
        WriteVectorOld(builder, entity.ConvertedPos);
        builder.AppendLine("team [1] =");
        builder.AppendLine(entity.Team.ToString(CultureInfo.InvariantCulture));
        builder.AppendLine($"label = {entity.Label}");
        builder.AppendLine("isUser [1] =");
        builder.AppendLine(entity.IsUser ? "1" : "0");
        builder.AppendLine($"obj_addr = {entity.ObjAddr:X8}");
        builder.AppendLine("transform [1] =");
        WriteMatrixOld(builder, entity.ConvertedTransform);
    }

    File.WriteAllText(path, builder.ToString(), Encoding.ASCII);
}

static void WriteMissingOdfs(string path, IReadOnlyList<ConvertedEntity> entities, string? odfDirectory)
{
    if (odfDirectory is null)
    {
        return;
    }

    var missing = entities
        .Where(entity => entity.OdfExists == false)
        .Select(entity => entity.PrjId)
        .Distinct(StringComparer.OrdinalIgnoreCase)
        .OrderBy(value => value, StringComparer.OrdinalIgnoreCase)
        .ToList();

    File.WriteAllLines(path, missing, Encoding.ASCII);
}

static void WriteVectorOld(StringBuilder builder, Vector3D vector)
{
    builder.AppendLine("  x [1] =");
    builder.AppendLine(FormatFloat(vector.x));
    builder.AppendLine("  y [1] =");
    builder.AppendLine(FormatFloat(vector.y));
    builder.AppendLine("  z [1] =");
    builder.AppendLine(FormatFloat(vector.z));
}

static void WriteMatrixOld(StringBuilder builder, Matrix matrix)
{
    builder.AppendLine("  right_x [1] =");
    builder.AppendLine(FormatFloat(matrix.right.x));
    builder.AppendLine("  right_y [1] =");
    builder.AppendLine(FormatFloat(matrix.right.y));
    builder.AppendLine("  right_z [1] =");
    builder.AppendLine(FormatFloat(matrix.right.z));
    builder.AppendLine("  up_x [1] =");
    builder.AppendLine(FormatFloat(matrix.up.x));
    builder.AppendLine("  up_y [1] =");
    builder.AppendLine(FormatFloat(matrix.up.y));
    builder.AppendLine("  up_z [1] =");
    builder.AppendLine(FormatFloat(matrix.up.z));
    builder.AppendLine("  front_x [1] =");
    builder.AppendLine(FormatFloat(matrix.front.x));
    builder.AppendLine("  front_y [1] =");
    builder.AppendLine(FormatFloat(matrix.front.y));
    builder.AppendLine("  front_z [1] =");
    builder.AppendLine(FormatFloat(matrix.front.z));
    builder.AppendLine("  posit_x [1] =");
    builder.AppendLine(FormatFloat(matrix.posit.x));
    builder.AppendLine("  posit_y [1] =");
    builder.AppendLine(FormatFloat(matrix.posit.y));
    builder.AppendLine("  posit_z [1] =");
    builder.AppendLine(FormatFloat(matrix.posit.z));
}

static string FormatFloat(float value)
{
    return value.ToString("G9", CultureInfo.InvariantCulture);
}

static T RunWithOptionalConsoleSuppression<T>(bool verbose, Func<T> action)
{
    if (verbose)
    {
        return action();
    }

    var originalOut = Console.Out;
    try
    {
        Console.SetOut(TextWriter.Null);
        return action();
    }
    finally
    {
        Console.SetOut(originalOut);
    }
}

sealed record ConvertedEntity(
    uint SeqNo,
    string PrjId,
    string ClassLabel,
    uint Team,
    string Label,
    bool IsUser,
    uint ObjAddr,
    Vector3D OriginalPos,
    Vector3D ConvertedPos,
    Matrix OriginalTransform,
    Matrix ConvertedTransform,
    bool? OdfExists)
{
    public static ConvertedEntity From(Entity entity, float scaleX, float scaleZ, string? odfDirectory)
    {
        var originalPos = HasMeaningfulPosition(entity.pos) ? entity.pos : entity.transform.posit;
        var convertedPos = originalPos;
        convertedPos.x *= scaleX;
        convertedPos.z *= scaleZ;

        var convertedTransform = entity.transform;
        convertedTransform.posit.x *= scaleX;
        convertedTransform.posit.z *= scaleZ;

        bool? odfExists = null;
        if (odfDirectory is not null)
        {
            var odfPath = Path.Combine(odfDirectory, $"{entity.PrjID}.odf");
            odfExists = File.Exists(odfPath);
        }

        return new ConvertedEntity(
            entity.seqNo,
            entity.PrjID,
            entity.ClassLabel,
            entity.team,
            entity.label,
            entity.isUser,
            entity.obj_addr,
            originalPos,
            convertedPos,
            entity.transform,
            convertedTransform,
            odfExists);
    }

    static bool HasMeaningfulPosition(Vector3D vector)
    {
        return vector.x != 0f || vector.y != 0f || vector.z != 0f;
    }
}

sealed class Options
{
    public required string InputBznPath { get; init; }
    public required string OutputDirectory { get; init; }
    public string? TrnPath { get; init; }
    public float? SourceWidth { get; init; }
    public float? SourceDepth { get; init; }
    public float? TargetWidth { get; init; }
    public float? TargetDepth { get; init; }
    public string? OdfDirectory { get; init; }
    public bool Verbose { get; init; }

    public static Options? Parse(string[] args)
    {
        if (args.Length == 0 || args.Contains("--help", StringComparer.OrdinalIgnoreCase) || args.Contains("-h", StringComparer.OrdinalIgnoreCase))
        {
            PrintUsage();
            return null;
        }

        string? input = null;
        string? output = null;
        string? trn = null;
        string? odfDirectory = null;
        float? sourceWidth = null;
        float? sourceDepth = null;
        float? targetWidth = null;
        float? targetDepth = null;
        var verbose = false;

        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            var next = i + 1 < args.Length ? args[i + 1] : null;

            switch (arg)
            {
                case "--input":
                    input = RequireValue(arg, next);
                    i++;
                    break;
                case "--output-dir":
                    output = RequireValue(arg, next);
                    i++;
                    break;
                case "--trn":
                    trn = RequireValue(arg, next);
                    i++;
                    break;
                case "--source-width":
                    sourceWidth = ParseFloat(arg, next);
                    i++;
                    break;
                case "--source-depth":
                    sourceDepth = ParseFloat(arg, next);
                    i++;
                    break;
                case "--target-width":
                    targetWidth = ParseFloat(arg, next);
                    i++;
                    break;
                case "--target-depth":
                    targetDepth = ParseFloat(arg, next);
                    i++;
                    break;
                case "--odf-dir":
                    odfDirectory = RequireValue(arg, next);
                    i++;
                    break;
                case "--verbose":
                    verbose = true;
                    break;
                default:
                    throw new ArgumentException($"Unknown argument: {arg}");
            }
        }

        if (input is null)
        {
            throw new ArgumentException("--input is required.");
        }

        output ??= Path.Combine(Path.GetDirectoryName(input) ?? Environment.CurrentDirectory, "bz1_reverse_out");

        return new Options
        {
            InputBznPath = Path.GetFullPath(input),
            OutputDirectory = Path.GetFullPath(output),
            TrnPath = trn is null ? null : Path.GetFullPath(trn),
            SourceWidth = sourceWidth,
            SourceDepth = sourceDepth,
            TargetWidth = targetWidth,
            TargetDepth = targetDepth,
            OdfDirectory = odfDirectory is null ? null : Path.GetFullPath(odfDirectory),
            Verbose = verbose,
        };
    }

    static string RequireValue(string argName, string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException($"{argName} requires a value.");
        }

        return value;
    }

    static float ParseFloat(string argName, string? value)
    {
        var parsed = RequireValue(argName, value);
        if (!float.TryParse(parsed, NumberStyles.Float | NumberStyles.AllowThousands, CultureInfo.InvariantCulture, out var result))
        {
            throw new ArgumentException($"{argName} requires a numeric value.");
        }

        return result;
    }

    static void PrintUsage()
    {
        Console.WriteLine("Usage:");
        Console.WriteLine("  dotnet run --project tools/Bz2ToBz1Mission -- --input <path> [--trn <path>] [--output-dir <path>]");
        Console.WriteLine("      [--source-width <value> --source-depth <value>]");
        Console.WriteLine("      [--target-width <value> --target-depth <value>]");
        Console.WriteLine("      [--odf-dir <path>] [--verbose]");
        Console.WriteLine();
        Console.WriteLine("If --target-width/--target-depth are omitted, the tool uses the BZ1:BZ2 terrain ratio of 10:8.");
    }
}

sealed record TrnDimensions(float Width, float Depth)
{
    static readonly Regex WidthPattern = new(@"^\s*Width\s*=\s*(?<value>[-+]?\d+(?:\.\d+)?)\s*$", RegexOptions.IgnoreCase | RegexOptions.Multiline);
    static readonly Regex DepthPattern = new(@"^\s*Depth\s*=\s*(?<value>[-+]?\d+(?:\.\d+)?)\s*$", RegexOptions.IgnoreCase | RegexOptions.Multiline);

    public static TrnDimensions Load(string path)
    {
        var text = File.ReadAllText(path);
        var widthMatch = WidthPattern.Match(text);
        var depthMatch = DepthPattern.Match(text);

        if (!widthMatch.Success || !depthMatch.Success)
        {
            throw new InvalidOperationException($"Unable to read Width/Depth from TRN: {path}");
        }

        var width = float.Parse(widthMatch.Groups["value"].Value, CultureInfo.InvariantCulture);
        var depth = float.Parse(depthMatch.Groups["value"].Value, CultureInfo.InvariantCulture);
        return new TrnDimensions(width, depth);
    }
}
