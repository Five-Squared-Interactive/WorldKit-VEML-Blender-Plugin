# Copyright (c) 2019-2026 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# VEML 4.0 exporter (#21): this module COLLECTS scene data with bpy and
# delegates every byte of XML to the bpy-free `veml40_writer` (which the
# monorepo test suite drives directly). Grammar target:
# specs/veml/veml-4.0.xsd — the package carries a verified copy under
# schema/ (tools/verify-schema.mjs gates drift in CI).

import os
import uuid

import bpy

from ..utils.color_utils import blender_to_veml_color
from .entity_exporter import EntityExporter
from .mesh_exporter import MeshExporter
from .veml40_writer import build_world_document


class VEMLExporter:
    """Main exporter: Blender scene -> VEML 4.0 document."""

    def __init__(
        self,
        context,
        filepath,
        export_selected=False,
        export_mode='ENTITIES',
        export_meshes=True,
        mesh_format='GLB',
        apply_modifiers=True,
        world_mesh_name='WorldMesh',
        include_namespace=True,
    ):
        self.context = context
        self.filepath = filepath
        self.export_selected = export_selected
        self.export_mode = export_mode
        self.export_meshes = export_meshes
        self.mesh_format = mesh_format
        self.apply_modifiers = apply_modifiers
        self.world_mesh_name = world_mesh_name
        # §1.4: the root always carries version="4.0"; the namespace
        # declaration is optional — a namespace-less root WITH version is a
        # VEML 4.0 document, and authoring tools SHOULD emit the declaration
        # (so True is the default).
        self.include_namespace = include_namespace

        self.export_dir = os.path.dirname(filepath)
        self.mesh_exporter = MeshExporter(
            export_dir=self.export_dir,
            mesh_format=mesh_format,
            apply_modifiers=apply_modifiers,
        )
        self.entity_exporter = EntityExporter(
            mesh_exporter=self.mesh_exporter,
            export_meshes=export_meshes,
        )

    def export(self) -> dict:
        """Main export method. Returns dict with 'success', 'error', and
        'skipped' (objects the 4.0 core surface has no home for)."""
        try:
            world = {
                'title': self._collect_title(),
                'sync': self._collect_sync(),
                'background': self._collect_background(),
                'entry_point': None,  # the shell derives arrival (§5)
                'entities': self._collect_entities(),
            }
            document = build_world_document(world, include_namespace=self.include_namespace)
            with open(self.filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(document)

            for name, reason in self.entity_exporter.skipped:
                print(f"VEML export: skipped {name} — {reason}")
            return {'success': True, 'error': None, 'skipped': list(self.entity_exporter.skipped)}

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'skipped': []}

    # -- collection ----------------------------------------------------------

    def _props(self):
        return self.context.scene.veml_scene_properties

    def _collect_title(self):
        return self._props().title or "Untitled World"

    def _collect_sync(self):
        veml_props = self._props()
        if not veml_props.sync_enabled:
            return None
        # 4.0 §7: all four attributes are required on the declaration.
        return {
            'type': veml_props.sync_type or 'unknown',
            'address': veml_props.sync_address or '',
            'id': veml_props.sync_id or str(uuid.uuid4()),
            'session': veml_props.sync_session or 'default',
        }

    def _collect_background(self):
        veml_props = self._props()
        if veml_props.background_type == 'COLOR':
            return {'color': blender_to_veml_color(veml_props.background_color)}
        if veml_props.background_type == 'PANORAMA':
            return {'panorama': veml_props.background_panorama}
        if veml_props.background_type == 'PROCEDURAL':
            # The procedural sky is a PROFILE surface in 4.0 (§10), not core
            # grammar — export the core document without it, loudly.
            print("VEML export: procedural sky skipped — a 4.0 profile surface, not core grammar (§10)")
        return None

    def _collect_entities(self):
        if self.export_mode == 'SINGLE_MESH':
            return self._collect_single_mesh_entity()
        return self._collect_individual_entities()

    def _collect_individual_entities(self):
        scene = self.context.scene
        if self.export_selected:
            objects = [obj for obj in self.context.selected_objects if obj.parent is None]
        else:
            objects = [obj for obj in scene.objects if obj.parent is None]
        objects.sort(key=lambda o: o.name)

        entities = []
        for obj in objects:
            entity = self.entity_exporter.collect_object(obj)
            if entity is not None:
                entities.append(entity)
        return entities

    def _collect_single_mesh_entity(self):
        mesh_path = self._export_world_mesh()
        if mesh_path is None:
            print("VEML export: world mesh export produced no file — no entity emitted")
            return []
        return [{
            'kind': 'asset',
            'tag': self.world_mesh_name,
            'id': str(uuid.uuid4()),
            'src': mesh_path,
            'transform': {
                'position': (0, 0, 0),
                'rotation': (0, 0, 0, 1),
                'scale': (1, 1, 1),
            },
            'sockets': [],
            'children': [],
        }]

    def _export_world_mesh(self):
        """Export the entire scene as a single GLB/GLTF file."""
        meshes_dir = os.path.join(self.export_dir, 'meshes')
        os.makedirs(meshes_dir, exist_ok=True)

        ext = '.glb' if self.mesh_format == 'GLB' else '.gltf'
        filename = f"{self.world_mesh_name}{ext}"
        filepath = os.path.join(meshes_dir, filename)

        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.view_layer.objects.active

        try:
            bpy.ops.object.select_all(action='DESELECT')
            exportable_types = ('MESH', 'CURVE', 'SURFACE', 'FONT', 'LIGHT', 'CAMERA', 'EMPTY', 'ARMATURE')

            export_objects = []
            candidates = original_selection if self.export_selected else self.context.scene.objects
            view_layer_objects = set(obj.name for obj in self.context.view_layer.objects)
            for obj in candidates:
                if obj.type not in exportable_types:
                    continue
                if obj.name not in view_layer_objects:
                    continue
                if not self.export_selected and (obj.hide_viewport or obj.hide_select):
                    continue
                obj.select_set(True)
                export_objects.append(obj)

            if not export_objects:
                return None

            bpy.context.view_layer.objects.active = export_objects[0]

            export_format = 'GLB' if self.mesh_format == 'GLB' else 'GLTF_SEPARATE'
            kwargs = dict(
                filepath=filepath,
                export_format=export_format,
                use_selection=True,
                export_apply=self.apply_modifiers,
                export_yup=True,
                export_materials='EXPORT',
                export_image_format='AUTO',
                export_keep_originals=False,
                export_original_specular=False,
                export_texcoords=True,
                export_normals=True,
                export_tangents=True,
                export_attributes=True,
                export_vertex_color='MATERIAL',
                export_cameras=True,
                export_lights=True,
                export_extras=True,
                export_skins=True,
                export_morph=True,
                export_morph_normal=True,
                export_morph_tangent=True,
                export_animations=True,
                export_morph_animation=True,
            )
            if export_format == 'GLTF_SEPARATE':
                kwargs['export_texture_dir'] = 'textures'
            bpy.ops.export_scene.gltf(**kwargs)

            return f'meshes/{filename}'

        except Exception as e:
            import traceback
            print(f"Failed to export world mesh: {e}")
            traceback.print_exc()
            return None

        finally:
            bpy.ops.object.select_all(action='DESELECT')
            for sel_obj in original_selection:
                if sel_obj.name in bpy.data.objects:
                    sel_obj.select_set(True)
            if original_active and original_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = original_active
