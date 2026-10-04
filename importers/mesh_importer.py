# Copyright (c) 2019-2026 Five Squared Interactive
# SPDX-License-Identifier: MIT

#

import os

import bpy


class MeshImporter:
    """Imports external mesh files (GLB/GLTF) for VEML mesh entities"""

    def __init__(self, import_dir):
        self.import_dir = import_dir
        self.imported_meshes = {}  # Cache to avoid re-importing same mesh

    def import_mesh(self, resource_path) -> bpy.types.Object:
        """
        Import a mesh from GLB/GLTF format.
        Returns the imported object, or None if import failed.
        """
        # Check if already imported
        if resource_path in self.imported_meshes:
            # Duplicate the cached object
            original = self.imported_meshes[resource_path]
            if original is not None:
                new_obj = original.copy()
                new_obj.data = original.data.copy()
                bpy.context.collection.objects.link(new_obj)
                return new_obj
            return None

        # Build full path
        if os.path.isabs(resource_path):
            filepath = resource_path
        else:
            filepath = os.path.join(self.import_dir, resource_path)

        # Normalize path
        filepath = os.path.normpath(filepath)

        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Mesh file not found: {filepath}")
            self.imported_meshes[resource_path] = None
            return None

        # Store current selection
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.view_layer.objects.active

        try:
            # Deselect all
            bpy.ops.object.select_all(action='DESELECT')

            # Import based on file extension
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == '.glb':
                bpy.ops.import_scene.gltf(filepath=filepath)
            elif ext == '.gltf':
                bpy.ops.import_scene.gltf(filepath=filepath)
            elif ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=filepath)
            elif ext == '.obj':
                bpy.ops.import_scene.obj(filepath=filepath)
            else:
                print(f"Unsupported mesh format: {ext}")
                self.imported_meshes[resource_path] = None
                return None

            # Get the imported objects
            imported_objects = bpy.context.selected_objects

            if not imported_objects:
                print(f"No objects imported from: {filepath}")
                self.imported_meshes[resource_path] = None
                return None

            # Find the main mesh object (prefer mesh over armature/empty)
            main_obj = None
            for obj in imported_objects:
                if obj.type == 'MESH':
                    main_obj = obj
                    break

            # If no mesh found, use the first object
            if main_obj is None:
                main_obj = imported_objects[0]

            # If multiple objects were imported, join them into one
            if len(imported_objects) > 1:
                # Find all mesh objects
                mesh_objects = [obj for obj in imported_objects if obj.type == 'MESH']
                
                if len(mesh_objects) > 1:
                    # Select all mesh objects
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in mesh_objects:
                        obj.select_set(True)
                    bpy.context.view_layer.objects.active = mesh_objects[0]
                    
                    # Join them
                    bpy.ops.object.join()
                    main_obj = bpy.context.active_object

                # Delete non-mesh objects (armatures, empties from import)
                for obj in imported_objects:
                    if obj != main_obj and obj.type not in ('MESH',):
                        try:
                            bpy.data.objects.remove(obj, do_unlink=True)
                        except:
                            pass

            # Cache the imported object
            self.imported_meshes[resource_path] = main_obj

            return main_obj

        except Exception as e:
            print(f"Failed to import mesh {filepath}: {e}")
            self.imported_meshes[resource_path] = None
            return None

        finally:
            # Restore selection (best effort)
            try:
                bpy.ops.object.select_all(action='DESELECT')
                for sel_obj in original_selection:
                    if sel_obj.name in bpy.data.objects:
                        sel_obj.select_set(True)
                if original_active and original_active.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = original_active
            except:
                pass

    def clear_cache(self):
        """Clear the imported mesh cache"""
        self.imported_meshes.clear()
