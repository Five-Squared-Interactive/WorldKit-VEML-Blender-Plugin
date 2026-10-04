# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

import math
from xml.etree import ElementTree as ET

import bpy
from mathutils import Vector, Quaternion

from ..utils.color_utils import veml_to_blender_color
from ..utils.transform_utils import convert_position_from_yup, convert_rotation_from_yup


class EntityImporter:
    """Imports VEML entity elements to Blender objects"""

    VEML_NAMESPACE = "http://www.fivesqd.com/schemas/veml/4.0"  # 4.0
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

    # Mapping of VEML entity types to Blender primitive creation
    PRIMITIVE_MAP = {
        'cubemesh': ('MESH', 'Cube'),
        'spheremesh': ('MESH', 'Sphere'),
        'cylindermesh': ('MESH', 'Cylinder'),
        'conemesh': ('MESH', 'Cone'),
        'planemesh': ('MESH', 'Plane'),
        'torusmesh': ('MESH', 'Torus'),
        'capsulemesh': ('MESH', 'Capsule'),
        'prismmesh': ('MESH', 'Prism'),
        'archmesh': ('MESH', 'Arch'),
        'tetrahedronmesh': ('MESH', 'Tetrahedron'),
        'rectangularpyramidmesh': ('MESH', 'Pyramid'),
    }

    # Entity type to Blender property enum mapping
    ENTITY_TYPE_ENUM = {
        'container': 'CONTAINER',
        'mesh': 'MESH',
        'cubemesh': 'CUBEMESH',
        'spheremesh': 'SPHEREMESH',
        'cylindermesh': 'CYLINDERMESH',
        'conemesh': 'CONEMESH',
        'planemesh': 'PLANEMESH',
        'torusmesh': 'TORUSMESH',
        'capsulemesh': 'CAPSULEMESH',
        'prismmesh': 'PRISMMESH',
        'archmesh': 'ARCHMESH',
        'tetrahedronmesh': 'TETRAHEDRONMESH',
        'rectangularpyramidmesh': 'RECTANGULARPYRAMIDMESH',
        'light': 'LIGHT',
        'audio': 'AUDIO',
        'character': 'CHARACTER',
        'canvas': 'CANVAS',
        'text': 'TEXT',
        'button': 'BUTTON',
        'input': 'INPUT',
        'image': 'IMAGE',
        'html': 'HTML',
        'terrain': 'TERRAIN',
        'water': 'WATER',
        'waterblocker': 'WATERBLOCKER',
        'voxel': 'VOXEL',
        'automobile': 'AUTOMOBILE',
        'airplane': 'AIRPLANE',
    }

    def __init__(self, mesh_importer, import_meshes=True, set_properties=True):
        self.mesh_importer = mesh_importer
        self.import_meshes = import_meshes
        self.set_properties = set_properties

    def import_entity(self, entity_elem, parent=None):
        """Import a VEML entity element and create corresponding Blender object"""
        # Get entity type from xsi:type attribute
        entity_type = self._get_entity_type(entity_elem)
        if entity_type is None:
            return None

        # Get tag (name) for the object
        tag = entity_elem.get('tag', 'Entity')

        # Create the appropriate Blender object
        obj = self._create_object(entity_type, tag, entity_elem)
        if obj is None:
            return None

        # Set parent
        if parent is not None:
            obj.parent = parent

        # Apply transform
        self._apply_transform(obj, entity_elem)

        # Set VEML properties
        if self.set_properties:
            self._set_veml_properties(obj, entity_elem, entity_type)

        # Import type-specific properties
        self._import_type_specific(obj, entity_elem, entity_type)

        # Process child entities — the 4.0 entity FAMILY (§4.1).
        for child in entity_elem:
            child_tag = self._strip_namespace(child.tag)
            if child_tag in ('entity', 'container', 'asset', 'primitive', 'html', 'lod'):
                self.import_entity(child, parent=obj)

        return obj

    def _get_entity_type(self, entity_elem):
        """Determine the entity kind. In 4.0 the ELEMENT NAME is the
        discriminator (asset/primitive/container/entity/html/lod); the
        prototype-era xsi:type attribute remains as a legacy fallback for
        pre-4.0 files."""
        local = self._strip_namespace(entity_elem.tag).lower()
        if local == 'asset':
            return 'mesh'
        if local == 'primitive':
            shape = (entity_elem.get('shape') or 'cube').replace('-', '')
            return f'{shape}mesh'
        if local in ('container', 'lod'):
            return 'container'
        if local == 'html':
            return 'html'

        xsi_type = entity_elem.get(f'{{{self.XSI_NAMESPACE}}}type')
        if xsi_type is None:
            # Try without namespace
            xsi_type = entity_elem.get('type')

        if xsi_type is None:
            return 'container'  # Default

        # Remove 'vem:' prefix if present
        if ':' in xsi_type:
            xsi_type = xsi_type.split(':')[1]

        return xsi_type.lower()

    def _strip_namespace(self, tag):
        """Remove namespace from tag"""
        if tag.startswith('{'):
            return tag.split('}')[1]
        return tag

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

    def _create_object(self, entity_type, name, entity_elem):
        """Create a Blender object based on entity type"""
        
        # Primitive meshes
        if entity_type in self.PRIMITIVE_MAP:
            return self._create_primitive(entity_type, name, entity_elem)

        # Custom mesh
        elif entity_type == 'mesh':
            return self._create_custom_mesh(name, entity_elem)

        # Container (empty)
        elif entity_type == 'container':
            return self._create_empty(name)

        # Light
        elif entity_type == 'light':
            return self._create_light(name, entity_elem)

        # Audio (speaker)
        elif entity_type == 'audio':
            return self._create_speaker(name, entity_elem)

        # Character (armature placeholder)
        elif entity_type == 'character':
            return self._create_empty(name, empty_type='PLAIN_AXES')

        # Text
        elif entity_type == 'text':
            return self._create_text(name, entity_elem)

        # Canvas/UI elements - create as empties
        elif entity_type in ('canvas', 'button', 'input', 'image', 'html'):
            return self._create_empty(name, empty_type='CUBE')

        # Terrain, water, etc. - create as placeholder empties
        elif entity_type in ('terrain', 'water', 'waterblocker', 'voxel', 'automobile', 'airplane'):
            return self._create_empty(name, empty_type='CUBE')

        else:
            # Unknown type - create empty
            return self._create_empty(name)

    def _create_primitive(self, entity_type, name, entity_elem):
        """Create a primitive mesh object"""
        primitive_info = self.PRIMITIVE_MAP.get(entity_type)
        if primitive_info is None:
            return self._create_empty(name)

        obj_type, mesh_type = primitive_info

        # Create the mesh
        if mesh_type == 'Cube':
            bpy.ops.mesh.primitive_cube_add()
        elif mesh_type == 'Sphere':
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif mesh_type == 'Cylinder':
            bpy.ops.mesh.primitive_cylinder_add()
        elif mesh_type == 'Cone':
            bpy.ops.mesh.primitive_cone_add()
        elif mesh_type == 'Plane':
            bpy.ops.mesh.primitive_plane_add()
        elif mesh_type == 'Torus':
            bpy.ops.mesh.primitive_torus_add()
        else:
            # For types without direct Blender equivalent, use cube
            bpy.ops.mesh.primitive_cube_add()

        obj = bpy.context.active_object
        obj.name = name

        # Apply color if specified
        color_elem = self._find_element(entity_elem, 'color')
        if color_elem is not None and color_elem.text:
            self._apply_color(obj, color_elem.text)

        return obj

    def _create_custom_mesh(self, name, entity_elem):
        """Create a custom mesh object by importing GLB/GLTF"""
        if not self.import_meshes:
            return self._create_empty(name, empty_type='CUBE')

        # 4.0 asset: the resource is the `src` ATTRIBUTE (§4.4).
        src = entity_elem.get('src')
        if src:
            obj = self.mesh_importer.import_mesh(src)
            if obj is not None:
                obj.name = name
                return obj

        # Legacy (pre-4.0) mesh-resource child element fallback.
        mesh_resource = self._find_element(entity_elem, 'mesh-resource')
        if mesh_resource is not None and mesh_resource.text:
            obj = self.mesh_importer.import_mesh(mesh_resource.text)
            if obj is not None:
                obj.name = name
                return obj

        # Fallback to empty if no mesh resource
        return self._create_empty(name, empty_type='CUBE')

    def _create_empty(self, name, empty_type='PLAIN_AXES'):
        """Create an empty object"""
        bpy.ops.object.empty_add(type=empty_type)
        obj = bpy.context.active_object
        obj.name = name
        return obj

    def _create_light(self, name, entity_elem):
        """Create a light object"""
        # Determine light type
        light_type_elem = self._find_element(entity_elem, 'light-type')
        light_type_str = light_type_elem.text if light_type_elem is not None else 'point'

        light_type_map = {
            'point': 'POINT',
            'directional': 'SUN',
            'spot': 'SPOT',
            'area': 'AREA',
        }
        blender_light_type = light_type_map.get(light_type_str.lower(), 'POINT')

        # Create light
        bpy.ops.object.light_add(type=blender_light_type)
        obj = bpy.context.active_object
        obj.name = name

        # Apply light properties
        light_data = obj.data

        # Color
        color_elem = self._find_element(entity_elem, 'color')
        if color_elem is not None and color_elem.text:
            color = veml_to_blender_color(color_elem.text)
            light_data.color = color[:3]

        # Intensity
        intensity_elem = self._find_element(entity_elem, 'intensity')
        if intensity_elem is not None and intensity_elem.text:
            try:
                light_data.energy = float(intensity_elem.text)
            except ValueError:
                pass

        # Spot angle
        if blender_light_type == 'SPOT':
            spot_angle_elem = self._find_element(entity_elem, 'spot-angle')
            if spot_angle_elem is not None and spot_angle_elem.text:
                try:
                    light_data.spot_size = math.radians(float(spot_angle_elem.text))
                except ValueError:
                    pass

        return obj

    def _create_speaker(self, name, entity_elem):
        """Create a speaker object for audio"""
        bpy.ops.object.speaker_add()
        obj = bpy.context.active_object
        obj.name = name
        return obj

    def _create_text(self, name, entity_elem):
        """Create a text object"""
        bpy.ops.object.text_add()
        obj = bpy.context.active_object
        obj.name = name

        # Set text content
        text_content = entity_elem.get('text', '')
        if text_content:
            obj.data.body = text_content

        return obj

    def _apply_transform(self, obj, entity_elem):
        """Apply transform from VEML to Blender object"""
        transform = self._find_element(entity_elem, 'transform')
        if transform is None:
            return

        # Get transform type
        xsi_type = transform.get(f'{{{self.XSI_NAMESPACE}}}type', '')
        if ':' in xsi_type:
            xsi_type = xsi_type.split(':')[1]

        # Position
        position = self._find_element(transform, 'position')
        if position is not None:
            x = float(position.get('x', 0))
            y = float(position.get('y', 0))
            z = float(position.get('z', 0))
            # Convert from Y-up to Blender Z-up
            obj.location = convert_position_from_yup((x, y, z))

        # Position percent (for canvas transform)
        position_percent = self._find_element(transform, 'position-percent')
        if position_percent is not None:
            # Store in VEML properties for canvas entities
            pass  # Handled in _set_veml_properties

        # Rotation
        rotation = self._find_element(transform, 'rotation')
        if rotation is not None:
            x = float(rotation.get('x', 0))
            y = float(rotation.get('y', 0))
            z = float(rotation.get('z', 0))
            w = float(rotation.get('w', 1))
            # Convert from Y-up to Blender Z-up
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = convert_rotation_from_yup((x, y, z, w))

        # Scale
        scale = self._find_element(transform, 'scale')
        if scale is not None:
            x = float(scale.get('x', 1))
            y = float(scale.get('y', 1))
            z = float(scale.get('z', 1))
            # Swap Y and Z for coordinate conversion
            obj.scale = (x, z, y)

        # Size (for size transform - store in properties)
        size = self._find_element(transform, 'size')
        if size is not None and self.set_properties:
            veml_props = obj.veml_properties
            veml_props.transform_type = 'SIZE'
            veml_props.size_x = float(size.get('x', 1))
            veml_props.size_y = float(size.get('y', 1))
            veml_props.size_z = float(size.get('z', 1))

    def _set_veml_properties(self, obj, entity_elem, entity_type):
        """Set VEML-specific properties on the object"""
        veml_props = obj.veml_properties

        # Entity type
        enum_value = self.ENTITY_TYPE_ENUM.get(entity_type, 'AUTO')
        veml_props.entity_type = enum_value

        # Tag
        tag = entity_elem.get('tag', '')
        if tag:
            veml_props.tag = tag

        # ID
        entity_id = entity_elem.get('id', '')
        if entity_id:
            veml_props.entity_id = entity_id

        # On-load event
        on_load = entity_elem.get('on-load-event', '')
        if on_load:
            veml_props.on_load_event = on_load

        # Synchronizer
        sync_elem = self._find_element(entity_elem, 'synchronizer')
        if sync_elem is not None and sync_elem.text:
            veml_props.synchronizer = sync_elem.text

        # Canvas transform properties
        transform = self._find_element(entity_elem, 'transform')
        if transform is not None:
            xsi_type = transform.get(f'{{{self.XSI_NAMESPACE}}}type', '')
            if 'canvastransform' in xsi_type.lower():
                veml_props.use_canvas_transform = True

                pos_percent = self._find_element(transform, 'position-percent')
                if pos_percent is not None:
                    veml_props.canvas_position_x = float(pos_percent.get('x', 0))
                    veml_props.canvas_position_y = float(pos_percent.get('y', 0))

                size_percent = self._find_element(transform, 'size-percent')
                if size_percent is not None:
                    veml_props.canvas_size_x = float(size_percent.get('x', 1))
                    veml_props.canvas_size_y = float(size_percent.get('y', 1))

                # Alignment
                h_align = transform.get('align-horizontal', '')
                if h_align:
                    veml_props.canvas_align_horizontal = h_align.upper()

                v_align = transform.get('align-vertical', '')
                if v_align:
                    veml_props.canvas_align_vertical = v_align.upper()

                stretch = transform.get('stretch-to-parent', '')
                veml_props.canvas_stretch_to_parent = stretch.lower() == 'true'

        # Placement sockets
        for child in entity_elem:
            if self._strip_namespace(child.tag) == 'placement-socket':
                self._import_placement_socket(veml_props, child)

    def _import_placement_socket(self, veml_props, socket_elem):
        """Import a placement socket"""
        socket = veml_props.placement_sockets.add()

        # Position
        position = self._find_element(socket_elem, 'position')
        if position is not None:
            socket.position_x = float(position.get('x', 0))
            socket.position_y = float(position.get('y', 0))
            socket.position_z = float(position.get('z', 0))

        # Rotation
        rotation = self._find_element(socket_elem, 'rotation')
        if rotation is not None:
            socket.rotation_x = float(rotation.get('x', 0))
            socket.rotation_y = float(rotation.get('y', 0))
            socket.rotation_z = float(rotation.get('z', 0))
            socket.rotation_w = float(rotation.get('w', 1))

        # Connecting offset
        offset = self._find_element(socket_elem, 'connecting-offset')
        if offset is not None:
            socket.connecting_offset_x = float(offset.get('x', 0))
            socket.connecting_offset_y = float(offset.get('y', 0))
            socket.connecting_offset_z = float(offset.get('z', 0))

    def _import_type_specific(self, obj, entity_elem, entity_type):
        """Import type-specific properties"""
        if not self.set_properties:
            return

        veml_props = obj.veml_properties

        if entity_type == 'audio':
            self._import_audio_properties(veml_props, entity_elem)
        elif entity_type == 'light':
            self._import_light_properties(veml_props, entity_elem, obj)
        elif entity_type == 'character':
            self._import_character_properties(veml_props, entity_elem)
        elif entity_type == 'text':
            self._import_text_properties(veml_props, entity_elem)
        elif entity_type == 'button':
            self._import_button_properties(veml_props, entity_elem)
        elif entity_type == 'image':
            self._import_image_properties(veml_props, entity_elem)
        elif entity_type == 'html':
            self._import_html_properties(veml_props, entity_elem)
        elif entity_type == 'terrain':
            self._import_terrain_properties(veml_props, entity_elem)
        elif entity_type == 'water':
            self._import_water_properties(veml_props, entity_elem)
        elif entity_type == 'automobile':
            self._import_automobile_properties(veml_props, entity_elem)
        elif entity_type == 'airplane':
            self._import_airplane_properties(veml_props, entity_elem)

    def _import_audio_properties(self, veml_props, entity_elem):
        """Import audio entity properties"""
        audio_file = self._find_element(entity_elem, 'audio-file')
        if audio_file is not None and audio_file.text:
            veml_props.audio_file = audio_file.text

        auto_play = self._find_element(entity_elem, 'auto-play')
        if auto_play is not None and auto_play.text:
            veml_props.audio_autoplay = auto_play.text.lower() == 'true'

        loop = self._find_element(entity_elem, 'loop')
        if loop is not None and loop.text:
            veml_props.audio_loop = loop.text.lower() == 'true'

        volume = self._find_element(entity_elem, 'volume')
        if volume is not None and volume.text:
            try:
                veml_props.audio_volume = float(volume.text)
            except ValueError:
                pass

    def _import_light_properties(self, veml_props, entity_elem, obj):
        """Import light entity properties"""
        veml_props.light_use_blender_settings = False

        color_elem = self._find_element(entity_elem, 'color')
        if color_elem is not None and color_elem.text:
            veml_props.light_color = veml_to_blender_color(color_elem.text)

        intensity = self._find_element(entity_elem, 'intensity')
        if intensity is not None and intensity.text:
            try:
                veml_props.light_intensity = float(intensity.text)
            except ValueError:
                pass

        range_elem = self._find_element(entity_elem, 'range')
        if range_elem is not None and range_elem.text:
            try:
                veml_props.light_range = float(range_elem.text)
            except ValueError:
                pass

        spot_angle = self._find_element(entity_elem, 'spot-angle')
        if spot_angle is not None and spot_angle.text:
            try:
                veml_props.light_spot_angle = float(spot_angle.text)
            except ValueError:
                pass

        cast_shadows = self._find_element(entity_elem, 'cast-shadows')
        if cast_shadows is not None and cast_shadows.text:
            veml_props.light_cast_shadows = cast_shadows.text.lower() == 'true'

    def _import_character_properties(self, veml_props, entity_elem):
        """Import character entity properties"""
        mesh_name = self._find_element(entity_elem, 'mesh-name')
        if mesh_name is not None and mesh_name.text:
            veml_props.character_mesh_name = mesh_name.text

        mesh_resource = self._find_element(entity_elem, 'mesh-resource')
        if mesh_resource is not None and mesh_resource.text:
            veml_props.character_mesh_resource = mesh_resource.text

        # Mesh offset
        mesh_offset = self._find_element(entity_elem, 'mesh-offset')
        if mesh_offset is not None:
            veml_props.character_mesh_offset_x = float(mesh_offset.get('x', 0))
            veml_props.character_mesh_offset_y = float(mesh_offset.get('y', 0))
            veml_props.character_mesh_offset_z = float(mesh_offset.get('z', 0))

        # Mesh rotation
        mesh_rotation = self._find_element(entity_elem, 'mesh-rotation')
        if mesh_rotation is not None:
            veml_props.character_mesh_rotation_x = float(mesh_rotation.get('x', 0))
            veml_props.character_mesh_rotation_y = float(mesh_rotation.get('y', 0))
            veml_props.character_mesh_rotation_z = float(mesh_rotation.get('z', 0))
            veml_props.character_mesh_rotation_w = float(mesh_rotation.get('w', 1))

        # Label offset
        label_offset = self._find_element(entity_elem, 'label-offset')
        if label_offset is not None:
            veml_props.character_label_offset_x = float(label_offset.get('x', 0))
            veml_props.character_label_offset_y = float(label_offset.get('y', 0))
            veml_props.character_label_offset_z = float(label_offset.get('z', 0))

    def _import_text_properties(self, veml_props, entity_elem):
        """Import text entity properties"""
        text = entity_elem.get('text', '')
        if text:
            veml_props.text_content = text

        font_size = entity_elem.get('font-size')
        if font_size:
            try:
                veml_props.text_font_size = float(font_size)
            except ValueError:
                pass

        font = entity_elem.get('font', '')
        if font:
            veml_props.text_font = font

        color = entity_elem.get('color')
        if color:
            veml_props.text_color = veml_to_blender_color(color)

        # Style flags
        veml_props.text_bold = entity_elem.get('bold', '').lower() == 'true'
        veml_props.text_italic = entity_elem.get('italic', '').lower() == 'true'
        veml_props.text_underline = entity_elem.get('underline', '').lower() == 'true'
        veml_props.text_strikethrough = entity_elem.get('strikethrough', '').lower() == 'true'

        # Alignment
        h_align = entity_elem.get('text-align-horizontal', '')
        if h_align:
            veml_props.text_align_horizontal = h_align.upper()

        v_align = entity_elem.get('text-align-vertical', '')
        if v_align:
            veml_props.text_align_vertical = v_align.upper()

        # Wrap
        wrap = entity_elem.get('text-wrap', '')
        if wrap == 'no-wrap':
            veml_props.text_wrap = 'NO_WRAP'
        elif wrap == 'wrap':
            veml_props.text_wrap = 'WRAP'

    def _import_button_properties(self, veml_props, entity_elem):
        """Import button entity properties"""
        on_click = entity_elem.get('on-click-event', '')
        if on_click:
            veml_props.button_on_click = on_click

        color = entity_elem.get('color')
        if color:
            veml_props.button_color = veml_to_blender_color(color)

    def _import_image_properties(self, veml_props, entity_elem):
        """Import image entity properties"""
        image_file = self._find_element(entity_elem, 'image-file')
        if image_file is not None and image_file.text:
            veml_props.image_file = image_file.text

    def _import_html_properties(self, veml_props, entity_elem):
        """Import HTML entity properties"""
        url = entity_elem.get('url', '')
        if url:
            veml_props.html_url = url

        on_message = entity_elem.get('on-message', '')
        if on_message:
            veml_props.html_on_message = on_message

    def _import_terrain_properties(self, veml_props, entity_elem):
        """Import terrain entity properties"""
        length = entity_elem.get('length')
        if length:
            try:
                veml_props.terrain_length = float(length)
            except ValueError:
                pass

        width = entity_elem.get('width')
        if width:
            try:
                veml_props.terrain_width = float(width)
            except ValueError:
                pass

        height = entity_elem.get('height')
        if height:
            try:
                veml_props.terrain_height = float(height)
            except ValueError:
                pass

        terrain_type = entity_elem.get('type', '')
        if terrain_type:
            veml_props.terrain_type = terrain_type.upper()

        heights = entity_elem.get('heights', '')
        if heights:
            veml_props.terrain_heights = heights

    def _import_water_properties(self, veml_props, entity_elem):
        """Import water entity properties"""
        # Colors
        shallow_color = self._find_element(entity_elem, 'shallow-color')
        if shallow_color is not None and shallow_color.text:
            veml_props.water_shallow_color = veml_to_blender_color(shallow_color.text)

        deep_color = self._find_element(entity_elem, 'deep-color')
        if deep_color is not None and deep_color.text:
            veml_props.water_deep_color = veml_to_blender_color(deep_color.text)

        specular_color = self._find_element(entity_elem, 'specular-color')
        if specular_color is not None and specular_color.text:
            veml_props.water_specular_color = veml_to_blender_color(specular_color.text)

        scattering_color = self._find_element(entity_elem, 'scattering-color')
        if scattering_color is not None and scattering_color.text:
            veml_props.water_scattering_color = veml_to_blender_color(scattering_color.text)

        # Depth
        deep_start = self._find_element(entity_elem, 'deep-start')
        if deep_start is not None and deep_start.text:
            try:
                veml_props.water_deep_start = float(deep_start.text)
            except ValueError:
                pass

        deep_end = self._find_element(entity_elem, 'deep-end')
        if deep_end is not None and deep_end.text:
            try:
                veml_props.water_deep_end = float(deep_end.text)
            except ValueError:
                pass

        # Surface properties
        distortion = self._find_element(entity_elem, 'distortion')
        if distortion is not None and distortion.text:
            try:
                veml_props.water_distortion = float(distortion.text)
            except ValueError:
                pass

        smoothness = self._find_element(entity_elem, 'smoothness')
        if smoothness is not None and smoothness.text:
            try:
                veml_props.water_smoothness = float(smoothness.text)
            except ValueError:
                pass

        # Wave properties
        num_waves = self._find_element(entity_elem, 'num-waves')
        if num_waves is not None and num_waves.text:
            try:
                veml_props.water_num_waves = int(num_waves.text)
            except ValueError:
                pass

        wave_amplitude = self._find_element(entity_elem, 'wave-amplitude')
        if wave_amplitude is not None and wave_amplitude.text:
            try:
                veml_props.water_wave_amplitude = float(wave_amplitude.text)
            except ValueError:
                pass

        wave_steepness = self._find_element(entity_elem, 'wave-steepness')
        if wave_steepness is not None and wave_steepness.text:
            try:
                veml_props.water_wave_steepness = float(wave_steepness.text)
            except ValueError:
                pass

        wave_speed = self._find_element(entity_elem, 'wave-speed')
        if wave_speed is not None and wave_speed.text:
            try:
                veml_props.water_wave_speed = float(wave_speed.text)
            except ValueError:
                pass

        wave_length = self._find_element(entity_elem, 'wave-length')
        if wave_length is not None and wave_length.text:
            try:
                veml_props.water_wave_length = float(wave_length.text)
            except ValueError:
                pass

        wave_scale = self._find_element(entity_elem, 'wave-scale')
        if wave_scale is not None and wave_scale.text:
            try:
                veml_props.water_wave_scale = float(wave_scale.text)
            except ValueError:
                pass

        wave_intensity = self._find_element(entity_elem, 'wave-intensity')
        if wave_intensity is not None and wave_intensity.text:
            try:
                veml_props.water_wave_intensity = float(wave_intensity.text)
            except ValueError:
                pass

    def _import_automobile_properties(self, veml_props, entity_elem):
        """Import automobile entity properties"""
        mesh_name = self._find_element(entity_elem, 'mesh-name')
        if mesh_name is not None and mesh_name.text:
            veml_props.automobile_mesh_name = mesh_name.text

        mesh_resource = self._find_element(entity_elem, 'mesh-resource')
        if mesh_resource is not None and mesh_resource.text:
            veml_props.automobile_mesh_resource = mesh_resource.text

        mass = self._find_element(entity_elem, 'mass')
        if mass is not None and mass.text:
            try:
                veml_props.automobile_mass = float(mass.text)
            except ValueError:
                pass

        auto_type = self._find_element(entity_elem, 'automobile-type')
        if auto_type is not None and auto_type.text:
            veml_props.automobile_type = auto_type.text

    def _import_airplane_properties(self, veml_props, entity_elem):
        """Import airplane entity properties"""
        mesh_name = self._find_element(entity_elem, 'mesh-name')
        if mesh_name is not None and mesh_name.text:
            veml_props.airplane_mesh_name = mesh_name.text

        mesh_resource = self._find_element(entity_elem, 'mesh-resource')
        if mesh_resource is not None and mesh_resource.text:
            veml_props.airplane_mesh_resource = mesh_resource.text

        mass = self._find_element(entity_elem, 'mass')
        if mass is not None and mass.text:
            try:
                veml_props.airplane_mass = float(mass.text)
            except ValueError:
                pass

    def _apply_color(self, obj, color_str):
        """Apply a color to a mesh object as a material"""
        color = veml_to_blender_color(color_str)

        # Create material
        mat_name = f"{obj.name}_material"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True

        # Set up principled BSDF
        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            principled = nodes.get('Principled BSDF')
            if principled is None:
                for node in nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        principled = node
                        break

            if principled:
                principled.inputs['Base Color'].default_value = color

        # Assign material to object
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
