"""Blender regression tests for io_scene_bz2xsi.

usage: blender -b --factory-startup -P tests/xsi_blender_tests.py -- [test names]
Environment:
  XSI_CORPUS_SRC  folder of real BZ2/BZCC XSI files (e.g. CombatCommanderSourceMaterialModsv2),
                  used by corpus_src, skin_*, edge_*, object_anim and roundtrip
  XSI_DEMO_DIR    folder holding the BZ2 demo data.pak and its extraction in <dir>/pak,
                  used by corpus_demo and pak_operator
The skinned tests compare Blender's deformed mesh with a numpy re-implementation of XSI
skinning: sum(w * W_anim(bone) @ W_base(bone)^-1 @ W_base(mesh) @ v), weights normalised.
"""
import bpy, sys, os, glob, math, io, contextlib, traceback, time
import numpy as np
from mathutils import Matrix, Quaternion, Euler, Vector
sys.path.insert(0, os.environ.get("XSI_ADDON_PARENT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from importlib import import_module
imp = import_module("io_scene_bz2xsi.xsi_blender_importer")
exp = import_module("io_scene_bz2xsi.xsi_blender_exporter")
bz2xsi = import_module("io_scene_bz2xsi.bz2xsi")
SRC = os.environ.get("XSI_CORPUS_SRC", "")
import tempfile
DEMO_DIR = os.environ.get("XSI_DEMO_DIR", "")
DEMO = os.path.join(DEMO_DIR, "pak")
TMP = os.path.join(tempfile.gettempdir(), "io_scene_bz2xsi_tests")
IOPT = dict(emulate_flags=True, import_animations=True, import_envelopes=True, import_lights=False, import_cameras=False,
            import_mesh=True, import_mesh_normals=True, import_mesh_materials=True, import_mesh_uvmap=True,
            import_mesh_vertcolor=True, find_textures=False, find_textures_ext=".pic .png .tga .dds",
            convert_pic_textures=False, auto_convert_dxtbz2=False, add_material_overrides=True,
            place_at_cursor=False, rotate_for_yz=True, quat_anims_to_euler=False, remove_negative_rotations=False)
EOPT = dict(export_mode="ACTIVE_COLLECTION", export_mesh=True, export_mesh_uvmap=True, export_mesh_materials=True,
            export_mesh_vertcolor=True, export_envelopes=True, export_animations=True, zero_root_transforms=True,
            generate_empty_mesh=False, generate_bone_mesh=False)


def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path, **kw):
    o = dict(IOPT); o.update(kw)
    with contextlib.redirect_stdout(io.StringIO()) as b:
        imp.load(None, bpy.context, filepath=path, **o)
    return b.getvalue()


def save(path, **kw):
    o = dict(EOPT); o.update(kw)
    with contextlib.redirect_stdout(io.StringIO()) as b:
        exp.save(None, bpy.context, filepath=path, **o)
    return b.getvalue()


def run(name, fn):
    try: print("TEST", name, "->", fn(), flush=True)
    except Exception as e:
        print("TEST", name, "-> EXCEPTION", type(e).__name__, e, flush=True); traceback.print_exc(limit=-2)


def write(name, text):
    p = os.path.join(TMP, name); open(p, "w").write(text); return p


HDR = "xsi 0101txt 0032\n"


def frame(name, pos=(0, 0, 0), body=""):
    return ("Frame frm-%s {\nFrameTransformMatrix {\n1,0,0,0,\n0,1,0,0,\n0,0,1,0,\n%f,%f,%f,1;;\n}\n%s}\n"
            % (name, *pos, body))


def tri_mesh(name, verts=((0, 0, 0), (1, 0, 0), (0, 1, 0)), tex=None, extra=""):
    t = 'SI_Texture2D {\n"%s";\n}\n' % tex if tex else ""
    return ("Mesh %s {\n3;\n%s;\n1;\n3;0,1,2;;\nMeshMaterialList {\n1;\n1;\n0;\nSI_Material {\n1;1;1;1;;\n50;\n1;1;1;;\n0;0;0;;\n2;\n0;0;0;;\n%s}\n}\n%s}\n"
            % (name, ",\n".join("%f;%f;%f;" % v for v in verts), t, extra))


def corpus(folder):
    files = sorted(glob.glob(folder + "/**/*.xsi", recursive=True)); bad = []; notes = 0
    t = time.time(); skinned = anim = 0
    for p in files:
        reset(); t0 = time.time()
        print("  loading", os.path.basename(p), flush=True)
        try:
            out = load(p); notes += bool(out.strip())
            anim += any(o.animation_data for o in bpy.data.objects)
            skinned += any(o.type == "ARMATURE" for o in bpy.data.objects)
        except Exception as e:
            bad.append((os.path.basename(p), type(e).__name__, str(e)[:80]))
        if time.time() - t0 > 5: print("  SLOW %.0fs %s" % (time.time() - t0, os.path.basename(p)), flush=True)
    return "files %d failures %d animated %d skinned %d (%.0fs) %s" % (len(files), len(bad), anim, skinned, time.time() - t, bad[:6])


# ---- numpy reference for XSI transforms / skinning ----
def M(m): return np.array(m.to_list()).T


def sample(keys, f):
    if f <= keys[0][0]: return np.array(keys[0][1])
    for (f0, a), (f1, b) in zip(keys, keys[1:]):
        if f0 <= f <= f1: a, b = np.array(a), np.array(b); return a + (b - a) * (f - f0) / (f1 - f0)
    return np.array(keys[-1][1])


def local_anim(fr, f):
    L = M(fr.transform)
    for k in fr.animation_keys:
        if k.key_type == 0:
            w, x, y, z = sample(k.keys, f)
            L[:3, :3] = np.array(Quaternion((w, -x, -y, -z)).normalized().to_matrix())
        elif k.key_type == 2:
            L[:3, 3] = sample(k.keys, f)
    return L


def world(fr, fn):
    W = fn(fr)
    while fr.parent: fr = fr.parent; W = fn(fr) @ W
    return W


def reference_skin(mf, f):
    V = np.c_[np.array(mf.mesh.vertices), np.ones(len(mf.mesh.vertices))]
    base = lambda fr: M(fr.pose or fr.transform)
    S = np.zeros((len(V), 3)); Wm = world(mf, base); total = np.zeros(len(V))
    for env in mf.envelopes:
        K = world(env.bone, lambda fr: local_anim(fr, f)) @ np.linalg.inv(world(env.bone, base)) @ Wm
        for vi, w in env.vertices: S[vi] += w / 100 * (K @ V[vi])[:3]; total[vi] += w / 100
    S /= np.maximum(total, 1e-9)[:, None]  # weights normalised per vertex, as Blender's armature modifier does
    conv = np.array(Euler((math.pi / 2, 0, math.pi)).to_matrix())
    return (conv @ S.T).T


def skinned(fname, frames):
    path = glob.glob(SRC + "/**/" + fname, recursive=True)[0]
    x = bz2xsi.read(path); mf = next(x.get_skinned_frames())
    reset(); load(path); out = []
    size = np.ptp(np.array(mf.mesh.vertices), axis=0).max()
    for f in frames:
        bpy.context.scene.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects[mf.name].evaluated_get(dg)
        got = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
        out.append("f%d %.2f" % (f, np.abs(got - reference_skin(mf, f)).max()))
    return "model size %.1f, max vertex error: %s" % (size, ", ".join(out))


def object_anim():
    path = glob.glob(SRC + "/**/mcwing_fly.xsi", recursive=True)[0]
    x = bz2xsi.read(path); fr = x.frame_table["jnt17_2"]
    reset(); load(path, import_envelopes=False); bpy.context.scene.frame_set(1)
    got = bpy.data.objects["jnt17_2"].matrix_local.to_quaternion()
    want = Matrix(local_anim(fr, 1).tolist()).to_quaternion()
    return "jnt17_2 @f1 local rotation: expected %.1f deg about %s, imported %.1f deg about %s" % (
        math.degrees(want.angle), tuple(round(c, 2) for c in want.axis), math.degrees(got.angle), tuple(round(c, 2) for c in got.axis))


def yz_offset():
    reset(); load(write("a.xsi", HDR + frame("root", (0, 0, 0), tri_mesh("root", ((1, 2, 3), (1, 2, 3.5), (1, 2.5, 3))))))
    bpy.context.view_layer.update(); a = bpy.data.objects["root"].matrix_world @ bpy.data.objects["root"].data.vertices[0].co
    reset(); load(write("b.xsi", HDR + frame("root", (1, 2, 3), tri_mesh("root", ((0, 0, 0), (0, 0, .5), (0, .5, 0))))))
    bpy.context.view_layer.update(); b = bpy.data.objects["root"].matrix_world @ bpy.data.objects["root"].data.vertices[0].co
    return "XSI point (1,2,3): as vertex -> %s, as root offset -> %s" % (tuple(round(c, 2) for c in a), tuple(round(c, 2) for c in b))


def chrome():
    reset(); load(write("c.xsi", HDR + frame("root", body=tri_mesh("root", tex="reflection3.tga"))))
    b = next(n for n in bpy.data.objects["root"].data.materials[0].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return "Metallic %.1f Roughness %.2f; code writes inputs[4]=%r inputs[7]=%r" % (
        b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value, b.inputs[4].name, b.inputs[7].name)


def bone_parent_gap():
    body = frame("A", (0, 1, 0), frame("G", (0, 1, 0), frame("B", (0, 1, 0))))
    env = ('SI_EnvelopeList {\n2;\nSI_Envelope {\n"frm-skin";\n"frm-A";\n1;\n0;100.0;;\n}\n'
           'SI_Envelope {\n"frm-skin";\n"frm-B";\n1;\n1;100.0;;\n}\n}\n')
    reset(); load(write("d.xsi", HDR + frame("root", body=frame("skin", body=tri_mesh("skin")) + body) + env))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    p = arm.data.bones["B"].parent
    return "bone B (grandchild of bone A via plain frame G) parent = %r" % (p.name if p else None)


def env_then_anim():
    env = 'SI_EnvelopeList {\n1;\nSI_Envelope {\n"frm-skin";\n"frm-A";\n1;\n0;100.0;;\n}\n}\n'
    anim = "AnimationSet {\nAnimation anim-A {\n{frm-A}\nSI_AnimationKey {\n2;\n1;\n1;3;0,5,0;;;\n}\n}\n}\n"
    x = bz2xsi.read(write("e.xsi", HDR + frame("skin", body=tri_mesh("skin") + frame("A")) + env + anim))
    return "AnimationSet after SI_EnvelopeList: frame A has %d anim key block(s), expected 1" % len(x.frame_table["A"].animation_keys)


def writer_vcol():
    vc = "SI_MeshVertexColors {\n1;\n1;0;0;1;;\n1;\n0;3;0,0,0;;\n}\n"
    x = bz2xsi.read(write("f.xsi", HDR + frame("m", body=tri_mesh("m", extra=vc))))
    x.write(os.path.join(TMP, "f_out.xsi"))
    try:
        y = bz2xsi.read(os.path.join(TMP, "f_out.xsi"))
        return "re-read colours %s faces %s" % (y.frame_table["m"].mesh.vertex_colors, y.frame_table["m"].mesh.vertex_color_faces)
    except Exception as e:
        return "written file unreadable: %s: %s" % (type(e).__name__, e)


def new_obj(name, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.parent = parent; o.location = loc
    return o


def ex_dupkeys():
    reset(); root = new_obj("root"); o = new_obj("a", root)
    for f, z in ((1, 0), (10, 5)): o.location.z = z; o.keyframe_insert("location", frame=f)
    save(os.path.join(TMP, "g.xsi")); x = bz2xsi.read(os.path.join(TMP, "g.xsi"))
    return "location keyed on 2 frames -> exported key frames %s" % [k for k, v in x.frame_table["a"].animation_keys[0].keys]


def ex_siblings():
    reset(); root = new_obj("root"); a = new_obj("a", root); b = new_obj("b", root)
    for o in (a, b):
        for f, z in ((1, 0), (10, 5)): o.location.z = z; o.keyframe_insert("location", frame=f)
    bpy.context.scene.frame_set(1); save(os.path.join(TMP, "h.xsi")); x = bz2xsi.read(os.path.join(TMP, "h.xsi"))
    return "rest Z (pose at frame_start is 0 for both): a=%.1f b=%.1f" % (x.frame_table["a"].transform.posit[2], x.frame_table["b"].transform.posit[2])


def ex_empty_slot():
    reset(); o = new_obj("root"); o.data.materials.append(None); save(os.path.join(TMP, "i.xsi")); return "ok"


def ex_bone_mesh():
    reset(); arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig")); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
    arm.data.edit_bones.new("b").tail = (0, 0, 1); bpy.ops.object.mode_set(mode="OBJECT")
    save(os.path.join(TMP, "j.xsi"), generate_bone_mesh=True); return "ok"


def ex_selected():
    reset(); root = new_obj("root"); c = new_obj("child", root); root.select_set(True); c.select_set(True)
    save(os.path.join(TMP, "k.xsi"), export_mode="SELECTED_OBJECTS"); x = bz2xsi.read(os.path.join(TMP, "k.xsi"))
    return "select parent+child -> frames written %s" % [f.get_chained_name("/") for f in x.get_all_frames()]


def ex_texture():
    reset(); o = new_obj("root"); m = bpy.data.materials.new("m")
    n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.new("tex", 4, 4); n.image.filepath = "C:\\Mods\\textures\\ivtank.tga"
    o.data.materials.append(m); save(os.path.join(TMP, "l.xsi")); x = bz2xsi.read(os.path.join(TMP, "l.xsi"))
    return "texture written as %r" % x.frame_table["root"].mesh.face_materials[0].texture


def ex_skin_pose():
    reset(); root = new_obj("root")
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig")); bpy.context.scene.collection.objects.link(arm); arm.parent = root
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
    arm.data.edit_bones.new("b").tail = (0, 0, 1); bpy.ops.object.mode_set(mode="OBJECT")
    sk = new_obj("skin", root); sk.vertex_groups.new(name="b").add([0, 1, 2], 1.0, "REPLACE")
    sk.modifiers.new("Armature", "ARMATURE").object = arm
    pb = arm.pose.bones["b"]
    pb.location = (0, 3, 0); pb.keyframe_insert("location", frame=1); pb.location = (0, 0, 0); pb.keyframe_insert("location", frame=10)
    bpy.context.scene.frame_set(1); save(os.path.join(TMP, "n.xsi")); x = bz2xsi.read(os.path.join(TMP, "n.xsi"))
    return "rest vertex (0,0,0) exported as %s" % (tuple(round(c, 2) for c in x.frame_table["skin"].mesh.vertices[0]),)


def roundtrip(name):
    path = glob.glob(SRC + "/**/" + name, recursive=True)[0]
    def pts(): return sorted(tuple(round(c, 3) for c in o.matrix_world @ v.co) for o in bpy.data.objects if o.type == "MESH" for v in o.data.vertices)
    reset(); load(path, rotate_for_yz=False); a = pts()
    save(os.path.join(TMP, "o.xsi"), zero_root_transforms=False)
    reset(); load(os.path.join(TMP, "o.xsi"), rotate_for_yz=False); b = pts()
    return "%s import->export->import: %d/%d world vertices identical" % (name, sum(p == q for p, q in zip(a, b)), max(len(a), len(b)))


T = dict(corpus_src=lambda: corpus(SRC), corpus_demo=lambda: corpus(DEMO),
         skin_fly=lambda: skinned("mcwing_fly.xsi", (1, 8, 24)), skin_jak=lambda: skinned("jak_kill.xsi", (1, 10, 30)),
         object_anim=object_anim, yz_offset=yz_offset, chrome=chrome, bone_parent_gap=bone_parent_gap,
         env_then_anim=env_then_anim, writer_vcol=writer_vcol, ex_dupkeys=ex_dupkeys, ex_siblings=ex_siblings,
         ex_empty_slot=ex_empty_slot, ex_bone_mesh=ex_bone_mesh, ex_selected=ex_selected, ex_texture=ex_texture,
         ex_skin_pose=ex_skin_pose, roundtrip=lambda: roundtrip("ibnav00.xsi"))
os.makedirs(TMP, exist_ok=True)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for n in (args or list(T)):
    if n in T: run(n, T[n])


def edge_sanity(fname, frames):
    path = glob.glob(SRC + "/**/" + fname, recursive=True)[0]
    x = bz2xsi.read(path); mf = next(x.get_skinned_frames())
    reset(); load(path)
    E = [(f[i], f[(i + 1) % len(f)]) for f in mf.mesh.faces for i in range(len(f))]
    V0 = np.array(mf.mesh.vertices); L0 = np.array([np.linalg.norm(V0[a] - V0[b]) for a, b in E]) + 1e-9
    def dist(P): L = np.array([np.linalg.norm(P[a] - P[b]) for a, b in E]); return np.median(np.abs(L / L0 - 1)) * 100, np.percentile(np.abs(L / L0 - 1), 95) * 100
    out = []
    for f in frames:
        bpy.context.scene.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects[mf.name].evaluated_get(dg)
        got = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
        out.append("f%d ref %.1f%%/%.1f%% blender %.1f%%/%.1f%%" % (f, *dist(reference_skin(mf, f)), *dist(got)))
    return "edge stretch median/p95: " + "; ".join(out)


def pak_operator():
    pkg = import_module("io_scene_bz2xsi"); pkg.register()
    try:
        pak = os.path.join(DEMO_DIR, "data.pak"); cache = os.path.join(TMP, "pakcache")
        reset()
        with contextlib.redirect_stdout(io.StringIO()):
            r = bpy.ops.import_scene.io_scene_bz2xsi(filepath=pak, pak_cache_dir=cache,
                pak_xsi_path=chr(92).join(("objects", "ISDF", "people", "rifle", "cockpit", "iwrifl_cockpit_run.xsi")))
        anim = [o.name for o in bpy.data.objects if o.animation_data]
        imgs = sorted(i.name for i in bpy.data.images if i.has_data or os.path.exists(bpy.path.abspath(i.filepath)))
        return "%s, %d objects, %d animated, textures found %s, extracted to its PAK folder: %s" % (r, len(bpy.data.objects), len(anim), imgs[:4],
            os.path.exists(os.path.join(cache, "objects", "ISDF", "people", "rifle", "cockpit", "iwrifl_cockpit_run.xsi")))
    finally:
        pkg.unregister()


T["pak_operator"] = pak_operator
T["edge_fly"] = lambda: edge_sanity("mcwing_fly.xsi", (1, 8, 24))
T["edge_jak"] = lambda: edge_sanity("jak_kill.xsi", (1, 10, 30))
for n in [a for a in args if a in ("edge_fly", "edge_jak", "pak_operator")]: run(n, T[n])
