# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ImportHelper

from ..importers.veml_importer import VEMLImporter


class IMPORT_OT_veml(bpy.types.Operator, ImportHelper):
    """Import a VEML file into Blender"""
    bl_idname = "import_scene.veml"
    bl_label = "Import VEML"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".veml"

    filter_glob: StringProperty(
        default="*.veml",
        options={'HIDDEN'},
        maxlen=255,
    )

    import_meshes: BoolProperty(
        name="Import Custom Meshes",
        description="Import GLB/GLTF mesh files referenced by mesh entities",
        default=True,
    )

    set_properties: BoolProperty(
        name="Set VEML Properties",
        description="Set VEML-specific properties on imported objects",
        default=True,
    )

    def execute(self, context):
        importer = VEMLImporter(
            context=context,
            filepath=self.filepath,
            import_meshes=self.import_meshes,
            set_properties=self.set_properties,
        )

        result = importer.import_veml()

        if result['success']:
            obj_count = len(result['objects'])
            self.report({'INFO'}, f"VEML imported successfully: {obj_count} root objects created")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Import failed: {result['error']}")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Import options
        layout.prop(self, "import_meshes")
        layout.prop(self, "set_properties")
