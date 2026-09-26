# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
from xml.etree import ElementTree as ET

import bpy

from .entity_importer import EntityImporter
from .mesh_importer import MeshImporter


class VEMLImporter:
    """Main importer class for VEML format"""

    # 4.0 (#21). Parsing itself is namespace-agnostic (_strip_namespace), so
    # a namespace-less root carrying version="4.0" imports identically —
    # draft §1.4's discriminator.
    VEML_NAMESPACE = "http://www.fivesqd.com/schemas/veml/4.0"
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(
        self,
        context,
        filepath,
        import_meshes=True,
        set_properties=True,
    ):
        self.context = context
        self.filepath = filepath
        self.import_meshes = import_meshes
        self.set_properties = set_properties

        self.import_dir = os.path.dirname(filepath)
        self.mesh_importer = MeshImporter(import_dir=self.import_dir)
        self.entity_importer = EntityImporter(
            mesh_importer=self.mesh_importer,
            import_meshes=import_meshes,
            set_properties=set_properties,
        )

        # Namespace map for parsing
        self.namespaces = {
            'vem': self.VEML_NAMESPACE,
            'xsi': self.XSI_NAMESPACE,
        }

    def import_veml(self) -> dict:
        """Main import method. Returns dict with 'success', 'error', and 'objects' keys."""
        try:
            # Parse the XML file
            tree = ET.parse(self.filepath)
            root = tree.getroot()

            # Strip namespace from root if present
            root_tag = root.tag
            if root_tag.startswith('{'):
                root_tag = root_tag.split('}')[1]

            if root_tag != 'veml':
                return {'success': False, 'error': 'Not a valid VEML file', 'objects': []}

            created_objects = []

            # Import metadata
            self._import_metadata(root)

            # Import environment
            environment = self._find_element(root, 'environment')
            if environment is not None:
                # Import background settings
                self._import_background(environment)

                # Import effects
                self._import_effects(environment)

                # Import entities — the 4.0 entity FAMILY (§4.1), not just
                # the base element name.
                entity_family = ('entity', 'container', 'asset', 'primitive', 'html', 'lod')
                for entity in environment:
                    tag = self._strip_namespace(entity.tag)
                    if tag in entity_family:
                        obj = self.entity_importer.import_entity(entity, parent=None)
                        if obj:
                            created_objects.append(obj)

            return {'success': True, 'error': None, 'objects': created_objects}

        except ET.ParseError as e:
            return {'success': False, 'error': f'XML parse error: {e}', 'objects': []}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'objects': []}

    def _find_element(self, parent, tag):
        """Find element with or without namespace"""
        # Try with namespace
        elem = parent.find(f'{{{self.VEML_NAMESPACE}}}{tag}')
        if elem is not None:
            return elem
        # Try without namespace
        elem = parent.find(tag)
        if elem is not None:
            return elem
        # Try iterating children
        for child in parent:
            if self._strip_namespace(child.tag) == tag:
                return child
        return None

    def _strip_namespace(self, tag):
        """Remove namespace from tag"""
        if tag.startswith('{'):
            return tag.split('}')[1]
        return tag

    def _import_metadata(self, root):
        """Import metadata section into scene properties"""
        metadata = self._find_element(root, 'metadata')
        if metadata is None:
            return

        scene = self.context.scene
        veml_props = scene.veml_scene_properties

        # Title
        title_elem = self._find_element(metadata, 'title')
        if title_elem is not None and title_elem.text:
            veml_props.title = title_elem.text

        # Scripts
        scripts = []
        for child in metadata:
            if self._strip_namespace(child.tag) == 'script' and child.text:
                scripts.append(child.text)
        if scripts:
            veml_props.scripts = ', '.join(scripts)

        # Synchronization service
        sync_service = self._find_element(metadata, 'synchronizationservice')
        if sync_service is not None:
            veml_props.sync_enabled = True
            veml_props.sync_type = sync_service.get('type', 'vss')
            veml_props.sync_address = sync_service.get('address', '')
            veml_props.sync_id = sync_service.get('id', '')
            veml_props.sync_session = sync_service.get('session', '')

    def _import_background(self, environment):
        """Import background settings"""
        background = self._find_element(environment, 'background')
        if background is None:
            return

        scene = self.context.scene
        veml_props = scene.veml_scene_properties

        # Check for color background
        color_elem = self._find_element(background, 'color')
        if color_elem is not None and color_elem.text:
            veml_props.background_type = 'COLOR'
            veml_props.background_color = self._parse_color(color_elem.text)
            return

        # Check for panorama
        panorama_elem = self._find_element(background, 'panorama')
        if panorama_elem is not None and panorama_elem.text:
            veml_props.background_type = 'PANORAMA'
            veml_props.background_panorama = panorama_elem.text
            return

        # Check for procedural sky
        sky_elem = self._find_element(background, 'lite-procedural-sky')
        if sky_elem is not None:
            veml_props.background_type = 'PROCEDURAL'
            veml_props.procedural_day_night_cycle = self._parse_bool(
                sky_elem.get('day-night-cycle-enabled', 'true')
            )
            veml_props.procedural_sun_enabled = self._parse_bool(
                sky_elem.get('sun-enabled', 'true')
            )
            veml_props.procedural_moon_enabled = self._parse_bool(
                sky_elem.get('moon-enabled', 'true')
            )
            veml_props.procedural_stars_enabled = self._parse_bool(
                sky_elem.get('stars-enabled', 'true')
            )
            veml_props.procedural_clouds_enabled = self._parse_bool(
                sky_elem.get('clouds-enabled', 'true')
            )

    def _import_effects(self, environment):
        """Import effects settings"""
        effects = self._find_element(environment, 'effects')
        if effects is None:
            return

        scene = self.context.scene
        veml_props = scene.veml_scene_properties

        # Check for fog
        fog_elem = self._find_element(effects, 'lite-fog')
        if fog_elem is not None:
            fog_enabled = fog_elem.get('fog-enabled', 'false')
            veml_props.fog_enabled = self._parse_bool(fog_enabled)

            color_str = fog_elem.get('color')
            if color_str:
                veml_props.fog_color = self._parse_color(color_str)

            density_str = fog_elem.get('density')
            if density_str:
                try:
                    veml_props.fog_density = float(density_str)
                except ValueError:
                    pass

    def _parse_color(self, color_str):
        """Parse VEML color string to Blender RGBA tuple"""
        from ..utils.color_utils import veml_to_blender_color
        return veml_to_blender_color(color_str)

    def _parse_bool(self, value):
        """Parse boolean string"""
        return value.lower() in ('true', '1', 'yes')
