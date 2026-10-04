# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

import math

import bpy
from mathutils import Quaternion, Vector


def get_transform_elements(obj) -> tuple:
    """
    Get position, rotation (quaternion), and scale from a Blender object.
    Converts from Blender's Z-up coordinate system to Y-up (common in game engines).
    
    Returns:
        tuple: (position, rotation, scale) where:
            - position is (x, y, z)
            - rotation is (x, y, z, w) quaternion
            - scale is (x, y, z)
    """
    # Get local transform (relative to parent)
    if obj.parent:
        # Use local matrix for parented objects
        matrix = obj.matrix_local
    else:
        # Use world matrix for root objects
        matrix = obj.matrix_world

    # Decompose matrix
    loc, rot, scale = matrix.decompose()

    # Convert coordinate system: Blender Z-up to Y-up
    # Blender: X-right, Y-forward, Z-up
    # Target:  X-right, Y-up, Z-forward (common in game engines)
    position = convert_position_to_yup(loc)
    rotation = convert_rotation_to_yup(rot)
    scale_converted = convert_scale_to_yup(scale)

    return position, rotation, scale_converted


def convert_position_to_yup(pos: Vector) -> tuple:
    """
    Convert position from Blender Z-up to Y-up coordinate system.
    Blender (x, y, z) -> Target (x, z, -y)
    """
    return (pos.x, pos.z, -pos.y)


def convert_rotation_to_yup(rot: Quaternion) -> tuple:
    """
    Convert quaternion rotation from Blender Z-up to Y-up coordinate system.
    Returns (x, y, z, w) format for VEML.
    """
    # Create rotation that converts from Z-up to Y-up
    # This is a -90 degree rotation around the X axis
    conversion_rot = Quaternion((1, 0, 0), math.radians(-90))

    # Apply conversion
    converted = conversion_rot @ rot

    # VEML uses (x, y, z, w) format
    return (converted.x, converted.y, converted.z, converted.w)


def convert_scale_to_yup(scale: Vector) -> tuple:
    """
    Convert scale from Blender Z-up to Y-up coordinate system.
    Scale axes need to be swapped to match position conversion.
    """
    return (scale.x, scale.z, scale.y)


def convert_position_from_yup(pos: tuple) -> Vector:
    """
    Convert position from Y-up to Blender Z-up coordinate system.
    Target (x, y, z) -> Blender (x, -z, y)
    """
    return Vector((pos[0], -pos[2], pos[1]))


def convert_rotation_from_yup(rot: tuple) -> Quaternion:
    """
    Convert quaternion from Y-up to Blender Z-up coordinate system.
    Input is (x, y, z, w) format from VEML.
    """
    # Create quaternion from VEML format
    quat = Quaternion((rot[3], rot[0], rot[1], rot[2]))  # w, x, y, z

    # Create inverse conversion rotation (+90 degrees around X)
    conversion_rot = Quaternion((1, 0, 0), math.radians(90))

    # Apply inverse conversion
    return conversion_rot @ quat


def euler_to_quaternion(euler_deg: tuple) -> tuple:
    """
    Convert Euler angles (degrees) to quaternion.
    Returns (x, y, z, w) format.
    """
    from mathutils import Euler
    euler = Euler((
        math.radians(euler_deg[0]),
        math.radians(euler_deg[1]),
        math.radians(euler_deg[2])
    ), 'XYZ')
    quat = euler.to_quaternion()
    return (quat.x, quat.y, quat.z, quat.w)


def quaternion_to_euler(quat: tuple) -> tuple:
    """
    Convert quaternion (x, y, z, w) to Euler angles (degrees).
    """
    q = Quaternion((quat[3], quat[0], quat[1], quat[2]))  # w, x, y, z
    euler = q.to_euler('XYZ')
    return (
        math.degrees(euler.x),
        math.degrees(euler.y),
        math.degrees(euler.z)
    )
