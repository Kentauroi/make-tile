import os
import bpy
from .. lib.utils.selection import select, activate, deselect_all, select_all
from .. utils.registration import get_prefs
from .. lib.utils.collections import create_collection, add_object_to_collection
from .. enums.enums import units
from .voxeliser import voxelise_mesh


# TODO: Ensure you no longer have to manually switch collections to get exporter to work
class MT_OT_Export_Tile(bpy.types.Operator):
    '''Exports contents of current collection as an .stl.
    Creates a copy of the original tile, applies all modifiers,
    joins everything together, voxelises and trims if necessary, creates
    Merged Objects group and moves copy to new group'''

    bl_idname = "scene.export_tile"
    bl_label = "Export tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()

        obj = context.active_object
        obj_props = obj.mt_object_props

        # set up exporter options
        units = bpy.context.scene.mt_units
        export_path = context.scene.mt_export_path

        if units == 'CM':
            unit_multiplier = 10
        else:
            unit_multiplier = 25.4

        if not os.path.exists(export_path):
            os.mkdir(export_path)

        # create a collection called Exported objects
        exported_obj_collection = create_collection("Exported Objects", bpy.context.scene.collection)

        # check if active object is a MT object, if so we export everything
        # in the collection corresponding to the object's mt_object_props.tile_name

        if obj_props.is_mt_object is True:
            tile_name = obj_props.tile_name
            tile_collection = bpy.data.collections[tile_name]

            # save list of visible objects in tile collection
            obs = []
            for obj in tile_collection.all_objects:
                if obj.type == 'MESH':
                    if obj.hide_viewport is False and obj.hide_get() is False:
                        obs.append(obj)
                        select(obj.name)

            # cannot get this to work with context override whatever
            # I do so using select
            '''
            ctx = bpy.context.copy()
            ctx['active_object'] = obs[0]
            ctx['object'] = obs[0]
            ctx['selected_objects'] = obs
            ctx['selected_editable_objects'] = obs
            bpy.ops.object.convert(ctx, target='MESH', keep_original=True)
            '''

            # Apply all modifiers and create a copy of our meshes
            bpy.ops.object.convert(target='MESH', keep_original=True)
            deselect_all()

            # hide the original objects
            for obj in obs:
                obj.hide_set(True)

            # save a list of the copies
            copies = []
            for obj in tile_collection.all_objects:
                if obj.type == 'MESH':
                    if obj.hide_viewport is False and obj.hide_get() is False:
                        copies.append(obj)

            # join the copies together into one object
            ctx = bpy.context.copy()
            ctx['active_object'] = copies[0]
            ctx['object'] = copies[0]
            ctx['selected_objects'] = copies
            ctx['selected_editable_objects'] = copies

            bpy.ops.object.join(ctx)

            # Rename merged tile
            merged_obj = copies[0]
            merged_obj.name = tile_name + '.merged'
            merged_obj.mt_object_props.tile_name = tile_name

            # update context
            ctx['active_object'] = merged_obj
            ctx['object'] = merged_obj

            # voxelise if necessary
            if context.scene.mt_voxelise_on_export is True:
                merged_obj = voxelise_mesh(merged_obj)

            # add merged object to exported objects collection
            add_object_to_collection(merged_obj, exported_obj_collection.name)

            # remove merged_obj from tile collection
            bpy.ops.collection.objects_remove(ctx, collection=tile_name)

            file_path = os.path.join(context.scene.mt_export_path, tile_name + '.stl')

            # export our merged object
            bpy.ops.export_mesh.stl('INVOKE_DEFAULT', filepath=file_path, check_existing=True, filter_glob="*.stl", use_selection=True, global_scale=unit_multiplier, use_mesh_modifiers=True)

        else:
            obj = context.active_object
            obj_copy = obj.copy()
            obj_copy.data = obj_copy.data.copy()

            if context.scene.mt_voxelise_on_export is True:
                obj = voxelise_mesh(obj)

            file_path = os.path.join(context.scene.mt_export_path, context.active_object.name + '.stl')
            bpy.ops.export_mesh.stl('INVOKE_DEFAULT', filepath=file_path, check_existing=True, filter_glob="*.stl", use_selection=True, global_scale=unit_multiplier, use_mesh_modifiers=True)

            ctx = {
                'active_object': obj_copy,
                'object': obj_copy}

            # remove copy from original collection
            # and add it to exported objects collection
            bpy.ops.collection.objects_remove(ctx)
            add_object_to_collection(obj_copy, exported_obj_collection.name)

        return {'FINISHED'}

    @classmethod
    def register(cls):

        preferences = get_prefs()

        bpy.types.Scene.mt_export_path = bpy.props.StringProperty(
            name="Export Path",
            description="Path to export tiles to",
            subtype="DIR_PATH",
            default=preferences.default_export_path,
        )

        bpy.types.Scene.mt_units = bpy.props.EnumProperty(
            name="Units",
            items=units,
            description="Export units",
            default=preferences.default_units
        )

        bpy.types.Scene.mt_voxelise_on_export = bpy.props.BoolProperty(
            name="Voxelise",
            default=False
        )

        bpy.types.Scene.mt_trim_on_export = bpy.props.BoolProperty(
            name="Trim",
            description="Uses the Trim Tile settings",
            default=False
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_trim_on_export
        del bpy.types.Scene.mt_voxelise_on_export
        del bpy.types.Scene.mt_units
        del bpy.types.Scene.mt_export_path
