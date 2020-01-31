"""Contains operator class to make tiles"""
import os
import bpy
import bpy.utils.previews
from mathutils import Vector
from .. lib.utils.selection import deselect_all
from .. utils.registration import get_path, get_prefs
from .. lib.utils.collections import (
    create_collection,
    activate_collection)

from .. enums.enums import (
    tile_main_systems,
    tile_types,
    units,
    base_systems,
    tile_blueprints,
    base_socket_side,
    curve_types,
    material_mapping)

from .. materials.materials import (
    load_materials,
    get_blend_filenames,
    update_displacement_material_2,
    update_preview_material_2,
    assign_mat_to_vert_group,
    assign_texture_to_areas)

from .. tile_creation.create_straight_wall_tile import create_straight_wall
from .. tile_creation.create_rect_floor_tile import create_rectangular_floor
from .. tile_creation.create_curved_wall_tile import create_curved_wall
from .. tile_creation.create_corner_wall import create_corner_wall
from .. tile_creation.create_triangular_floor import create_triangular_floor
from .. tile_creation.create_curved_floor import create_curved_floor

from .. property_groups.property_groups import MT_Tile_Properties, MT_Object_Properties


class MT_OT_Make_Tile(bpy.types.Operator):
    """Create a Tile"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):

        ############################################
        # Set defaults for different tile systems #
        ############################################
        tile_blueprint = context.scene.mt_tile_blueprint
        tile_type = context.scene.mt_tile_type

        if tile_blueprint == 'OPENLOCK':
            context.scene.mt_main_part_blueprint = 'OPENLOCK'
            context.scene.mt_base_blueprint = 'OPENLOCK'

        if tile_blueprint == 'PLAIN':
            context.scene.mt_main_part_blueprint = 'PLAIN'
            context.scene.mt_base_blueprint = 'PLAIN'

        #######################################
        # Create our collection and tile name #
        # 'Tiles' are collections of meshes   #
        # parented to an empty                #
        #######################################

        scene_collection = bpy.context.scene.collection

        # Check to see if tile collection exist and create if not
        tiles_collection = create_collection('Tiles', scene_collection)

        # construct first part of tile name based on system and type
        tile_name = tile_blueprint.lower() + "." + tile_type.lower()
        # deselect_all()

        if tile_type == 'STRAIGHT_WALL' or tile_type == 'CURVED_WALL' or tile_type == 'CORNER_WALL':
            # create walls collection if it doesn't already exist
            walls_collection = create_collection('Walls', tiles_collection)

            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Walls'].children.link(tile_collection)

        elif tile_type == 'RECTANGULAR_FLOOR' or tile_type == 'TRIANGULAR_FLOOR' or tile_type == 'CURVED_FLOOR':
            # create floor collection if one doesn't already exist
            floors_collection = create_collection('Floors', tiles_collection)
            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Floors'].children.link(tile_collection)

        # make final tile name
        tile_name = tile_collection.name

        # We store tile properties in the mt_tile_props property group of
        # the collection so we can access them from any object in this
        # collection.

        activate_collection(tile_collection.name)
        props = context.collection.mt_tile_props
        props.tile_name = tile_name
        props.is_mt_collection = True
        props.tile_blueprint = tile_blueprint
        props.tile_type = tile_type
        props.main_part_blueprint = context.scene.mt_main_part_blueprint
        props.base_blueprint = context.scene.mt_base_blueprint

        ###############
        # Create Tile #
        ###############

        if tile_type == 'STRAIGHT_WALL':
            create_straight_wall()

        if tile_type == 'CURVED_WALL':
            create_curved_wall()

        if tile_type == 'CORNER_WALL':
            create_corner_wall()

        if tile_type == 'RECTANGULAR_FLOOR':
            create_rectangular_floor()

        if tile_type == 'TRIANGULAR_FLOOR':
            create_triangular_floor()

        if tile_type == 'CURVED_FLOOR':
            create_curved_floor()

        return {'FINISHED'}

    @classmethod
    def register(cls):

        preferences = get_prefs()
        material_enum_collection = bpy.utils.previews.new()
        material_enum_collection.directory = ''
        material_enum_collection.enums = ()
        enum_collections["materials"] = material_enum_collection

        # Property group that contains properties relating to a tile on the tile collection
        bpy.types.Collection.mt_tile_props = bpy.props.PointerProperty(
            type=MT_Tile_Properties
        )

        # Property group that contains properties of an object stored on the object
        bpy.types.Object.mt_object_props = bpy.props.PointerProperty(
            type=MT_Object_Properties
        )

        bpy.types.Scene.mt_tile_name = bpy.props.StringProperty(
            name="Tile Name",
            default="Tile"
        )

        bpy.types.Scene.mt_tile_units = bpy.props.EnumProperty(
            items=units,
            name="Units",
            default=preferences.default_units,
        )

        bpy.types.Scene.mt_tile_blueprint = bpy.props.EnumProperty(
            items=tile_blueprints,
            name="Blueprint",
            default=preferences.default_tile_blueprint,
        )

        bpy.types.Scene.mt_main_part_blueprint = bpy.props.EnumProperty(
            items=tile_main_systems,
            name="Main System",
            default=preferences.default_tile_main_system,
        )
        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Type",
            default="STRAIGHT_WALL",
        )

        bpy.types.Scene.mt_base_blueprint = bpy.props.EnumProperty(
            items=base_systems,
            name="Base Type",
            default=preferences.default_base_system,
        )

        bpy.types.Scene.mt_tile_material_1 = bpy.props.EnumProperty(
            items=load_material_enums,
            name="Material 1",
            update=update_material_enums
        )

        bpy.types.Scene.mt_material_mapping_method = bpy.props.EnumProperty(
            items=material_mapping,
            description="How to map the active material onto an object",
            name="Material Mapping Method",
            update=update_material_mapping,
            default='OBJECT'
        )

        bpy.types.Scene.mt_displacement_strength = bpy.props.FloatProperty(
            name="Displacement Strength",
            description="Overall Displacement Strength",
            default=0.1,
            min=0.0,
            max=1,
            step=1,
            precision=3,
            update=update_disp_strength
        )

        bpy.types.Scene.mt_tile_resolution = bpy.props.IntProperty(
            name="Resolution",
            description="Bake resolution of displacement maps. Higher = better quality but slower. Also images are 32 bit so 4K and 8K images can be gigabytes in size",
            default=1024,
            min=1024,
            max=8192,
            step=1024,
        )

        bpy.types.Scene.mt_subdivisions = bpy.props.IntProperty(
            name="Subdivisions",
            description="How many times to subdivide the displacement mesh. Higher = better but slower. \
            Going above 8 is really not recommended and may cause Blender to freeze up for a loooooong time!",
            default=6,
            soft_max=8,
            update=update_disp_subdivisions
        )

        # Tile and base size. We use seperate floats so that we can only show
        # customisable ones where appropriate. These are wrapped up
        # in a vector and passed on as tile_size and base_size

        # Tile size
        bpy.types.Scene.mt_tile_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_y = bpy.props.FloatProperty(
            name="Y",
            default=2,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_z = bpy.props.FloatProperty(
            name="Z",
            default=2.0,
            step=0.1,
            precision=3,
            min=0
        )

        # Base size
        bpy.types.Scene.mt_base_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_base_y = bpy.props.FloatProperty(
            name="Y",
            default=0.5,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_base_z = bpy.props.FloatProperty(
            name="Z",
            default=0.3,
            step=0.1,
            precision=3,
            min=0
        )

        # Corner wall and triangular base specific
        bpy.types.Scene.mt_angle = bpy.props.FloatProperty(
            name="Base Angle",
            default=90,
            step=5,
            precision=1
        )

        bpy.types.Scene.mt_leg_1_len = bpy.props.FloatProperty(
            name="Leg 1 Length",
            description="Length of leg",
            default=2,
            step=0.5,
            precision=2
        )

        bpy.types.Scene.mt_leg_2_len = bpy.props.FloatProperty(
            name="Leg 2 Length",
            description="Length of leg",
            default=2,
            step=0.5,
            precision=2
        )

        # Openlock curved wall specific
        bpy.types.Scene.mt_base_socket_side = bpy.props.EnumProperty(
            items=base_socket_side,
            name="Socket Side",
            default="INNER",
        )

        # Used for curved wall tiles
        bpy.types.Scene.mt_base_radius = bpy.props.FloatProperty(
            name="Base inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0,
        )

        bpy.types.Scene.mt_wall_radius = bpy.props.FloatProperty(
            name="Wall inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        # used for curved floors
        bpy.types.Scene.mt_curve_type = bpy.props.EnumProperty(
            items=curve_types,
            name="Curve type",
            default="POS",
            description="Whether the tile has a positive or negative curvature"
        )

        # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
        bpy.types.Scene.mt_degrees_of_arc = bpy.props.FloatProperty(
            name="Degrees of arc",
            default=90,
            step=45,
            precision=1,
            max=359.999,
            min=-359.999
        )

        bpy.types.Scene.mt_segments = bpy.props.IntProperty(
            name="Number of segments",
            default=8,
        )

        bpy.types.Scene.mt_trim_buffer = bpy.props.FloatProperty(
            name="Buffer",
            description="Buffer to use for creating tile trimmers. Helps Booleans work",
            default=-0.001,
            precision=4
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_trim_buffer
        del bpy.types.Scene.mt_tile_name
        del bpy.types.Scene.mt_segments
        del bpy.types.Scene.mt_base_radius
        del bpy.types.Scene.mt_wall_radius
        del bpy.types.Scene.mt_curve_type
        del bpy.types.Scene.mt_degrees_of_arc
        del bpy.types.Scene.mt_base_socket_side
        del bpy.types.Scene.mt_base_x
        del bpy.types.Scene.mt_base_y
        del bpy.types.Scene.mt_base_z
        del bpy.types.Scene.mt_tile_x
        del bpy.types.Scene.mt_tile_y
        del bpy.types.Scene.mt_tile_z
        del bpy.types.Scene.mt_base_blueprint
        del bpy.types.Scene.mt_tile_resolution
        del bpy.types.Scene.mt_displacement_strength
        del bpy.types.Scene.mt_tile_material_1
        del bpy.types.Scene.mt_material_mapping_method
        del bpy.types.Scene.mt_subdivisions
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_blueprint
        del bpy.types.Scene.mt_main_part_blueprint
        del bpy.types.Scene.mt_tile_units
        del bpy.types.Collection.mt_tile_props
        del bpy.types.Object.mt_object_props

        for pcoll in enum_collections.values():
            bpy.utils.previews.remove(pcoll)
        enum_collections.clear()


def load_material_enums(self, context):
    '''Constructs a material Enum from materials found in the materials asset folder'''
    enum_items = []
    prefs = get_prefs()
    if context is None:
        return enum_items

    materials_path = os.path.join(prefs.assets_path, "materials")
    blend_filenames = get_blend_filenames(materials_path)
    enum_collection = enum_collections['materials']
    if materials_path == enum_collection.directory:
        return enum_collection.enums

    load_materials(materials_path, blend_filenames)
    materials = bpy.data.materials
    for material in materials:
        # prevent make-tile adding the default material to the list
        if material.name != prefs.secondary_material and material.name != 'Material':
            enum = (material.name, material.name, "")
            enum_items.append(enum)

    return enum_items


def update_material_enums(self, context):
    enum_items = []
    materials = bpy.data.materials
    prefs = get_prefs()

    for material in materials:
        # prevent make-tile adding the default material to the list
        if material.name != prefs.secondary_material and material.name != 'Material':
            enum = (material.name, material.name, "")
            enum_items.append(enum)

    return enum_items


def update_disp_strength(self, context):
    disp_obj = bpy.context.object

    if 'Displacement' in disp_obj.modifiers:
        mod = disp_obj.modifiers['Displacement']
        mod.strength = context.scene.mt_displacement_strength


def update_disp_subdivisions(self, context):
    '''Updates the numnber of subdivisions used by the displacement material modifier'''
    disp_obj = bpy.context.object

    if 'Subsurf' in disp_obj.modifiers:
        modifier = disp_obj.modifiers['Subsurf']
        modifier.levels = context.scene.mt_subdivisions


def update_material_mapping(self, context):
    '''updates which mapping method to use for a material'''
    material = context.object.active_material
    tree = material.node_tree
    nodes = tree.nodes

    map_meth = context.scene.mt_material_mapping_method

    if 'master_mapping' in nodes:
        mapping_node = nodes['master_mapping']
        if map_meth == 'WRAP_AROUND':
            map_type_node = nodes['wrap_around_map']
            tree.links.new(
                map_type_node.outputs['Vector'],
                mapping_node.inputs['Vector'])
        elif map_meth == 'TRIPLANAR':
            map_type_node = nodes['triplanar_map']
            tree.links.new(
                map_type_node.outputs['Vector'],
                mapping_node.inputs['Vector'])
        elif map_meth == 'OBJECT':
            map_type_node = nodes['object_map']
            tree.links.new(
                map_type_node.outputs['Color'],
                mapping_node.inputs['Vector'])
        elif map_meth == 'GENERATED':
            map_type_node = nodes['generated_map']
            tree.links.new(
                map_type_node.outputs['Color'],
                mapping_node.inputs['Vector'])
        elif map_meth == 'UV':
            map_type_node = nodes['UV_map']
            tree.links.new(
                map_type_node.outputs['Color'],
                mapping_node.inputs['Vector'])


enum_collections = {}
