import os
import bpy

from .. utils.registration import get_path
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_all, select, activate


def load_materials(directory_path, blend_filenames):
    all_materials = []
    for filename in blend_filenames:
        file_path = os.path.join(directory_path, filename)
        materials = get_materials_from_file(file_path)
        for material in materials:
            all_materials.append(material)
    return all_materials


def get_blend_filenames(directory_path):
    blend_filenames = [name for name in os.listdir(directory_path)
                       if name.endswith('.blend')]
    return blend_filenames


def get_materials_from_file(file_path):
    with bpy.data.libraries.load(file_path) as (data_from, data_to):
        data_to.materials = data_from.materials
    return data_to.materials


def load_material(material_name):
    '''loads a named material into the scene from external blend file'''
    if material_name not in bpy.data.materials:
        material_file = material_name + ".blend"
        materials_path = os.path.join(get_path(), "assets", "materials", material_file)
        with bpy.data.libraries.load(materials_path) as (data_from, data_to):
            data_to.materials = [material_name]
        material = data_to.materials[0]
        return material
    else:
        return bpy.data.materials[material_name]


def load_secondary_material():
    '''Adds a blank material to the passed in object'''
    if "Blank_Material" not in bpy.data.materials:
        blank_material = bpy.data.materials.new("Blank_Material")
    else:
        blank_material = bpy.data.materials['Blank_Material']
    return blank_material


def assign_mat_to_vert_group(vert_group, obj, material):
    select(obj.name)
    activate(obj.name)
    mode('EDIT')
    deselect_all()
    bpy.ops.object.vertex_group_set_active(group=vert_group)
    bpy.ops.object.vertex_group_select()
    material_index = list(obj.material_slots.keys()).index(material.name)
    obj.active_material_index = material_index
    bpy.ops.object.material_slot_assign()
    mode('OBJECT')


def add_displacement_mesh_modifiers(obj, disp_axis, vert_group, disp_dir, image_size):
    obj_subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    obj_subsurf.subdivision_type = 'SIMPLE'
    obj_subsurf.levels = 0

    obj_disp_mod = obj.modifiers.new('Displacement', 'DISPLACE')
    obj_disp_mod.strength = 0
    obj_disp_mod.texture_coords = 'UV'
    obj_disp_mod.direction = disp_axis
    obj_disp_mod.vertex_group = vert_group
    obj_disp_mod.mid_level = 0

    obj_disp_texture = bpy.data.textures.new(obj.name + '.texture', 'IMAGE')
    obj['disp_texture'] = obj_disp_texture
    obj['disp_dir'] = disp_dir
    obj['subsurf_mod_name'] = obj_subsurf.name
    obj['disp_mod_name'] = obj_disp_mod.name


def assign_displacement_materials(obj, disp_axis, vert_group, disp_dir, image_size, primary_material):
    obj['primary_material'] = primary_material
    add_displacement_mesh_modifiers(obj, disp_axis, vert_group, disp_dir, image_size)
    obj.data.materials.append(primary_material)


def assign_preview_materials(obj, vert_group, primary_material, secondary_material):
    obj['primary_material'] = primary_material
    obj['secondary_material'] = secondary_material
    obj.data.materials.append(secondary_material)
    obj.data.materials.append(primary_material)
    assign_mat_to_vert_group(vert_group, obj, primary_material)