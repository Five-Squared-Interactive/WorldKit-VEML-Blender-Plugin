# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT
#
# Which sky "Ignore Viewport Sky" is about — deliberately bpy-free.
#
# Blender's Material Preview lights the viewport with a studio HDRI that is
# saved nowhere in the .blend. The exporter carries it as the world's sky
# unless the checkbox says not to, so the checkbox should name the file it
# is about: "forest.exr" means something to the person; "lookdev" does not.
# The rule here mirrors the exporter's own reading of a screen (the active
# screen's 3D viewports, Material Preview, not the scene's world), so the
# panel names the file the exporter would ship. tools/lookdev_sky_check.py
# pins it without a Blender install.


def viewport_sky_name(screen):
    """The studio HDRI a 3D viewport on `screen` is lit by, or None.

    None when no 3D viewport is in Material Preview, when the one that is
    uses the scene's own World (`use_scene_world`), or when it names no
    studio light. With several, the last one found decides, as the exporter
    has it.
    """
    if screen is None:
        return None
    found = None
    for area in getattr(screen, "areas", ()):
        if getattr(area, "type", None) != "VIEW_3D":
            continue
        for space in getattr(area, "spaces", ()):
            shading = getattr(space, "shading", None)
            if shading is None or getattr(shading, "type", None) != "MATERIAL":
                continue
            if getattr(shading, "use_scene_world", False):
                continue
            name = getattr(shading, "studio_light", None)
            if name:
                found = name
    return found


def checkbox_text(name):
    """The checkbox's label: the file it is about, when there is one."""
    return f"Ignore Viewport Sky ({name})" if name else "Ignore Viewport Sky"
