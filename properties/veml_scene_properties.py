# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy
from . import site_defaults
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
        description=(
            "Type of synchronization service. worldsync is the serverless "
            "protocol the shell speaks (#257); vss is the legacy server path "
            "the direct exporter still writes"
        ),
        # Was "vss". New scenes default to what the shell now implements;
        # a .blend that stored "vss" keeps it (stored values win).
        default="worldsync",
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

    # Save as My World (#119)
    deploy_dir: StringProperty(
        name="Deploy Directory",
        description="Serving location veml-ingest --deploy updates atomically",
        default="",
        subtype='DIR_PATH',
    )

    deploy_title: StringProperty(
        name="Deploy Title",
        description="World title passed to veml-ingest --title (default: the file stem, matching ingest)",
        default="",
    )

    no_lookdev_sky: BoolProperty(
        name="Ignore Viewport Sky",
        description=(
            "Do not ship Blender's Material Preview environment as this world's "
            "sky. That HDRI (forest.exr unless you changed it) is never saved in "
            "the .blend. Ticked by default: the world gets the sky you set in the "
            "scene's World, not the preview. Untick to ship the preview HDRI, which "
            "is what your glass and metal reflect while you work"
        ),
        # Founder, 2026-09-24 (#375): ignore it unless asked.
        default=True,
    )

    # Publishing (#257 story 3) — the button uploads the deployed folder and
    # hands back a link. The endpoint is per-scene rather than a preference
    # because a .blend may well belong to a different service than the last
    # one did; the token is NOT here, it is a credential (addon preferences).
    publish_endpoint: StringProperty(
        name="Publish To",
        description=(
            "Publish service the world is uploaded to, e.g. https://worlds.example. "
            "Leave empty to write the world locally and go no further"
        ),
        # A packaged build can arrive pointing somewhere, so a first press
        # needs nothing typed (#308). An unpackaged one is empty, which is
        # the self-hosting default. See properties/site_defaults.py.
        default=site_defaults.default_publish_endpoint(),
    )

    open_after_publish: BoolProperty(
        name="Open When Published",
        description=(
            "Open the world in the viewer as soon as it publishes, instead of "
            "leaving the address in the status bar to copy. Untick to just get "
            "the link"
        ),
        # On, because "press the button and be in your world" is the point
        # (#308). Nothing opens for a local deploy - there is no address -
        # and nothing opens when no viewer is configured.
        default=True,
    )

    world_url: StringProperty(
        name="World Address",
        description=(
            "Where this world is served. A successful publish fills this in; "
            "for a local deploy, paste the address your server exposes the "
            "world's index.veml at. The Open in Browser button opens it in "
            "the viewer"
        ),
        default="",
    )

    publish_world_id: StringProperty(
        name="World ID",
        description=(
            "Filled in by the first publish. Kept so the next press updates THIS world "
            "at the same address instead of creating a new one. Shown read-only because it is "
            "the service's id; use Publish as New World (the X beside it) to stop updating it"
        ),
        default="",
    )
