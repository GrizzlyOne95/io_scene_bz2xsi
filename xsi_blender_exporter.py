import bpy
import ntpath
from mathutils import Matrix, Vector

from . import bz2xsi

# Normals changed in 4.1 from 4.0
OLD_NORMALS = bpy.app.version < (4, 1, 0)

USE_FRAME_NAME_AS_MESH_NAME = True
ALLOW_MESH_WITH_NO_FACES = False
ALLOW_MESH_WITH_NO_MATERIAL = False
ALLOW_ROOT_LEVEL_ANIMS = True

KEYFRAME_PATHS = {"location", "rotation_euler", "rotation_quaternion"}
ALLOWED_SUB_OBJECTS = {"MESH", "EMPTY", "ARMATURE"}

DEFAULT_MATERIAL = {
	"diffuse": (bz2xsi.DEFAULT_DIFFUSE, tuple),
	"hardness": (bz2xsi.DEFAULT_HARDNESS, float),
	"specular": (bz2xsi.DEFAULT_SPECULAR, tuple),
	"ambient": (bz2xsi.DEFAULT_AMBIENT, tuple),
	"emissive": (bz2xsi.DEFAULT_EMISSIVE, tuple),
	"shading_type": (bz2xsi.DEFAULT_SHADING_TYPE, int),
	"texture": (None, str)
}

UNIT_SCALE = Vector((1.0, 1.0, 1.0))
SCALE_EPSILON = 1e-4

# Mesh for hardpoint objects
def generate_pointer_mesh(scale=0.05):
	bz2mesh = bz2xsi.Mesh()
	
	bz2mesh.vertices = (
		(-scale, -scale, 0.0),
		(scale, -scale, 0.0),
		(-scale, scale, 0.0),
		(scale, scale, 0.0),
		(0.0, 0.0, 7.0 * scale)
	)
	
	bz2mesh.normal_vertices = bz2mesh.vertices
	bz2mesh.faces = ((0, 2, 3, 1), (3, 2, 4), (0, 1, 4), (1, 3, 4), (2, 0, 4))
	bz2mesh.normal_faces = bz2mesh.faces
	bz2mesh.face_materials = [bz2xsi.Material(diffuse=(1.0, 1.0, 1.0))] * len(bz2mesh.faces)
	
	return bz2mesh

def generate_bone_mesh(bone, posebone):
	radius = bone.length*0.125
	base = bone.length*0.20
	tip = bone.length
	
	bone_group = getattr(posebone, "bone_group", None) # Removed in Blender 4.0
	rgb = tuple(bone_group.colors.active)[0:3] if bone_group else bz2xsi.DEFAULT_DIFFUSE[0:3]
	rgba = rgb + (0.80,)
	
	bz2mesh = bz2xsi.Mesh()
	
	bz2mesh.vertices = (
		(-radius, base, -radius),
		(0.0, 0.0, 0.0),
		(radius, base, -radius),
		(-radius, base, radius),
		(radius, base, radius),
		(0.0, tip, 0.0)
	)
	
	bz2mesh.faces = (
		(2, 4, 1),
		(1, 3, 0),
		(1, 4, 3),
		(2, 1, 0),
		(5, 3, 4),
		(5, 2, 0),
		(5, 0, 3),
		(5, 4, 2)
	)
	
	bz2mesh.face_materials = [bz2xsi.Material(diffuse=rgba)] * len(bz2mesh.faces)
	
	bz2mesh.normal_vertices = (
		(0.8, -0.6, 0),
		(0.8, -0.6, 0),
		(0.8, -0.6, 0),
		(-0.8, -0.6, 0),
		(-0.8, -0.6, 0),
		(-0.8, -0.6, 0),
		(0, -0.6, 0.8),
		(0, -0.6, 0.8),
		(0, -0.6, 0.8),
		(0, -0.6, -0.8),
		(0, -0.6, -0.8),
		(0, -0.6, -0.8),
		(0, 0.184289, 0.982872),
		(0, 0.184289, 0.982872),
		(0, 0.184289, 0.982872),
		(0, 0.184289, -0.982872),
		(0, 0.184289, -0.982872),
		(0, 0.184289, -0.982872),
		(-0.982872, 0.184289, 0),
		(-0.982872, 0.184289, 0),
		(-0.982872, 0.184289, 0),
		(0.982872, 0.184289, 0),
		(0.982872, 0.184289, 0),
		(0.982872, 0.184289, 0)
	)
	
	bz2mesh.normal_faces = (
		(0, 1, 2),
		(3, 4, 5),
		(6, 7, 8),
		(9, 10, 11),
		(12, 13, 14),
		(15, 16, 17),
		(18, 19, 20),
		(21, 22, 23)
	)
	
	return bz2mesh

