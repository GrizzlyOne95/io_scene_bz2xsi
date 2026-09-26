import sys, os, glob, re, io, contextlib, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bz2xsi
root = sys.argv[1]  # usage: python tests/xsi_parse_corpus.py <folder of .xsi files>
files = sorted(set(glob.glob(root + "/**/*.xsi", recursive=True) + glob.glob(root + "/**/*.XSI", recursive=True)))
fails = collections.Counter(); ex = {}; skinned = anim = 0; after_env = []; msgs = collections.Counter()
for p in files:
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            x = bz2xsi.read(p)
        skinned += x.is_skinned(); anim += x.is_animated()
    except Exception as e:
        k = type(e).__name__ + ": " + re.sub(r"\S+\.xsi:\d+:\d+:", "", str(e))[:70]
        fails[k] += 1; ex.setdefault(k, p)
    for line in buf.getvalue().splitlines():
        msgs[re.sub(r"'[^']*'|\d+", "#", re.sub(r"^.*?\.xsi:\d+:\d+:", "", line))] += 1
    t = open(p, errors="replace").read()
    m = re.search(r"(?im)^\s*SI_EnvelopeList\b", t)
    if m and re.search(r"(?im)^\s*(AnimationSet|Frame|SI_Light|SI_Camera)\b", t[m.end():]): after_env.append(p)
print("files", len(files), "skinned", skinned, "animated", anim)
for k, v in fails.most_common(): print("FAIL", v, k, "e.g.", ex[k])
for k, v in msgs.most_common(15): print("MSG", v, k)
print("blocks after SI_EnvelopeList:", len(after_env), after_env[:5])
