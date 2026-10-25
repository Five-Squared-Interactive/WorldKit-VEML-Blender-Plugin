# VEML Exporter for Blender

Build a room in Blender, press one button, get a link other people can walk
into. The add-on turns your scene into a world — a VEML 4.0 document plus
glTF assets — and can publish it to an address a visitor opens in a browser
with no install and no account.

![Blender](https://img.shields.io/badge/Blender-4.5%2B-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **One button** - save the scene, build the world, upload it, open it
- **VEML 4.0** - the document a world is, written against the published schema
  and validated before it ships
- **glTF assets, content-hashed** - meshes exported as glb, named by their
  hash so a cache can hold them forever
- **Materials and lights carried** - the Principled surface, Blender's lamps
  as `KHR_lights_punctual`, and the viewport environment as the world's sky
- **An entry point you choose** - mark a camera and visitors arrive there
  facing the way it faces
- **Nothing to configure** - the add-on carries the whole pipeline; it finds
  Node.js if you have it and offers to fetch it if you do not
- **Z-up to Y-up, hierarchy preserved** - the conversion a glTF consumer
  expects, with parent-child relationships intact

## Quick Start

### Install

1. Download `veml-blender-addon.zip` from the
   [latest release](https://github.com/Five-Squared-Interactive/WorldKit-VEML-Blender-Plugin/releases/latest).
2. In Blender: **Edit → Preferences → Add-ons → Install from Disk**, pick the
   zip, and tick it on.
3. Nothing. The add-on carries the whole world pipeline, and needs a Node.js
   runtime to run it with. If one is already on your machine it is found by
   itself. If not, the panel says so and offers **Get Node.js**, which fetches
   the official build from nodejs.org, checks it against a published
   checksum, and keeps it beside Blender's own user data. One press, no
   restart.

   The runtime is not shipped inside the zip because it is per-platform and
   would need signing; fetching it on a press keeps the download to the people
   who actually need it. Nothing is ever downloaded unless you press that
   button. On a platform with no official build the panel says that instead,
   and you install Node yourself.

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

**Who can open it.** A published world is open to anyone with its address
unless you tick **Only People I Allow**. Then fill **Allowed Viewers** with
their email addresses (commas or spaces between them). The world's address
does not change and is not listed; a visitor who opens it is asked to sign
in, with the same account kind you publish with, and the service lets them
in if they are on your list or turns them away if they are not. You can
always open your own world. The list is kept on the service: re-publishing
keeps it, and unticking the box opens the world to everyone without
forgetting who was on it, so ticking it again restores them. The box states
your choice every time you press the button, so the box is the truth.
**Sign Out** is in the add-on preferences, beside Sign In; it forgets both tokens.

### Export a single .veml (the older, narrower path)

1. Create your scene in Blender
2. Go to **File → Export → VEML (.veml)**
3. Configure options and export

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions
- **[Architecture](docs/ARCHITECTURE.md)** - how the add-on is laid out, and the one rule worth knowing before changing it
- **[VEML](docs/VEML.md)** - the format this writes, and where it is specified

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
├── operators/      # the button, sign-in, open-in-browser, import/export
├── panels/         # the VEML panels in the scene and object properties
├── properties/     # scene/object properties, and the command the button runs
├── exporters/      # scene -> VEML 4.0 document, and glb export
├── importers/      # reading a VEML document back into Blender
├── utils/          # transforms, colour, and the Node runtime fetch
└── ingest/         # the bundled world builder (not in the source tree)
```

## Requirements

- Blender 4.5 or later. Tested on 4.5 LTS and 5.2; the add-on uses Blender
  4-era shader socket names, so 3.x will not work.
- A Node.js runtime, which the add-on will fetch for you on a press if you do
  not have one. Nothing else.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome. [ARCHITECTURE.md](docs/ARCHITECTURE.md) describes how
the add-on is laid out. The format itself is specified separately — see
[the VEML 4.0 spec](docs/VEML.md).