def action_fcurves(animation_data):
	"""F-Curves animating an ID: its slot of a layered Action (Blender 4.4+), or the legacy list."""
	action = animation_data.action
	layers = getattr(action, "layers", None)
	if layers:
		slot = getattr(animation_data, "action_slot", None)
		for layer in layers:
			for strip in layer.strips:
				for bag in getattr(strip, "channelbags", []):
					if slot is None or bag.slot == slot:
						yield from bag.fcurves
	elif hasattr(action, "fcurves"):
		yield from action.fcurves

# Returns {data path: sorted unique whole keyframes}, one entry per keyed frame across all channels
def get_keyframes_filtered(animation_data, keyframe_filter):
	filtered_frames = {key: set() for key in keyframe_filter}
	key_min, key_max = tuple(animation_data.action.frame_range)
	
	for fcurve in action_fcurves(animation_data):
		if not fcurve.data_path in keyframe_filter:
			continue

		for point in fcurve.keyframe_points:
			pos = round(point.co[0])

			if pos >= key_min and pos <= key_max:
				filtered_frames[fcurve.data_path].add(pos)

	return {key: sorted(frames) for key, frames in filtered_frames.items()}

# Returns dictionary of {Bone Name: [(Vert Index, Vert Weight)...]}
def get_vertex_weights(obj, group_names=None):
	vertex_weights = {}
	name_by_index = {}
	indices_used = []
	
	for vertex_group in obj.vertex_groups:
		if group_names == None or vertex_group.name in group_names:
			name_by_index[vertex_group.index] = vertex_group.name
			vertex_weights[vertex_group.name] = []
			indices_used.append(vertex_group.index)
	
	for vertex in obj.data.vertices:
		for group in vertex.groups:
			if group.group in indices_used:
				name = name_by_index[group.group]
				vertex_weights[name].append((vertex.index, group.weight * 100.0))
	
	return vertex_weights

def get_parents(bpy_obj):
	while bpy_obj.parent:
		bpy_obj = bpy_obj.parent
		yield bpy_obj

def get_armature(bpy_obj):
	armature_mod = None
	for modifier in bpy_obj.modifiers:
		if modifier.type == "ARMATURE":
			if not armature_mod:
				armature_mod = modifier.object
			else:
				print("XSI Warning: Multiple armature modifiers may cause unexpected results.")
				break
	
	return armature_mod

def is_unit_scale(scale):
	return all(abs(axis - unit) <= SCALE_EPSILON for axis, unit in zip(scale, UNIT_SCALE))

def get_active_color_layer(data):
	if hasattr(data, "color_attributes"):
		if "Col" in data.color_attributes:
			return data.color_attributes["Col"].data
		
		if data.color_attributes.active_color:
			return data.color_attributes.active_color.data
	
	if hasattr(data, "vertex_colors"):
		if "Col" in data.vertex_colors:
			return data.vertex_colors["Col"].data
		
		if data.vertex_colors.active:
			return data.vertex_colors.active.data
	
	return None

def obj_hierarchy_to_linear(bpy_objects):
	for bpy_obj in bpy_objects:
		for bpy_subobj in bpy_obj.children:
			if bpy_subobj.type in ALLOWED_SUB_OBJECTS:
				yield bpy_subobj
			
			yield from obj_hierarchy_to_linear([bpy_subobj])

