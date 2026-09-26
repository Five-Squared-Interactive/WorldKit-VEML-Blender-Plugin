# VEML Exporter for Blender

A Blender addon for exporting scenes to VEML (Virtual Environment Markup Language) format.

![Blender](https://img.shields.io/badge/Blender-3.0%2B-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Full VEML 3.0 Support** - Export all entity types defined in the VEML schema
- **Automatic Entity Detection** - Primitives, meshes, lights, and more auto-detected
- **GLB/GLTF Export** - Custom meshes automatically exported as GLB files
- **UI Integration** - Properties panels for scene and object settings
- **Coordinate Conversion** - Automatic Z-up to Y-up transformation
- **Hierarchical Export** - Parent-child relationships preserved

## Quick Start

### Install

1. Download `veml-blender-addon.zip` from this repository's
   [latest release](https://github.com/Five-Squared-Interactive/WorldKit-VEML-Blender-Plugin/releases/latest).
   Use the release, not a zip of this folder: the release also carries the
   VEML ingest (the world pipeline the add-on runs), which is built with it
   and is not part of this source tree.
2. In Blender: **Edit → Preferences → Add-ons → Install from Disk**, pick the
   zip, and tick it on.
3. Install [Node.js](https://nodejs.org) if you do not have it. The add-on
   carries the whole world pipeline; Node is the one thing it cannot ship
   (the runtime is per-platform and needs code signing). The panel says so
   plainly when it is missing, and finds it by itself when it is not.

That is the configuration. No path to paste, no CLI to install separately.

### Build a world

1. Open your scene and save the .blend.
2. **View3D > sidebar > VEML > Save as My World**.
3. The report names the folder it wrote and where a visitor arrives, e.g.
   `Deployed to C:\worlds\lobby (entry point: veml_spawn camera "Arrival")`.

Fill **Publish To** with a publish service and the same press uploads it and
hands you a link instead — and **Open in Browser** lights up.

Publishing needs you signed in. If you are not — or your sign-in has run out —
the panel says so under the button and offers **Sign In** right there; pressing
**Save as My World** in that state opens the sign-in in your browser and
publishes on its own once you are back. A sign-in lasts: the add-on renews the
token quietly before each publish, so you sign in once, not every hour.
**Sign Out** is in the add-on preferences, beside Sign In; it forgets both tokens.

### Export a single .veml (the older, narrower path)

1. Create your scene in Blender
2. Go to **File → Export → VEML (.veml)**
3. Configure options and export

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and extension guide
- **[VEML Reference](docs/VEML_REFERENCE.md)** - Format quick reference

## Supported Entity Types

| Category | Types |
|----------|-------|
| **Primitives** | cube, sphere, cylinder, cone, plane, torus, capsule, prism, arch, tetrahedron, pyramid |
| **Complex** | mesh, light, audio, character, terrain, water, automobile, airplane, voxel |
| **UI** | canvas, text, button, input, image, html |
| **Utility** | container, waterblocker |

## Project Structure

```
veml_exporter/
├── operators/      # Export and UI operators
├── panels/         # Blender UI panels
├── properties/     # Custom property definitions
├── exporters/      # XML and mesh export logic
└── utils/          # Color and transform utilities
```

## Requirements

- Blender 3.0 or later
- Python 3.9+ (included with Blender)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the [Developer Guide](docs/DEVELOPER_GUIDE.md) before submitting PRs.
