# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import uuid
from xml.etree import ElementTree as ET

import bpy

from ..utils.color_utils import blender_to_veml_color
from ..utils.transform_utils import get_transform_elements
from .entity_exporter import EntityExporter
from .mesh_exporter import MeshExporter


class VEMLExporter:
    """Main exporter class for VEML format"""

    VEML_NAMESPACE = "http://www.fivesqd.com/schemas/veml/3.0"
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

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
    ):
        self.context = context
        self.filepath = filepath
        self.export_selected = export_selected
        self.export_mode = export_mode
        self.export_meshes = export_meshes
        self.mesh_format = mesh_format
        self.apply_modifiers = apply_modifiers
        self.world_mesh_name = world_mesh_name

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
        """Main export method. Returns dict with 'success' and 'error' keys."""
        try:
            # Register namespaces - empty prefix for default namespace
            ET.register_namespace('', self.VEML_NAMESPACE)
            ET.register_namespace('xsi', self.XSI_NAMESPACE)

            # Create root element
            root = ET.Element(
                f'{{{self.VEML_NAMESPACE}}}veml',
                {
                    f'{{{self.XSI_NAMESPACE}}}schemaLocation': 
                        f'{self.VEML_NAMESPACE} veml.xsd',
                }
            )

            # Build document
            self._build_metadata(root)
            self._build_environment(root)

            # Write to file
            self._write_xml(root)

            return {'success': True, 'error': None}

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _build_metadata(self, root):
        """Build the metadata section"""
        scene = self.context.scene
        veml_props = scene.veml_scene_properties

        metadata = ET.SubElement(root, 'metadata')

        # Title
        title = ET.SubElement(metadata, 'title')
        title.text = veml_props.title or "Untitled World"

        # Scripts
        if veml_props.scripts:
            scripts = [s.strip() for s in veml_props.scripts.split(',') if s.strip()]
            for script_path in scripts:
                script = ET.SubElement(metadata, 'script')
                script.text = script_path

        # Synchronization Service
        if veml_props.sync_enabled:
            sync_service = ET.SubElement(metadata, 'synchronizationservice')
            if veml_props.sync_type:
                sync_service.set('type', veml_props.sync_type)
            if veml_props.sync_address:
                sync_service.set('address', veml_props.sync_address)
            if veml_props.sync_id:
                sync_service.set('id', veml_props.sync_id)
            if veml_props.sync_session:
                sync_service.set('session', veml_props.sync_session)

    def _build_environment(self, root):
        """Build the environment section"""
        scene = self.context.scene
        veml_props = scene.veml_scene_properties

        environment = ET.SubElement(root, 'environment')

        # Background
        self._build_background(environment, veml_props)

        # Effects
        if veml_props.fog_enabled:
            self._build_effects(environment, veml_props)

        # Entities
        self._build_entities(environment)

    def _build_background(self, environment, veml_props):
        """Build the background element"""
        background = ET.SubElement(environment, 'background')

        if veml_props.background_type == 'COLOR':
            color_elem = ET.SubElement(background, 'color')
            color_elem.text = blender_to_veml_color(veml_props.background_color)

        elif veml_props.background_type == 'PANORAMA':
            panorama_elem = ET.SubElement(background, 'panorama')
            panorama_elem.text = veml_props.background_panorama

        elif veml_props.background_type == 'PROCEDURAL':
            sky = ET.SubElement(background, 'lite-procedural-sky')
            sky.set('day-night-cycle-enabled', str(veml_props.procedural_day_night_cycle).lower())
            sky.set('sun-enabled', str(veml_props.procedural_sun_enabled).lower())
            sky.set('moon-enabled', str(veml_props.procedural_moon_enabled).lower())
            sky.set('stars-enabled', str(veml_props.procedural_stars_enabled).lower())
            sky.set('clouds-enabled', str(veml_props.procedural_clouds_enabled).lower())

    def _build_effects(self, environment, veml_props):
        """Build the effects element"""
        effects = ET.SubElement(environment, 'effects')
        lite_fog = ET.SubElement(effects, 'lite-fog')
        lite_fog.set('fog-enabled', 'true')
        lite_fog.set('color', blender_to_veml_color(veml_props.fog_color))
        lite_fog.set('density', str(veml_props.fog_density))

    def _build_entities(self, environment):
        """Build entity elements from scene objects"""
        print(f"Building entities with export_mode: {self.export_mode}")
        if self.export_mode == 'SINGLE_MESH':
            self._build_single_mesh_entity(environment)
        else:
            self._build_individual_entities(environment)

    def _build_individual_entities(self, environment):
        """Build individual entity elements from scene objects"""
        scene = self.context.scene

        # Get objects to export
        if self.export_selected:
            objects = [obj for obj in self.context.selected_objects if obj.parent is None]
        else:
            objects = [obj for obj in scene.objects if obj.parent is None]

        # Sort by name for consistent output
        objects.sort(key=lambda o: o.name)

        # Export each root object
        for obj in objects:
            entity_elem = self.entity_exporter.export_object(obj)
            if entity_elem is not None:
                environment.append(entity_elem)

    def _build_single_mesh_entity(self, environment):
        """Export entire scene as a single GLB and create one mesh entity"""
        print("Building single mesh entity...")
        
        # Export the entire scene (or selection) as a single GLB
        mesh_path = self._export_world_mesh()
        
        print(f"Mesh path returned: {mesh_path}")
        
        if mesh_path is None:
            print("ERROR: mesh_path is None, no entity will be created!")
            return
        
        print("Creating mesh entity element...")
        # Create a single mesh entity
        entity = ET.SubElement(environment, 'entity')
        entity.set(f'{{{self.XSI_NAMESPACE}}}type', 'vem:mesh')
        entity.set('tag', self.world_mesh_name)
        entity.set('id', str(uuid.uuid4()))
        
        # Transform at origin with no rotation and unit scale
        transform = ET.SubElement(entity, 'transform')
        transform.set(f'{{{self.XSI_NAMESPACE}}}type', 'vem:scaletransform')
        
        position = ET.SubElement(transform, 'position')
        position.set('x', '0')
        position.set('y', '0')
        position.set('z', '0')
        
        rotation = ET.SubElement(transform, 'rotation')
        rotation.set('x', '0')
        rotation.set('y', '0')
        rotation.set('z', '0')
        rotation.set('w', '1')
        
        scale = ET.SubElement(transform, 'scale')
        scale.set('x', '1')
        scale.set('y', '1')
        scale.set('z', '1')
        
        # Mesh name and resource (both use the same path)
        mesh_name = ET.SubElement(entity, 'mesh-name')
        mesh_name.text = mesh_path
        
        mesh_resource = ET.SubElement(entity, 'mesh-resource')
        mesh_resource.text = mesh_path

    def _export_world_mesh(self) -> str:
        """Export the entire scene as a single GLB/GLTF file"""
        print("=== _export_world_mesh called ===")
        
        # Create meshes subdirectory
        meshes_dir = os.path.join(self.export_dir, 'meshes')
        os.makedirs(meshes_dir, exist_ok=True)
        print(f"Meshes directory: {meshes_dir}")
        
        # Determine file extension and path
        ext = '.glb' if self.mesh_format == 'GLB' else '.gltf'
        filename = f"{self.world_mesh_name}{ext}"
        filepath = os.path.join(meshes_dir, filename)
        print(f"Target filepath: {filepath}")
        
        # Store current selection
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.view_layer.objects.active
        
        try:
            # Deselect all first
            bpy.ops.object.select_all(action='DESELECT')
            
            # Object types to export
            exportable_types = ('MESH', 'CURVE', 'SURFACE', 'FONT', 'LIGHT', 'CAMERA', 'EMPTY', 'ARMATURE')
            
            if self.export_selected:
                # Re-select the originally selected objects
                export_objects = []
                for obj in original_selection:
                    if obj.type in exportable_types:
                        # Check if object is in the current view layer
                        if obj.name in self.context.view_layer.objects:
                            obj.select_set(True)
                            export_objects.append(obj)
                        else:
                            print(f"  Skipped (not in view layer): {obj.name}")
            else:
                # Select all exportable objects that are in the view layer
                export_objects = []
                skipped_objects = []
                
                # First, log what's in the scene vs view layer
                scene_objects = set(obj.name for obj in self.context.scene.objects)
                view_layer_objects = set(obj.name for obj in self.context.view_layer.objects)
                
                for obj in self.context.scene.objects:
                    if obj.type in exportable_types:
                        if obj.name in view_layer_objects:
                            # Check if object is visible and selectable
                            if obj.hide_viewport:
                                skipped_objects.append((obj.name, "hidden in viewport"))
                            elif obj.hide_select:
                                skipped_objects.append((obj.name, "not selectable"))
                            else:
                                obj.select_set(True)
                                export_objects.append(obj)
                        else:
                            skipped_objects.append((obj.name, "not in view layer"))
                
                if skipped_objects:
                    print(f"Skipped {len(skipped_objects)} objects:")
                    for name, reason in skipped_objects[:20]:  # Limit output
                        print(f"  - {name}: {reason}")
                    if len(skipped_objects) > 20:
                        print(f"  ... and {len(skipped_objects) - 20} more")
            
            if not export_objects:
                print("No mesh objects found to export")
                return None
            
            # Set active object
            bpy.context.view_layer.objects.active = export_objects[0]
            
            print(f"Exporting {len(export_objects)} objects to {filepath}")
            
            # Export
            if self.mesh_format == 'GLB':
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    export_format='GLB',
                    use_selection=True,
                    export_apply=self.apply_modifiers,
                    export_yup=True,
                    # Materials and textures
                    export_materials='EXPORT',
                    export_image_format='AUTO',
                    export_keep_originals=False,
                    export_original_specular=False,
                    # Mesh data
                    export_texcoords=True,
                    export_normals=True,
                    export_tangents=True,
                    export_attributes=True,
                    export_vertex_color='MATERIAL',
                    # Objects
                    export_cameras=True,
                    export_lights=True,
                    export_extras=True,
                    # Skinning and shape keys
                    export_skins=True,
                    export_morph=True,
                    export_morph_normal=True,
                    export_morph_tangent=True,
                    # Animation
                    export_animations=True,
                    export_morph_animation=True,
                )
            else:
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    export_format='GLTF_SEPARATE',
                    use_selection=True,
                    export_apply=self.apply_modifiers,
                    export_yup=True,
                    # Materials and textures
                    export_materials='EXPORT',
                    export_image_format='AUTO',
                    export_texture_dir='textures',
                    export_keep_originals=False,
                    export_original_specular=False,
                    # Mesh data
                    export_texcoords=True,
                    export_normals=True,
                    export_tangents=True,
                    export_attributes=True,
                    export_vertex_color='MATERIAL',
                    # Objects
                    export_cameras=True,
                    export_lights=True,
                    export_extras=True,
                    # Skinning and shape keys
                    export_skins=True,
                    export_morph=True,
                    export_morph_normal=True,
                    export_morph_tangent=True,
                    # Animation
                    export_animations=True,
                    export_morph_animation=True,
                )
            
            print(f"World mesh exported successfully: meshes/{filename}")
            return f'meshes/{filename}'
            
        except Exception as e:
            import traceback
            print(f"Failed to export world mesh: {e}")
            traceback.print_exc()
            return None
            
        finally:
            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for sel_obj in original_selection:
                if sel_obj.name in bpy.data.objects:
                    sel_obj.select_set(True)
            if original_active and original_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = original_active

    def _write_xml(self, root):
        """Write the XML tree to file with pretty formatting"""
        # Use ElementTree's built-in indentation (Python 3.9+)
        try:
            ET.indent(root, space='  ')
        except AttributeError:
            # Fallback for older Python versions
            self._indent_xml(root)
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='unicode')
        
        # Add xmlns:vem namespace declaration to root element
        # This is needed for xsi:type="vem:typename" references
        xml_string = xml_string.replace(
            f'xmlns="{self.VEML_NAMESPACE}"',
            f'xmlns="{self.VEML_NAMESPACE}" xmlns:vem="{self.VEML_NAMESPACE}"',
            1  # Only replace first occurrence
        )
        
        # Write to file with XML declaration
        with open(self.filepath, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(xml_string.encode('UTF-8'))

    def _indent_xml(self, elem, level=0):
        """Add pretty-print indentation to XML elements (fallback for Python < 3.9)"""
        indent = '\n' + '  ' * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