class Save:
	def __init__(self, operator, context, filepath="", **opt):
		self.depsgraph = context.evaluated_depsgraph_get()
		self.bz2xsi_xsi = bz2xsi.XSI()
		self.opt = opt
		
		original_keyframe_position = bpy.context.scene.frame_current
		
		if opt["export_animations"] and original_keyframe_position != bpy.context.scene.frame_start:
			# This is so animated objects keyframe offset does not affect object's unanimated pose or matrix.
			# We'll set it back to original_keyframe_position later when we're done.
			bpy.context.scene.frame_set(bpy.context.scene.frame_start)

		# Rest transforms are read at this frame; animation sampling returns here afterwards.
		self.rest_frame = bpy.context.scene.frame_current
		
		if opt["export_mode"] == "ACTIVE_COLLECTION":
			objects = [obj for obj in bpy.context.view_layer.active_layer_collection.collection.objects if (obj.parent == None and not obj.hide_viewport)]
		
		elif opt["export_mode"] == "SELECTED_OBJECTS":
			selected = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
			# Selected children are exported with their selected parent, not again as roots
			objects = [obj for obj in selected if not any(parent in selected for parent in get_parents(obj))]
		
		if len(objects) >= 2:
			print("XSI Warning: BZ2 does not support more than 1 root-level object:", ", ".join(obj.name for obj in objects))

		self.referenced_objects = objects + list(obj_hierarchy_to_linear(objects))
		self.enveloped_bz2frames = {}
		self.bone_name_to_bz2frame = {}
		
		for obj in objects:
			if obj.type in ALLOWED_SUB_OBJECTS:
				self.bz2xsi_xsi.frames += [self.object_to_bz2frame(obj, is_root_level=True)]
		
		# Envelopes for bones
		if opt["export_envelopes"]:
			for bz2frame, obj in self.enveloped_bz2frames.items():
				vertex_weights = get_vertex_weights(obj.evaluated_get(self.depsgraph), self.bone_name_to_bz2frame)
				
				for bone_name, bz2bone in self.bone_name_to_bz2frame.items():
					if bone_name in vertex_weights:
						bz2frame.envelopes.append(bz2xsi.Envelope(bz2bone, vertex_weights[bone_name]))
					else:
						print("XSI Warning: Vertex group not found for bone:", bone_name)
		
		# Set keyframe position back, if changed during reading animation keyframes
		if bpy.context.scene.frame_current != original_keyframe_position:
			bpy.context.scene.frame_set(original_keyframe_position)
	
	def material_to_bz2material(self, material):
		mat = {}
		
		# Check material's custom attributes, these can be used to explicitly override material settings
		for key in DEFAULT_MATERIAL:
			default, value_type = DEFAULT_MATERIAL[key]
			if key in material: # if 'key' is in custom attributes of 'blender material object'
				mat[key] = value_type(material[key])
				# print("Using custom property %r with %r for material %r." % (key, mat[key], material.name))
			else:
				mat[key] = default
		
		# Use the first texture in the node tree if applicable.
		if material.use_nodes and not mat["texture"]:
			for node in material.node_tree.nodes:
				if node.type == "TEX_IMAGE" and node.image:
					mat["texture"] = ntpath.basename(node.image.filepath) # BZ2 looks textures up by file name
					break # Found an image texture.
		
		return bz2xsi.Material(
			mat["diffuse"],
			mat["hardness"],
			mat["specular"],
			mat["ambient"],
			mat["emissive"],
			mat["shading_type"],
			mat["texture"]
		)
	
	def matrix_to_bz2matrix(self, local_matrix):
		return bz2xsi.Matrix(*list(tuple(row) for row in tuple(local_matrix.transposed())))
	
	def object_to_bz2frame(self, obj, is_root_level=False):
		bz2frame = bz2xsi.Frame(obj.name)
		bz2frame.mesh = None
		is_skinned = self.opt["export_envelopes"] and get_armature(obj) in self.referenced_objects

		if is_root_level and self.opt["zero_root_transforms"]:
			bz2frame.transform = bz2xsi.Matrix()
		else:
			bz2frame.transform = self.matrix_to_bz2matrix(obj.matrix_local)
		
		if is_skinned:
			bz2frame.pose = bz2frame.transform
		
		obj_eval = obj.evaluated_get(self.depsgraph)
		data = obj_eval.data
		
		scale = obj_eval.matrix_local.to_scale()
		if not is_unit_scale(scale):
			print("XSI Warning: Scaling information %r contained in object %r is not supported by BZ2." % (scale, obj.name))
		
		if obj.type == "MESH" and not len(data.vertices) <= 0:
			if not ALLOW_MESH_WITH_NO_FACES and len(data.polygons) <= 0:
				print("XSI Warning: Mesh for object %r has no faces, ignoring mesh data." % obj.name)
			
			else:
				if self.opt["export_mesh"]:
					if is_skinned:
						# Envelope vertices must be in the bind pose, which matches the exported bone rest matrices
						armature = get_armature(obj)
						pose_position = armature.data.pose_position
						armature.data.pose_position = "REST"
						bpy.context.view_layer.update()
						data = obj.evaluated_get(self.depsgraph).data
					
					bz2frame.mesh = self.mesh_to_bz2mesh(data, bz2frame.name if USE_FRAME_NAME_AS_MESH_NAME else None)
					
					if is_skinned:
						armature.data.pose_position = pose_position
						bpy.context.view_layer.update()
						self.enveloped_bz2frames[bz2frame] = obj_eval
		
		elif obj.type == "ARMATURE":
			for bone, posebone in zip(obj_eval.data.bones, obj_eval.pose.bones):
				if not bone.parent:
					bz2frame.frames += [self.bone_to_bz2frame(bone, posebone, obj_eval)]
		
		# All other supported blender types are treated as empty objects by default below.
		elif self.opt["generate_empty_mesh"]:
			bz2frame.mesh = generate_pointer_mesh()
			bz2frame.mesh.name = bz2frame.name
		
		if self.opt["export_animations"] and obj_eval.animation_data and obj_eval.animation_data.action:
			bz2_animations = list(self.animation_to_bz2anim(obj_eval))
			
			if is_root_level and not ALLOW_ROOT_LEVEL_ANIMS:
				bz2_animations = []
			
			if bz2_animations:
				if is_root_level:
					print("XSI Warning: Root-level object %r animation data may not behave as expected in BZ2." % obj.name)
				
				bz2frame.animation_keys += bz2_animations
		
		for obj in obj.children:
			if obj.type in ALLOWED_SUB_OBJECTS:
				bz2frame.frames += [self.object_to_bz2frame(obj)]
		
		return bz2frame
	
	def sample_animation(self, keyed_frames, location_path, matrix_at_frame):
		"""One translation key block (location keys) and one quaternion block (rotation keys, euler or
		quaternion), each key sampled once per keyed frame. Returns to the rest frame afterwards."""
		location_frames = keyed_frames.pop(location_path, [])
		rotation_frames = sorted(set(frame for frames in keyed_frames.values() for frame in frames))

		for bz2_keyframe_type, frames in ((2, location_frames), (0, rotation_frames)):
			if not frames:
				continue

			bz2anim = bz2xsi.AnimationKey(bz2_keyframe_type)

			for pos in frames:
				bpy.context.scene.frame_set(pos)
				matrix = matrix_at_frame()

				if bz2_keyframe_type == 2:
					bz2anim.add_key(pos, tuple(matrix.to_translation()))
				else:
					bz2anim.add_key(pos, tuple(matrix.transposed().to_quaternion()))

			yield bz2anim

		bpy.context.scene.frame_set(self.rest_frame)

	def animation_to_bz2anim(self, obj):
		keyed_frames = get_keyframes_filtered(obj.animation_data, KEYFRAME_PATHS)
		yield from self.sample_animation(keyed_frames, "location", lambda: Matrix(obj.matrix_local))

	def bone_to_bz2frame(self, bone, posebone, armature):
		bz2frame = bz2xsi.Frame(bone.name)
		bz2frame.is_bone = True
		self.bone_name_to_bz2frame[bone.name] = bz2frame
		
		matrix = Matrix()

		if bone.parent:
			matrix @= Matrix(bone.parent.matrix_local).inverted()
		
		matrix @= Matrix(bone.matrix_local)

		bz2frame.transform = self.matrix_to_bz2matrix(matrix)
		bz2frame.pose = bz2frame.transform
		
		for child_bone, child_posebone in zip(bone.children, posebone.children):
			bz2frame.frames += [self.bone_to_bz2frame(child_bone, child_posebone, armature)]
		
		if self.opt["generate_bone_mesh"]:
			bz2frame.mesh = generate_bone_mesh(bone, posebone)
			bz2frame.mesh.name = bone.name
		
		if self.opt["export_animations"]:
			if armature.animation_data and armature.animation_data.action:
				bz2frame.animation_keys += list(self.bone_animation_to_bz2anim(bone, posebone, armature))

		return bz2frame
	
	def bone_animation_to_bz2anim(self, bone, posebone, armature):
		# fcurves will be in the armature object, not in the bone object.
		prefix = "pose.bones[\"%s\"]." % bpy.utils.escape_identifier(bone.name)
		keyed_frames = get_keyframes_filtered(armature.animation_data, [prefix + path for path in KEYFRAME_PATHS])

		def local_matrix():
			if posebone.parent:
				return Matrix(posebone.parent.matrix).inverted() @ Matrix(posebone.matrix)
			return Matrix(posebone.matrix)

		yield from self.sample_animation(keyed_frames, prefix + "location", local_matrix)

	def mesh_to_bz2mesh(self, data, name=None):
		bz2mesh = bz2xsi.Mesh(name if name else data.name)
		if OLD_NORMALS:
			data.calc_normals_split()
		bz2materials = []
		
		if self.opt["export_mesh_materials"]:
			for material in data.materials:
				bz2materials += [self.material_to_bz2material(material) if material else bz2xsi.Material()]
		
		for vertex in data.vertices:
			bz2mesh.vertices += [tuple(vertex.co.xyz)]
		
		for polygon in data.polygons:
			bz2mesh.faces += [tuple(polygon.vertices)]
		
		if bz2materials:
			for polygon in data.polygons:
				bz2mesh.face_materials += [bz2materials[polygon.material_index]]
		
		elif not ALLOW_MESH_WITH_NO_MATERIAL:
			print("XSI Warning: Mesh %r has no materials, adding default material." % name)
			bz2mesh.face_materials = [bz2xsi.Material()] * len(data.polygons)
		
		active_uv_layer = data.uv_layers.active
		uv_layer = active_uv_layer.data if active_uv_layer else None
		color_layer = get_active_color_layer(data)
		
		# Normals and mesh loop faces (loop indices shared for uv and vert colors)
		for polygon in data.polygons:
			for loop_index in polygon.loop_indices:
				bz2mesh.normal_vertices += [tuple(data.loops[loop_index].normal)]
			
			bz2mesh.normal_faces += [tuple(polygon.loop_indices)]
		
		if uv_layer and self.opt["export_mesh_uvmap"]:
			for poly in data.polygons:
				for loop_index in poly.loop_indices:
					bz2mesh.uv_vertices += [tuple(uv_layer[loop_index].uv)]
			
			bz2mesh.uv_faces = bz2mesh.normal_faces
		
		if color_layer and self.opt["export_mesh_vertcolor"]:
			for poly in data.polygons:
				for loop_index in poly.loop_indices:
					bz2mesh.vertex_colors += [tuple(color_layer[loop_index].color)]
			
			bz2mesh.vertex_color_faces = bz2mesh.normal_faces
		
		return bz2mesh

def save(operator, context, filepath="", **opt):
	Save(operator, context, filepath=filepath, **opt).bz2xsi_xsi.write(filepath=filepath)
	return {"FINISHED"}
