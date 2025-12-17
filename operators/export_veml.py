# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..exporters.veml_exporter import VEMLExporter


class EXPORT_OT_veml(bpy.types.Operator, ExportHelper):
    """Export scene to VEML format"""
    bl_idname = "export_scene.veml"
    bl_label = "Export VEML"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".veml"

    filter_glob: StringProperty(
        default="*.veml",
        options={'HIDDEN'},
        maxlen=255,
    )

    export_selected: BoolProperty(
        name="Selected Only",
        description="Export only selected objects",
        default=False,
    )

    export_mode: EnumProperty(
        name="Export Mode",
        description="How to export the scene geometry",
        items=[
            ('ENTITIES', "Individual Entities", "Export each object as a separate VEML entity"),
            ('SINGLE_MESH', "Single World Mesh", "Export entire scene as one GLB and reference in VEML"),
        ],
        default='ENTITIES',
    )

    export_meshes: BoolProperty(
        name="Export Custom Meshes",
        description="Export custom meshes as separate GLB files",
        default=True,
    )

    mesh_format: EnumProperty(
        name="Mesh Format",
        description="Format for exported meshes",
        items=[
            ('GLB', "GLB", "Binary glTF format"),
            ('GLTF', "GLTF", "Separate glTF format"),
        ],
        default='GLB',
    )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before exporting meshes",
        default=True,
    )

    world_mesh_name: StringProperty(
        name="World Mesh Name",
        description="Name for the world mesh entity (used in Single World Mesh mode)",
        default="WorldMesh",
    )

    def execute(self, context):
        exporter = VEMLExporter(
            context=context,
            filepath=self.filepath,
            export_selected=self.export_selected,
            export_mode=self.export_mode,
            export_meshes=self.export_meshes,
            mesh_format=self.mesh_format,
            apply_modifiers=self.apply_modifiers,
            world_mesh_name=self.world_mesh_name,
        )

        result = exporter.export()

        if result['success']:
            self.report({'INFO'}, f"VEML exported successfully: {self.filepath}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Export failed: {result['error']}")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # General options
        layout.prop(self, "export_selected")
        layout.prop(self, "export_mode")

        # Mesh options
        box = layout.box()
        box.label(text="Mesh Options", icon='MESH_DATA')
        
        if self.export_mode == 'SINGLE_MESH':
            box.prop(self, "world_mesh_name")
            box.prop(self, "mesh_format")
            box.prop(self, "apply_modifiers")
        else:
            box.prop(self, "export_meshes")
            if self.export_meshes:
                box.prop(self, "mesh_format")
                box.prop(self, "apply_modifiers")
