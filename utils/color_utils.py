# Copyright (c) 2019-2025 Five Squared Interactive. All rights reserved.
#
# SPDX-License-Identifier: MIT

import bpy


def blender_to_veml_color(color) -> str:
    """
    Convert a Blender color (tuple/list of 3-4 floats 0-1) to VEML hex format.
    Returns format: #rrggbbaa
    """
    if len(color) == 3:
        r, g, b = color
        a = 1.0
    else:
        r, g, b, a = color

    # Convert to 0-255 range
    r_int = int(round(r * 255))
    g_int = int(round(g * 255))
    b_int = int(round(b * 255))
    a_int = int(round(a * 255))

    # Clamp values
    r_int = max(0, min(255, r_int))
    g_int = max(0, min(255, g_int))
    b_int = max(0, min(255, b_int))
    a_int = max(0, min(255, a_int))

    return f"#{r_int:02x}{g_int:02x}{b_int:02x}{a_int:02x}"


def veml_to_blender_color(veml_color: str) -> tuple:
    """
    Convert a VEML color string to Blender format.
    Supports:
    - Hex format: #rgb, #rrggbb, #rrggbbaa
    - color() format: color(r g b a) or color(r, g, b, a)
    - Named colors (basic support)
    """
    veml_color = veml_color.strip()

    if veml_color.startswith('#'):
        return _parse_hex_color(veml_color)
    elif veml_color.startswith('color('):
        return _parse_color_function(veml_color)
    else:
        return _parse_named_color(veml_color)


def _parse_hex_color(hex_str: str) -> tuple:
    """Parse hex color string to Blender RGBA tuple"""
    hex_str = hex_str.lstrip('#')

    if len(hex_str) == 3:
        # #rgb -> #rrggbb
        r = int(hex_str[0] * 2, 16) / 255.0
        g = int(hex_str[1] * 2, 16) / 255.0
        b = int(hex_str[2] * 2, 16) / 255.0
        return (r, g, b, 1.0)

    elif len(hex_str) == 6:
        # #rrggbb
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b, 1.0)

    elif len(hex_str) == 8:
        # #rrggbbaa
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        a = int(hex_str[6:8], 16) / 255.0
        return (r, g, b, a)

    return (1.0, 1.0, 1.0, 1.0)


def _parse_color_function(color_str: str) -> tuple:
    """Parse color() function format"""
    # Extract content between parentheses
    content = color_str[6:-1].strip()

    # Handle both space and comma separators
    if ',' in content:
        parts = [p.strip() for p in content.split(',')]
    else:
        parts = content.split()

    try:
        values = [float(p) for p in parts]
        if len(values) == 3:
            values.append(1.0)

        # Normalize if values are in 0-255 range
        if any(v > 1.0 for v in values[:3]):
            values = [v / 255.0 for v in values]

        return tuple(values[:4])
    except ValueError:
        return (1.0, 1.0, 1.0, 1.0)


def _parse_named_color(name: str) -> tuple:
    """Parse named color to Blender format"""
    named_colors = {
        'white': (1.0, 1.0, 1.0, 1.0),
        'black': (0.0, 0.0, 0.0, 1.0),
        'red': (1.0, 0.0, 0.0, 1.0),
        'green': (0.0, 1.0, 0.0, 1.0),
        'blue': (0.0, 0.0, 1.0, 1.0),
        'yellow': (1.0, 1.0, 0.0, 1.0),
        'cyan': (0.0, 1.0, 1.0, 1.0),
        'magenta': (1.0, 0.0, 1.0, 1.0),
        'gray': (0.5, 0.5, 0.5, 1.0),
        'grey': (0.5, 0.5, 0.5, 1.0),
        'orange': (1.0, 0.5, 0.0, 1.0),
        'purple': (0.5, 0.0, 0.5, 1.0),
        'pink': (1.0, 0.75, 0.8, 1.0),
        'brown': (0.6, 0.3, 0.0, 1.0),
    }

    return named_colors.get(name.lower(), (1.0, 1.0, 1.0, 1.0))


def get_object_color(obj) -> str:
    """
    Get the color of an object from its material.
    Returns VEML hex color string.
    """
    # Default color
    default_color = (0.8, 0.8, 0.8, 1.0)

    if obj.type != 'MESH' or not obj.data.materials:
        return blender_to_veml_color(default_color)

    # Get first material
    material = obj.data.materials[0]
    if material is None:
        return blender_to_veml_color(default_color)

    # Try to get color from material
    if material.use_nodes:
        # Look for Principled BSDF node
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                base_color = node.inputs['Base Color'].default_value
                return blender_to_veml_color(base_color[:4])

        # Fallback: look for any diffuse-like input
        for node in material.node_tree.nodes:
            if hasattr(node, 'inputs'):
                for inp in node.inputs:
                    if 'color' in inp.name.lower() and hasattr(inp, 'default_value'):
                        try:
                            color = inp.default_value[:4]
                            return blender_to_veml_color(color)
                        except (TypeError, IndexError):
                            continue

    # Use diffuse color if available
    if hasattr(material, 'diffuse_color'):
        return blender_to_veml_color(material.diffuse_color[:4])

    return blender_to_veml_color(default_color)
