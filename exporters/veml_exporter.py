# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import uuid
from xml.dom import minidom
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
        export_meshes=True,
        mesh_format='GLB',
        apply_modifiers=True,
    ):
        self.context = context
        self.filepath = filepath
        self.export_selected = export_selected
        self.export_meshes = export_meshes
        self.mesh_format = mesh_format
        self.apply_modifiers = apply_modifiers

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
            # Register namespaces
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

    def _write_xml(self, root):
        """Write the XML tree to file with pretty formatting"""
        # Convert to string
        rough_string = ET.tostring(root, encoding='unicode')

        # Parse and pretty print
        dom = minidom.parseString(rough_string)
        pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8')

        # Remove extra blank lines that minidom adds
        lines = pretty_xml.decode('UTF-8').split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        clean_xml = '\n'.join(non_empty_lines)

        # Write to file
        with open(self.filepath, 'w', encoding='UTF-8') as f:
            f.write(clean_xml)
