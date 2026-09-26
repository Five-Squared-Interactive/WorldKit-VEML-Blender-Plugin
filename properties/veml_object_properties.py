# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy

from . import entry_point
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)


class VEMLPlacementSocket(bpy.types.PropertyGroup):
    """A placement socket for an entity"""
    
    name: StringProperty(
        name="Socket Name",
        description="Name identifier for this socket",
        default="Socket",
    )
    
    # Position relative to entity
    position_x: FloatProperty(name="X", default=0.0)
    position_y: FloatProperty(name="Y", default=0.0)
    position_z: FloatProperty(name="Z", default=0.0)
    
    # Rotation relative to entity (quaternion)
    rotation_x: FloatProperty(name="X", default=0.0)
    rotation_y: FloatProperty(name="Y", default=0.0)
    rotation_z: FloatProperty(name="Z", default=0.0)
    rotation_w: FloatProperty(name="W", default=1.0)
    
    # Connecting offset
    connecting_offset_x: FloatProperty(name="X", default=0.0)
    connecting_offset_y: FloatProperty(name="Y", default=0.0)
    connecting_offset_z: FloatProperty(name="Z", default=0.0)


class VEMLObjectProperties(bpy.types.PropertyGroup):
    """VEML-specific properties for Blender objects"""

    tag: StringProperty(
        name="Tag",
        description="Tag identifier for the entity (human-readable)",
        default="",
    )

    entity_id: StringProperty(
        name="ID",
        description="UUID for the entity (auto-generated if empty)",
        default="",
    )

    entity_type: EnumProperty(
        name="Entity Type",
        description="Override automatic entity type detection",
        items=[
            ('AUTO', "Auto-detect", "Automatically detect entity type from object"),
            ('CONTAINER', "Container", "Empty container entity"),
            ('MESH', "Mesh", "Custom mesh entity"),
            ('CUBEMESH', "Cube", "Cube primitive mesh"),
            ('SPHEREMESH', "Sphere", "Sphere primitive mesh"),
            ('CYLINDERMESH', "Cylinder", "Cylinder primitive mesh"),
            ('CONEMESH', "Cone", "Cone primitive mesh"),
            ('PLANEMESH', "Plane", "Plane primitive mesh"),
            ('TORUSMESH', "Torus", "Torus primitive mesh"),
            ('CAPSULEMESH', "Capsule", "Capsule primitive mesh"),
            ('PRISMMESH', "Prism", "Prism primitive mesh"),
            ('ARCHMESH', "Arch", "Arch primitive mesh"),
            ('TETRAHEDRONMESH', "Tetrahedron", "Tetrahedron primitive mesh"),
            ('RECTANGULARPYRAMIDMESH', "Rectangular Pyramid", "Rectangular pyramid primitive mesh"),
            ('LIGHT', "Light", "Light entity"),
            ('AUDIO', "Audio", "Audio entity"),
            ('CHARACTER', "Character", "Character entity"),
            ('CANVAS', "Canvas", "Canvas entity for UI elements"),
            ('TEXT', "Text", "Text entity"),
            ('BUTTON', "Button", "Button entity"),
            ('INPUT', "Input", "Input field entity"),
            ('IMAGE', "Image", "Image entity"),
            ('HTML', "HTML", "HTML entity"),
            ('TERRAIN', "Terrain", "Terrain entity"),
            ('WATER', "Water", "Water entity"),
            ('WATERBLOCKER', "Water Blocker", "Water blocker entity"),
            ('VOXEL', "Voxel", "Voxel entity"),
            ('AUTOMOBILE', "Automobile", "Vehicle entity"),
            ('AIRPLANE', "Airplane", "Airplane entity"),
        ],
        default='AUTO',
    )

    on_load_event: StringProperty(
        name="On Load Event",
        description="Script logic to invoke when entity finishes loading",
        default="",
    )

    # Color settings
    use_custom_color: BoolProperty(
        name="Use Custom Color",
        description="Override material color with custom VEML color",
        default=False,
    )

    color: FloatVectorProperty(
        name="Color",
        description="Color for primitive mesh entities",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    # Mesh-specific properties
    mesh_name: StringProperty(
        name="Mesh Name",
        description="Name for the mesh entity",
        default="",
    )

    # Audio-specific properties
    audio_file: StringProperty(
        name="Audio File",
        description="Path to audio file",
        default="",
        subtype='FILE_PATH',
    )

    audio_autoplay: BoolProperty(
        name="Auto Play",
        description="Automatically play audio when loaded",
        default=True,
    )

    audio_loop: BoolProperty(
        name="Loop",
        description="Loop the audio",
        default=True,
    )

    audio_volume: FloatProperty(
        name="Volume",
        description="Audio volume (0-1)",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    # Text-specific properties
    text_content: StringProperty(
        name="Text Content",
        description="Text content to display",
        default="",
    )

    text_font: StringProperty(
        name="Font",
        description="Font family to use",
        default="",
    )

    text_bold: BoolProperty(
        name="Bold",
        description="Make text bold",
        default=False,
    )

    text_italic: BoolProperty(
        name="Italic",
        description="Make text italic",
        default=False,
    )

    text_underline: BoolProperty(
        name="Underline",
        description="Underline text",
        default=False,
    )

    text_strikethrough: BoolProperty(
        name="Strikethrough",
        description="Strikethrough text",
        default=False,
    )

    text_align_horizontal: EnumProperty(
        name="Horizontal Align",
        description="Horizontal text alignment",
        items=[
            ('NONE', "None", "Default alignment"),
            ('CENTER', "Center", "Center text"),
            ('LEFT', "Left", "Align left"),
            ('RIGHT', "Right", "Align right"),
        ],
        default='NONE',
    )

    text_align_vertical: EnumProperty(
        name="Vertical Align",
        description="Vertical text alignment",
        items=[
            ('NONE', "None", "Default alignment"),
            ('CENTER', "Center", "Center text"),
            ('TOP', "Top", "Align top"),
            ('BOTTOM', "Bottom", "Align bottom"),
        ],
        default='NONE',
    )

    text_wrap: EnumProperty(
        name="Text Wrap",
        description="Text wrapping behavior",
        items=[
            ('NONE', "None", "Default wrapping"),
            ('NO_WRAP', "No Wrap", "Do not wrap text"),
            ('WRAP', "Wrap", "Wrap text"),
        ],
        default='NONE',
    )

    text_font_size: FloatProperty(
        name="Font Size",
        description="Font size",
        default=16.0,
        min=1.0,
    )

    text_color: FloatVectorProperty(
        name="Text Color",
        description="Color for text",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    # Light-specific properties
    light_color: FloatVectorProperty(
        name="Light Color",
        description="Color of the light",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    light_intensity: FloatProperty(
        name="Intensity",
        description="Light intensity/power",
        default=1.0,
        min=0.0,
        soft_max=10.0,
    )

    light_range: FloatProperty(
        name="Range",
        description="Maximum range of the light",
        default=10.0,
        min=0.0,
        soft_max=100.0,
    )

    light_spot_angle: FloatProperty(
        name="Spot Angle",
        description="Spotlight cone angle in degrees",
        default=45.0,
        min=1.0,
        max=180.0,
    )

    light_cast_shadows: BoolProperty(
        name="Cast Shadows",
        description="Whether the light casts shadows",
        default=True,
    )

    light_use_blender_settings: BoolProperty(
        name="Use Blender Settings",
        description="Automatically use light settings from Blender light data",
        default=True,
    )

    # Transform type
    transform_type: EnumProperty(
        name="Transform Type",
        description="Type of transform to use for this entity",
        items=[
            ('SCALE', "Scale Transform", "Use position, rotation, and scale"),
            ('SIZE', "Size Transform", "Use position, rotation, and size in meters"),
        ],
        default='SCALE',
    )

    size_x: FloatProperty(
        name="Size X",
        description="Size in meters (X axis)",
        default=1.0,
        min=0.0,
        soft_max=100.0,
    )

    size_y: FloatProperty(
        name="Size Y",
        description="Size in meters (Y axis)",
        default=1.0,
        min=0.0,
        soft_max=100.0,
    )

    size_z: FloatProperty(
        name="Size Z",
        description="Size in meters (Z axis)",
        default=1.0,
        min=0.0,
        soft_max=100.0,
    )

    # Character-specific properties
    character_mesh_name: StringProperty(
        name="Mesh Name",
        description="Name of the character mesh",
        default="",
    )

    character_mesh_resource: StringProperty(
        name="Mesh Resource",
        description="Path to the character mesh resource file",
        default="",
        subtype='FILE_PATH',
    )

    character_mesh_offset_x: FloatProperty(
        name="X",
        description="Mesh offset X",
        default=0.0,
    )

    character_mesh_offset_y: FloatProperty(
        name="Y",
        description="Mesh offset Y",
        default=0.0,
    )

    character_mesh_offset_z: FloatProperty(
        name="Z",
        description="Mesh offset Z",
        default=0.0,
    )

    character_mesh_rotation_x: FloatProperty(
        name="X",
        description="Mesh rotation X (quaternion)",
        default=0.0,
    )

    character_mesh_rotation_y: FloatProperty(
        name="Y",
        description="Mesh rotation Y (quaternion)",
        default=0.0,
    )

    character_mesh_rotation_z: FloatProperty(
        name="Z",
        description="Mesh rotation Z (quaternion)",
        default=0.0,
    )

    character_mesh_rotation_w: FloatProperty(
        name="W",
        description="Mesh rotation W (quaternion)",
        default=1.0,
    )

    character_label_offset_x: FloatProperty(
        name="X",
        description="Label offset X",
        default=0.0,
    )

    character_label_offset_y: FloatProperty(
        name="Y",
        description="Label offset Y",
        default=2.0,
    )

    character_label_offset_z: FloatProperty(
        name="Z",
        description="Label offset Z",
        default=0.0,
    )

    # Synchronizer
    synchronizer: StringProperty(
        name="Synchronizer",
        description="Synchronizer identifier for this entity (for multiplayer sync)",
        default="",
    )

    # Canvas transform properties
    use_canvas_transform: BoolProperty(
        name="Use Canvas Transform",
        description="Use canvas transform (position-percent and size-percent) instead of world transform",
        default=False,
    )

    canvas_position_x: FloatProperty(
        name="X",
        description="Position X as percentage (0-1) from left",
        default=0.0,
        min=0.0,
        max=1.0,
    )

    canvas_position_y: FloatProperty(
        name="Y",
        description="Position Y as percentage (0-1) from top",
        default=0.0,
        min=0.0,
        max=1.0,
    )

    canvas_size_x: FloatProperty(
        name="X",
        description="Size X as percentage (0-1) of parent width",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    canvas_size_y: FloatProperty(
        name="Y",
        description="Size Y as percentage (0-1) of parent height",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    canvas_align_horizontal: EnumProperty(
        name="Horizontal Align",
        description="Horizontal alignment within parent",
        items=[
            ('NONE', "None", "No alignment"),
            ('CENTER', "Center", "Center horizontally"),
            ('LEFT', "Left", "Align to left"),
            ('RIGHT', "Right", "Align to right"),
        ],
        default='NONE',
    )

    canvas_align_vertical: EnumProperty(
        name="Vertical Align",
        description="Vertical alignment within parent",
        items=[
            ('NONE', "None", "No alignment"),
            ('CENTER', "Center", "Center vertically"),
            ('TOP', "Top", "Align to top"),
            ('BOTTOM', "Bottom", "Align to bottom"),
        ],
        default='NONE',
    )

    canvas_stretch_to_parent: BoolProperty(
        name="Stretch to Parent",
        description="Stretch this entity to fit its parent",
        default=False,
    )

    # Button properties
    button_on_click: StringProperty(
        name="On Click Event",
        description="Script logic to invoke when button is clicked",
        default="",
    )

    button_color: FloatVectorProperty(
        name="Button Color",
        description="Color for the button",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.3, 0.3, 0.3, 1.0),
    )

    # Image properties
    image_file: StringProperty(
        name="Image File",
        description="Path to the image file",
        default="",
        subtype='FILE_PATH',
    )

    # HTML properties
    html_url: StringProperty(
        name="URL",
        description="URL to load in the HTML entity",
        default="",
    )

    html_on_message: StringProperty(
        name="On Message",
        description="Script logic to invoke when a message is received",
        default="",
    )

    # Terrain properties
    terrain_length: FloatProperty(
        name="Length",
        description="Length of the terrain in meters",
        default=100.0,
        min=1.0,
    )

    terrain_width: FloatProperty(
        name="Width",
        description="Width of the terrain in meters",
        default=100.0,
        min=1.0,
    )

    terrain_height: FloatProperty(
        name="Height",
        description="Maximum height of the terrain in meters",
        default=50.0,
        min=0.1,
    )

    terrain_type: EnumProperty(
        name="Terrain Type",
        description="Type of terrain",
        items=[
            ('HEIGHTMAP', "Heightmap", "Heightmap-based terrain"),
            ('VOXEL', "Voxel", "Voxel-based terrain"),
            ('HYBRID', "Hybrid", "Hybrid terrain"),
        ],
        default='HEIGHTMAP',
    )

    terrain_heights: StringProperty(
        name="Heights",
        description="Comma-separated 2D array of heights (e.g., 0,1,2;3,2,1)",
        default="",
    )

    terrain_layer_masks: StringProperty(
        name="Layer Masks",
        description="Layer mask values separated by | for each layer",
        default="",
    )

    # Water properties
    water_shallow_color: FloatVectorProperty(
        name="Shallow Color",
        description="Color for shallow water",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.8, 0.9, 0.8),
    )

    water_deep_color: FloatVectorProperty(
        name="Deep Color",
        description="Color for deep water",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.2, 0.4, 1.0),
    )

    water_specular_color: FloatVectorProperty(
        name="Specular Color",
        description="Specular reflection color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    water_scattering_color: FloatVectorProperty(
        name="Scattering Color",
        description="Light scattering color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.4, 0.4, 1.0),
    )

    water_deep_start: FloatProperty(
        name="Deep Start",
        description="Depth where deep color starts",
        default=1.0,
        min=0.0,
    )

    water_deep_end: FloatProperty(
        name="Deep End",
        description="Depth where deep color is full",
        default=10.0,
        min=0.0,
    )

    water_distortion: FloatProperty(
        name="Distortion",
        description="Water distortion factor (0-128)",
        default=0.5,
        min=0.0,
        max=128.0,
    )

    water_smoothness: FloatProperty(
        name="Smoothness",
        description="Water surface smoothness (0-1)",
        default=0.9,
        min=0.0,
        max=1.0,
    )

    water_num_waves: IntProperty(
        name="Number of Waves",
        description="Number of waves (1-32)",
        default=4,
        min=1,
        max=32,
    )

    water_wave_amplitude: FloatProperty(
        name="Wave Amplitude",
        description="Height of waves (0-1)",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    water_wave_steepness: FloatProperty(
        name="Wave Steepness",
        description="Steepness of waves (0-1)",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    water_wave_speed: FloatProperty(
        name="Wave Speed",
        description="Speed of wave movement",
        default=1.0,
        min=0.0,
    )

    water_wave_length: FloatProperty(
        name="Wave Length",
        description="Length of waves",
        default=10.0,
        min=0.1,
    )

    water_wave_scale: FloatProperty(
        name="Wave Scale",
        description="Scale of wave pattern",
        default=1.0,
        min=0.0,
    )

    water_wave_intensity: FloatProperty(
        name="Wave Intensity",
        description="Overall wave intensity",
        default=1.0,
        min=0.0,
    )

    # Automobile properties
    automobile_mesh_name: StringProperty(
        name="Mesh Name",
        description="Name of the automobile mesh",
        default="",
    )

    automobile_mesh_resource: StringProperty(
        name="Mesh Resource",
        description="Path to the automobile mesh file",
        default="",
        subtype='FILE_PATH',
    )

    automobile_mass: FloatProperty(
        name="Mass",
        description="Mass of the automobile in kg",
        default=1500.0,
        min=1.0,
    )

    automobile_type: StringProperty(
        name="Automobile Type",
        description="Type of automobile (e.g., car, truck, motorcycle)",
        default="car",
    )

    automobile_wheels: StringProperty(
        name="Wheels",
        description="Wheel definitions (submesh:radius pairs, comma-separated)",
        default="",
    )

    # Airplane properties
    airplane_mesh_name: StringProperty(
        name="Mesh Name",
        description="Name of the airplane mesh",
        default="",
    )

    airplane_mesh_resource: StringProperty(
        name="Mesh Resource",
        description="Path to the airplane mesh file",
        default="",
        subtype='FILE_PATH',
    )

    airplane_mass: FloatProperty(
        name="Mass",
        description="Mass of the airplane in kg",
        default=5000.0,
        min=1.0,
    )

    # Placement sockets
    placement_sockets: CollectionProperty(
        type=VEMLPlacementSocket,
        name="Placement Sockets",
        description="Sockets for connecting entities",
    )

    placement_sockets_index: IntProperty(
        name="Active Socket Index",
        default=0,
    )

    # -- Entry point (#115) ------------------------------------------------
    # Get/set-backed: the checkbox READS AND WRITES the raw `veml_spawn`
    # custom property on the camera OBJECT (the format contract veml-ingest
    # honors, #99) and stores NOTHING of its own — a scene marked here is
    # structurally identical to one marked by hand. Rules (exclusive move,
    # key removed on disable, no leakage on read) live bpy-free in
    # entry_point.py, pinned by tools/entry_point_logic_check.py.
    def _get_is_entry_point(self):
        return entry_point.get_entry_point(self.id_data)

    def _set_is_entry_point(self, value):
        entry_point.set_entry_point(bpy.data.objects, self.id_data, bool(value))

    is_entry_point: BoolProperty(
        name="VEML Entry Point",
        description=(
            "This camera is the world's entry point: the exporter uses its "
            "pose over the active scene camera (precedence: --entry > this > "
            "active camera > bounds framing). Writes the veml_spawn custom "
            "property; checking another camera moves it there"
        ),
        get=_get_is_entry_point,
        set=_set_is_entry_point,
    )
