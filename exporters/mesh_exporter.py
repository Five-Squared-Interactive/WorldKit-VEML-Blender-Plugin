# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os

import bpy


class MeshExporter:
    """Exports Blender meshes to external files (GLB/GLTF)"""

    def __init__(self, export_dir, mesh_format='GLB', apply_modifiers=True):
        self.export_dir = export_dir
        self.mesh_format = mesh_format
        self.apply_modifiers = apply_modifiers
        self.exported_meshes = {}  # Cache to avoid re-exporting same mesh

    def export_mesh(self, obj) -> str:
        """
        Export a mesh object to GLB/GLTF format.
        Returns the relative path to the exported file.
        """
        if obj.type != 'MESH':
            return None

        mesh = obj.data
        mesh_key = mesh.name

        # Check if already exported
        if mesh_key in self.exported_meshes:
            return self.exported_meshes[mesh_key]

        # Create meshes subdirectory
        meshes_dir = os.path.join(self.export_dir, 'meshes')
        os.makedirs(meshes_dir, exist_ok=True)

        # Determine file extension and path
        ext = '.glb' if self.mesh_format == 'GLB' else '.gltf'
        filename = self._sanitize_filename(mesh.name) + ext
        filepath = os.path.join(meshes_dir, filename)

        # Store current selection
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.view_layer.objects.active

        try:
            # Select only this object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Export
            if self.mesh_format == 'GLB':
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    export_format='GLB',
                    use_selection=True,
                    export_apply=self.apply_modifiers,
                    export_yup=True,  # VEML likely uses Y-up
                )
            else:
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    export_format='GLTF_SEPARATE',
                    use_selection=True,
                    export_apply=self.apply_modifiers,
                    export_yup=True,
                )

            # Store relative path
            relative_path = f'meshes/{filename}'
            self.exported_meshes[mesh_key] = relative_path

            return relative_path

        except Exception as e:
            print(f"Failed to export mesh {mesh.name}: {e}")
            return None

        finally:
            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for sel_obj in original_selection:
                sel_obj.select_set(True)
            bpy.context.view_layer.objects.active = original_active

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a name to be used as a filename"""
        # Replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        result = name
        for char in invalid_chars:
            result = result.replace(char, '_')
        return result
