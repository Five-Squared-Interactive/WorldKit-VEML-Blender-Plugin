# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
)


class VEMLSceneProperties(bpy.types.PropertyGroup):
    """VEML-specific properties for the scene/world"""

    # Metadata
    title: StringProperty(
        name="Title",
        description="Title for the VEML world",
        default="Untitled World",
    )

    scripts: StringProperty(
        name="Scripts",
        description="Comma-separated list of script files to include",
        default="",
    )

    # Background
    background_type: EnumProperty(
        name="Background Type",
        description="Type of background for the world",
        items=[
            ('COLOR', "Color", "Solid color background"),
            ('PANORAMA', "Panorama", "Panoramic image background"),
            ('PROCEDURAL', "Procedural Sky", "Lite procedural sky"),
        ],
        default='COLOR',
    )

    background_color: FloatVectorProperty(
        name="Background Color",
        description="Background color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5, 0.7, 1.0, 1.0),
    )

    background_panorama: StringProperty(
        name="Panorama",
        description="Path to panorama image file",
        default="",
        subtype='FILE_PATH',
    )

    # Procedural sky settings
    procedural_day_night_cycle: BoolProperty(
        name="Day/Night Cycle",
        description="Enable day/night cycle",
        default=True,
    )

    procedural_sun_enabled: BoolProperty(
        name="Sun Enabled",
        description="Enable procedural sun",
        default=True,
    )

    procedural_moon_enabled: BoolProperty(
        name="Moon Enabled",
        description="Enable procedural moon",
        default=True,
    )

    procedural_stars_enabled: BoolProperty(
        name="Stars Enabled",
        description="Enable stars",
        default=True,
    )

    procedural_clouds_enabled: BoolProperty(
        name="Clouds Enabled",
        description="Enable procedural clouds",
        default=True,
    )

    # Effects - Fog
    fog_enabled: BoolProperty(
        name="Fog Enabled",
        description="Enable lite fog effect",
        default=False,
    )

    fog_color: FloatVectorProperty(
        name="Fog Color",
        description="Color of the fog",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5, 0.5, 0.5, 1.0),
    )

    fog_density: FloatProperty(
        name="Fog Density",
        description="Density of the fog",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    # Synchronization Service
    sync_enabled: BoolProperty(
        name="Enable Synchronization",
        description="Enable synchronization service for multiplayer",
        default=False,
    )

    sync_type: StringProperty(
        name="Type",
        description="Type of synchronization service (e.g., vss)",
        default="vss",
    )

    sync_address: StringProperty(
        name="Address",
        description="Address of the synchronization service",
        default="",
    )

    sync_id: StringProperty(
        name="Session ID",
        description="UUID-encoded session identifier",
        default="",
    )

    sync_session: StringProperty(
        name="Session Name",
        description="Human-readable name for the session",
        default="",
    )
