# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import uuid
from xml.etree import ElementTree as ET

import bpy

from ..utils.color_utils import blender_to_veml_color, get_object_color
from ..utils.transform_utils import get_transform_elements


class EntityExporter:
    """Exports Blender objects to VEML entity elements"""

    # Mapping of Blender primitive mesh names to VEML entity types
    PRIMITIVE_MAP = {
        'Cube': 'cubemesh',
        'Sphere': 'spheremesh',
        'Cylinder': 'cylindermesh',
        'Cone': 'conemesh',
        'Plane': 'planemesh',
        'Torus': 'torusmesh',
        'Circle': 'planemesh',  # Circles become planes
        'Grid': 'planemesh',    # Grids become planes
        'Icosphere': 'spheremesh',
        'UV Sphere': 'spheremesh',
    }

    # Entity type string mapping from property enum
    ENTITY_TYPE_MAP = {
        'CONTAINER': 'container',
        'MESH': 'mesh',
        'CUBEMESH': 'cubemesh',
        'SPHEREMESH': 'spheremesh',
        'CYLINDERMESH': 'cylindermesh',
        'CONEMESH': 'conemesh',
        'PLANEMESH': 'planemesh',
        'TORUSMESH': 'torusmesh',
        'CAPSULEMESH': 'capsulemesh',
        'PRISMMESH': 'prismmesh',
        'ARCHMESH': 'archmesh',
        'TETRAHEDRONMESH': 'tetrahedronmesh',
        'RECTANGULARPYRAMIDMESH': 'rectangularpyramidmesh',
        'LIGHT': 'light',
        'AUDIO': 'audio',
        'CHARACTER': 'character',
        'CANVAS': 'canvas',
        'TEXT': 'text',
        'BUTTON': 'button',
        'INPUT': 'input',
        'IMAGE': 'image',
        'HTML': 'html',
        'TERRAIN': 'terrain',
        'WATER': 'water',
        'WATERBLOCKER': 'waterblocker',
        'VOXEL': 'voxel',
        'AUTOMOBILE': 'automobile',
        'AIRPLANE': 'airplane',
    }

    VEML_NAMESPACE = "http://www.fivesqd.com/schemas/veml/3.0"
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(self, mesh_exporter, export_meshes=True):
        self.mesh_exporter = mesh_exporter
        self.export_meshes = export_meshes

    def export_object(self, obj) -> ET.Element:
        """Export a Blender object to a VEML entity element"""
        # Skip hidden objects
        if obj.hide_viewport or obj.hide_render:
            return None

        # Determine entity type
        entity_type = self._get_entity_type(obj)
        if entity_type is None:
            return None

        # Create entity element with xsi:type
        entity = ET.Element('entity')
        entity.set(f'{{{self.XSI_NAMESPACE}}}type', f'vem:{entity_type}')

        # Set common attributes
        self._set_common_attributes(entity, obj)

        # Add transform
        transform = self._create_transform(obj)
        entity.append(transform)

        # Add type-specific content
        self._add_type_specific_content(entity, obj, entity_type)

        # Add synchronizer if specified
        if veml_props.synchronizer:
            synchronizer = ET.SubElement(entity, 'synchronizer')
            synchronizer.text = veml_props.synchronizer

        # Add placement sockets
        for socket in veml_props.placement_sockets:
            self._add_placement_socket(entity, socket)

        # Process children recursively
        self._process_children(entity, obj)

        return entity

    def _get_entity_type(self, obj) -> str:
        """Determine the VEML entity type for a Blender object"""
        veml_props = obj.veml_properties

        # Check for manual override
        if veml_props.entity_type != 'AUTO':
            return self.ENTITY_TYPE_MAP.get(veml_props.entity_type)

        # Auto-detect based on object type
        if obj.type == 'EMPTY':
            return 'container'

        elif obj.type == 'MESH':
            # Check if it's a known primitive
            mesh = obj.data
            if mesh.name in self.PRIMITIVE_MAP:
                return self.PRIMITIVE_MAP[mesh.name]
            # Check for common primitive naming patterns
            for primitive_name, veml_type in self.PRIMITIVE_MAP.items():
                if mesh.name.startswith(primitive_name):
                    return veml_type
            # Default to custom mesh
            return 'mesh'

        elif obj.type == 'LIGHT':
            return 'light'

        elif obj.type == 'SPEAKER':
            return 'audio'

        elif obj.type == 'ARMATURE':
            return 'character'

        elif obj.type == 'FONT':
            return 'text'

        elif obj.type == 'CAMERA':
            # Skip cameras by default (could be spawn point)
            return None

        else:
            # Default to container for other types
            return 'container'

    def _set_common_attributes(self, entity, obj):
        """Set common entity attributes (tag, id, on-load-event)"""
        veml_props = obj.veml_properties

        # Tag - use object name if not specified
        tag = veml_props.tag if veml_props.tag else obj.name
        entity.set('tag', tag)

        # ID - generate UUID if not specified
        if veml_props.entity_id:
            entity.set('id', veml_props.entity_id)
        else:
            entity.set('id', str(uuid.uuid4()))

        # On-load event
        if veml_props.on_load_event:
            entity.set('on-load-event', veml_props.on_load_event)

    def _create_transform(self, obj) -> ET.Element:
        """Create transform element for an object"""
        veml_props = obj.veml_properties
        transform = ET.Element('transform')

        pos, rot, scale = get_transform_elements(obj)

        if veml_props.use_canvas_transform:
            # Canvas transform (position-percent, size-percent)
            transform.set(f'{{{self.XSI_NAMESPACE}}}type', 'vem:canvastransform')

            # Position percent
            position_percent = ET.SubElement(transform, 'position-percent')
            position_percent.set('x', str(round(veml_props.canvas_position_x, 6)))
            position_percent.set('y', str(round(veml_props.canvas_position_y, 6)))

            # Size percent
            size_percent = ET.SubElement(transform, 'size-percent')
            size_percent.set('x', str(round(veml_props.canvas_size_x, 6)))
            size_percent.set('y', str(round(veml_props.canvas_size_y, 6)))

            # Alignment attributes (only if not NONE)
            if veml_props.canvas_align_horizontal != 'NONE':
                transform.set('align-horizontal', veml_props.canvas_align_horizontal.lower())
            if veml_props.canvas_align_vertical != 'NONE':
                transform.set('align-vertical', veml_props.canvas_align_vertical.lower())
            if veml_props.canvas_stretch_to_parent:
                transform.set('stretch-to-parent', 'true')

        elif veml_props.transform_type == 'SIZE':
            # Size transform (position, rotation, size in meters)
            transform.set(f'{{{self.XSI_NAMESPACE}}}type', 'vem:sizetransform')

            # Position
            position = ET.SubElement(transform, 'position')
            position.set('x', str(round(pos[0], 6)))
            position.set('y', str(round(pos[1], 6)))
            position.set('z', str(round(pos[2], 6)))

            # Rotation (quaternion)
            rotation = ET.SubElement(transform, 'rotation')
            rotation.set('x', str(round(rot[0], 6)))
            rotation.set('y', str(round(rot[1], 6)))
            rotation.set('z', str(round(rot[2], 6)))
            rotation.set('w', str(round(rot[3], 6)))

            # Size (in meters) - use custom size values
            size_elem = ET.SubElement(transform, 'size')
            size_elem.set('x', str(round(veml_props.size_x, 6)))
            size_elem.set('y', str(round(veml_props.size_y, 6)))
            size_elem.set('z', str(round(veml_props.size_z, 6)))
        else:
            # Scale transform (default)
            transform.set(f'{{{self.XSI_NAMESPACE}}}type', 'vem:scaletransform')

            # Position
            position = ET.SubElement(transform, 'position')
            position.set('x', str(round(pos[0], 6)))
            position.set('y', str(round(pos[1], 6)))
            position.set('z', str(round(pos[2], 6)))

            # Rotation (quaternion)
            rotation = ET.SubElement(transform, 'rotation')
            rotation.set('x', str(round(rot[0], 6)))
            rotation.set('y', str(round(rot[1], 6)))
            rotation.set('z', str(round(rot[2], 6)))
            rotation.set('w', str(round(rot[3], 6)))

            # Scale
            scale_elem = ET.SubElement(transform, 'scale')
            scale_elem.set('x', str(round(scale[0], 6)))
            scale_elem.set('y', str(round(scale[1], 6)))
            scale_elem.set('z', str(round(scale[2], 6)))

        return transform

    def _add_type_specific_content(self, entity, obj, entity_type):
        """Add type-specific elements to entity"""
        veml_props = obj.veml_properties

        # Primitive meshes need color
        primitive_types = [
            'cubemesh', 'spheremesh', 'cylindermesh', 'conemesh',
            'planemesh', 'torusmesh', 'capsulemesh', 'prismmesh',
            'archmesh', 'tetrahedronmesh', 'rectangularpyramidmesh'
        ]

        if entity_type in primitive_types:
            color_elem = ET.SubElement(entity, 'color')
            if veml_props.use_custom_color:
                color_elem.text = blender_to_veml_color(veml_props.color)
            else:
                color_elem.text = get_object_color(obj)

        elif entity_type == 'mesh':
            # Custom mesh
            mesh_name = ET.SubElement(entity, 'mesh-name')
            mesh_name.text = veml_props.mesh_name if veml_props.mesh_name else obj.data.name

            if self.export_meshes:
                # Export mesh and add resource
                mesh_path = self.mesh_exporter.export_mesh(obj)
                if mesh_path:
                    mesh_resource = ET.SubElement(entity, 'mesh-resource')
                    mesh_resource.text = mesh_path

        elif entity_type == 'audio':
            # Audio entity
            audio_file = ET.SubElement(entity, 'audio-file')
            audio_file.text = veml_props.audio_file

            auto_play = ET.SubElement(entity, 'auto-play')
            auto_play.text = str(veml_props.audio_autoplay).lower()

            loop = ET.SubElement(entity, 'loop')
            loop.text = str(veml_props.audio_loop).lower()

            volume = ET.SubElement(entity, 'volume')
            volume.text = str(veml_props.audio_volume)

        elif entity_type == 'text' and obj.type == 'FONT':
            # Text entity from Blender text object
            entity.set('text', obj.data.body)
            entity.set('font-size', str(veml_props.text_font_size))
            self._add_text_style_properties(entity, veml_props)

        elif entity_type == 'light' and obj.type == 'LIGHT':
            # Light entity
            self._add_light_properties(entity, obj, veml_props)

        elif entity_type == 'character':
            # Character entity
            self._add_character_properties(entity, obj, veml_props)

        elif entity_type == 'button':
            # Button entity
            if veml_props.button_on_click:
                entity.set('on-click-event', veml_props.button_on_click)
            if veml_props.button_color:
                entity.set('color', blender_to_veml_color(veml_props.button_color))

        elif entity_type == 'image':
            # Image entity
            if veml_props.image_file:
                image_file = ET.SubElement(entity, 'image-file')
                image_file.text = veml_props.image_file

        elif entity_type == 'html':
            # HTML entity
            if veml_props.html_url:
                entity.set('url', veml_props.html_url)
            if veml_props.html_on_message:
                entity.set('on-message', veml_props.html_on_message)

        elif entity_type == 'text' and veml_props.entity_type == 'TEXT':
            # Text entity from manual override (not Blender FONT object)
            self._add_text_properties(entity, obj, veml_props)

        elif entity_type == 'terrain':
            # Terrain entity
            self._add_terrain_properties(entity, obj, veml_props)

        elif entity_type == 'water':
            # Water entity
            self._add_water_properties(entity, obj, veml_props)

        elif entity_type == 'automobile':
            # Automobile entity
            self._add_automobile_properties(entity, obj, veml_props)

        elif entity_type == 'airplane':
            # Airplane entity
            self._add_airplane_properties(entity, obj, veml_props)

    def _add_text_properties(self, entity, obj, veml_props):
        """Add text-specific properties to entity"""
        # Required attributes
        entity.set('text', veml_props.text_content or "")
        entity.set('font-size', str(veml_props.text_font_size))
        
        # Style properties
        self._add_text_style_properties(entity, veml_props)

    def _add_text_style_properties(self, entity, veml_props):
        """Add text style properties (shared between TEXT entities and FONT objects)"""
        # Font
        if veml_props.text_font:
            entity.set('font', veml_props.text_font)
        
        # Color
        if veml_props.text_color:
            entity.set('color', blender_to_veml_color(veml_props.text_color))
        
        # Style flags
        if veml_props.text_bold:
            entity.set('bold', 'true')
        if veml_props.text_italic:
            entity.set('italic', 'true')
        if veml_props.text_underline:
            entity.set('underline', 'true')
        if veml_props.text_strikethrough:
            entity.set('strikethrough', 'true')
        
        # Alignment
        if veml_props.text_align_horizontal != 'NONE':
            entity.set('text-align-horizontal', veml_props.text_align_horizontal.lower())
        if veml_props.text_align_vertical != 'NONE':
            entity.set('text-align-vertical', veml_props.text_align_vertical.lower())
        
        # Wrap
        if veml_props.text_wrap == 'NO_WRAP':
            entity.set('text-wrap', 'no-wrap')
        elif veml_props.text_wrap == 'WRAP':
            entity.set('text-wrap', 'wrap')

    def _add_terrain_properties(self, entity, obj, veml_props):
        """Add terrain-specific properties to entity"""
        # Required attributes
        entity.set('length', str(veml_props.terrain_length))
        entity.set('width', str(veml_props.terrain_width))
        entity.set('height', str(veml_props.terrain_height))
        entity.set('type', veml_props.terrain_type.lower())

        # Heights (optional)
        if veml_props.terrain_heights:
            entity.set('heights', veml_props.terrain_heights)

        # For now, add a default layer (user would need to expand this)
        layer = ET.SubElement(entity, 'layer')
        diffuse = ET.SubElement(layer, 'diffuse-texture')
        diffuse.text = 'default_diffuse.png'
        normal = ET.SubElement(layer, 'normal-texture')
        normal.text = 'default_normal.png'
        mask = ET.SubElement(layer, 'mask-texture')
        mask.text = 'default_mask.png'
        specular = ET.SubElement(layer, 'specular')
        specular.text = '#ffffff'
        metallic = ET.SubElement(layer, 'metallic')
        metallic.text = '0'
        smoothness = ET.SubElement(layer, 'smoothness')
        smoothness.text = '0.5'

        # Layer masks
        layer_masks = ET.SubElement(entity, 'layer-masks')
        layer_masks.text = veml_props.terrain_layer_masks or '1'

    def _add_water_properties(self, entity, obj, veml_props):
        """Add water-specific properties to entity"""
        # Colors
        shallow_color = ET.SubElement(entity, 'shallow-color')
        shallow_color.text = blender_to_veml_color(veml_props.water_shallow_color)

        deep_color = ET.SubElement(entity, 'deep-color')
        deep_color.text = blender_to_veml_color(veml_props.water_deep_color)

        specular_color = ET.SubElement(entity, 'specular-color')
        specular_color.text = blender_to_veml_color(veml_props.water_specular_color)

        scattering_color = ET.SubElement(entity, 'scattering-color')
        scattering_color.text = blender_to_veml_color(veml_props.water_scattering_color)

        # Depth
        deep_start = ET.SubElement(entity, 'deep-start')
        deep_start.text = str(veml_props.water_deep_start)

        deep_end = ET.SubElement(entity, 'deep-end')
        deep_end.text = str(veml_props.water_deep_end)

        # Surface
        distortion = ET.SubElement(entity, 'distortion')
        distortion.text = str(veml_props.water_distortion)

        smoothness = ET.SubElement(entity, 'smoothness')
        smoothness.text = str(veml_props.water_smoothness)

        # Waves
        num_waves = ET.SubElement(entity, 'num-waves')
        num_waves.text = str(veml_props.water_num_waves)

        wave_amplitude = ET.SubElement(entity, 'wave-amplitude')
        wave_amplitude.text = str(veml_props.water_wave_amplitude)

        wave_steepness = ET.SubElement(entity, 'wave-steepness')
        wave_steepness.text = str(veml_props.water_wave_steepness)

        wave_speed = ET.SubElement(entity, 'wave-speed')
        wave_speed.text = str(veml_props.water_wave_speed)

        wave_length = ET.SubElement(entity, 'wave-length')
        wave_length.text = str(veml_props.water_wave_length)

        wave_scale = ET.SubElement(entity, 'wave-scale')
        wave_scale.text = str(veml_props.water_wave_scale)

        wave_intensity = ET.SubElement(entity, 'wave-intensity')
        wave_intensity.text = str(veml_props.water_wave_intensity)

    def _add_automobile_properties(self, entity, obj, veml_props):
        """Add automobile-specific properties to entity"""
        # Mesh
        mesh_name = ET.SubElement(entity, 'mesh-name')
        mesh_name.text = veml_props.automobile_mesh_name or obj.name

        if veml_props.automobile_mesh_resource:
            mesh_resource = ET.SubElement(entity, 'mesh-resource')
            mesh_resource.text = veml_props.automobile_mesh_resource

        # Wheels (parse from string format "submesh1:radius1,submesh2:radius2")
        if veml_props.automobile_wheels:
            wheel_defs = veml_props.automobile_wheels.split(',')
            for wheel_def in wheel_defs:
                wheel_def = wheel_def.strip()
                if ':' in wheel_def:
                    submesh, radius = wheel_def.split(':', 1)
                    wheels = ET.SubElement(entity, 'wheels')
                    wheel_submesh = ET.SubElement(wheels, 'wheel-submesh')
                    wheel_submesh.text = submesh.strip()
                    wheel_radius = ET.SubElement(wheels, 'wheel-radius')
                    wheel_radius.text = radius.strip()

        # Mass
        mass = ET.SubElement(entity, 'mass')
        mass.text = str(veml_props.automobile_mass)

        # Type
        auto_type = ET.SubElement(entity, 'automobile-type')
        auto_type.text = veml_props.automobile_type

    def _add_airplane_properties(self, entity, obj, veml_props):
        """Add airplane-specific properties to entity"""
        # Mesh
        mesh_name = ET.SubElement(entity, 'mesh-name')
        mesh_name.text = veml_props.airplane_mesh_name or obj.name

        if veml_props.airplane_mesh_resource:
            mesh_resource = ET.SubElement(entity, 'mesh-resource')
            mesh_resource.text = veml_props.airplane_mesh_resource

        # Mass
        mass = ET.SubElement(entity, 'mass')
        mass.text = str(veml_props.airplane_mass)

    def _add_character_properties(self, entity, obj, veml_props):
        """Add character-specific properties to entity"""
        # Mesh name (optional)
        if veml_props.character_mesh_name:
            mesh_name = ET.SubElement(entity, 'mesh-name')
            mesh_name.text = veml_props.character_mesh_name

        # Mesh resource (optional)
        if veml_props.character_mesh_resource:
            mesh_resource = ET.SubElement(entity, 'mesh-resource')
            mesh_resource.text = veml_props.character_mesh_resource

        # Mesh offset (optional - only if non-zero)
        if (veml_props.character_mesh_offset_x != 0 or 
            veml_props.character_mesh_offset_y != 0 or 
            veml_props.character_mesh_offset_z != 0):
            mesh_offset = ET.SubElement(entity, 'mesh-offset')
            mesh_offset.set('x', str(round(veml_props.character_mesh_offset_x, 6)))
            mesh_offset.set('y', str(round(veml_props.character_mesh_offset_y, 6)))
            mesh_offset.set('z', str(round(veml_props.character_mesh_offset_z, 6)))

        # Mesh rotation (optional - only if non-identity)
        if (veml_props.character_mesh_rotation_x != 0 or 
            veml_props.character_mesh_rotation_y != 0 or 
            veml_props.character_mesh_rotation_z != 0 or 
            veml_props.character_mesh_rotation_w != 1):
            mesh_rotation = ET.SubElement(entity, 'mesh-rotation')
            mesh_rotation.set('x', str(round(veml_props.character_mesh_rotation_x, 6)))
            mesh_rotation.set('y', str(round(veml_props.character_mesh_rotation_y, 6)))
            mesh_rotation.set('z', str(round(veml_props.character_mesh_rotation_z, 6)))
            mesh_rotation.set('w', str(round(veml_props.character_mesh_rotation_w, 6)))

        # Label offset (optional - only if non-zero)
        if (veml_props.character_label_offset_x != 0 or 
            veml_props.character_label_offset_y != 0 or 
            veml_props.character_label_offset_z != 0):
            label_offset = ET.SubElement(entity, 'label-offset')
            label_offset.set('x', str(round(veml_props.character_label_offset_x, 6)))
            label_offset.set('y', str(round(veml_props.character_label_offset_y, 6)))
            label_offset.set('z', str(round(veml_props.character_label_offset_z, 6)))

    def _add_light_properties(self, entity, obj, veml_props):
        """Add light-specific properties to entity"""
        light_data = obj.data

        # Determine light type
        light_type_map = {
            'POINT': 'point',
            'SUN': 'directional',
            'SPOT': 'spot',
            'AREA': 'area',
        }
        light_type = light_type_map.get(light_data.type, 'point')
        light_type_elem = ET.SubElement(entity, 'light-type')
        light_type_elem.text = light_type

        # Get color and intensity from Blender or custom properties
        if veml_props.light_use_blender_settings:
            # Use Blender light settings
            color = list(light_data.color) + [1.0]  # RGB -> RGBA
            intensity = light_data.energy
            
            # Get range (use shadow_soft_size or calculate from energy)
            if hasattr(light_data, 'cutoff_distance') and light_data.use_custom_distance:
                light_range = light_data.cutoff_distance
            else:
                # Approximate range from energy
                light_range = max(1.0, intensity * 2.0)
            
            # Spot angle
            if light_data.type == 'SPOT':
                import math
                spot_angle = math.degrees(light_data.spot_size)
            else:
                spot_angle = 45.0
        else:
            # Use custom VEML properties
            color = veml_props.light_color
            intensity = veml_props.light_intensity
            light_range = veml_props.light_range
            spot_angle = veml_props.light_spot_angle

        # Color
        color_elem = ET.SubElement(entity, 'color')
        color_elem.text = blender_to_veml_color(color)

        # Intensity
        intensity_elem = ET.SubElement(entity, 'intensity')
        intensity_elem.text = str(round(intensity, 4))

        # Range
        range_elem = ET.SubElement(entity, 'range')
        range_elem.text = str(round(light_range, 4))

        # Spot-specific properties
        if light_type == 'spot':
            spot_angle_elem = ET.SubElement(entity, 'spot-angle')
            spot_angle_elem.text = str(round(spot_angle, 4))

        # Shadows
        shadows_elem = ET.SubElement(entity, 'cast-shadows')
        shadows_elem.text = str(veml_props.light_cast_shadows).lower()

    def _process_children(self, entity, obj):
        """Recursively process child objects"""
        children = sorted(obj.children, key=lambda o: o.name)

        for child in children:
            child_entity = self.export_object(child)
            if child_entity is not None:
                entity.append(child_entity)

    def _add_placement_socket(self, entity, socket):
        """Add a placement socket element to entity"""
        socket_elem = ET.SubElement(entity, 'placement-socket')

        # Position
        position = ET.SubElement(socket_elem, 'position')
        position.set('x', str(round(socket.position_x, 6)))
        position.set('y', str(round(socket.position_y, 6)))
        position.set('z', str(round(socket.position_z, 6)))

        # Rotation
        rotation = ET.SubElement(socket_elem, 'rotation')
        rotation.set('x', str(round(socket.rotation_x, 6)))
        rotation.set('y', str(round(socket.rotation_y, 6)))
        rotation.set('z', str(round(socket.rotation_z, 6)))
        rotation.set('w', str(round(socket.rotation_w, 6)))

        # Connecting offset
        connecting_offset = ET.SubElement(socket_elem, 'connecting-offset')
        connecting_offset.set('x', str(round(socket.connecting_offset_x, 6)))
        connecting_offset.set('y', str(round(socket.connecting_offset_y, 6)))
        connecting_offset.set('z', str(round(socket.connecting_offset_z, 6)))
