# How the add-on is laid out

The add-on does two jobs. It reads a Blender scene and writes a VEML 4.0
document, and it drives a bundled world builder that turns the scene into a
publishable world folder. The first is pure Python in this tree; the second
shells out.

## The one rule worth knowing before you change anything

**Modules that construct commands, parse results or decide rules are kept free
of `bpy`.** `properties/deploy_command.py`, `properties/sign_in_flow.py`,
`properties/entry_point.py`, `exporters/veml40_writer.py` and
`utils/node_runtime.py` import no Blender API at all.

That is not tidiness. It means those rules can be exercised by plain Python
with no Blender installed, which is how the argv the button builds, the
document the exporter writes and the runtime fetch are all tested. If you
reach for `bpy` inside one of them, you have moved a rule out of reach of its
test — pass the value in instead.

## The tree

```
veml_exporter/
├── __init__.py        registration, and the menu entries
├── operators/         everything a press does
├── panels/            what you see: VEML in Scene and Object properties
├── properties/        the stored fields, and the bpy-free rules above
├── exporters/         scene -> VEML 4.0 document, and glb export
├── importers/         a VEML document back into Blender
├── utils/             transforms, colour, the Node runtime fetch
└── ingest/            the bundled world builder — NOT in the source tree
```

`ingest/` exists only inside a built zip. It is the world builder, bundled
from its own package, plus the schemas it validates against. The add-on finds
it next to itself and runs it with Node; that is the whole integration.

## Operators, and which one is the button

| Module | What it is |
|---|---|
| `save_as_my_world.py` | **the button.** Saves, builds the world, publishes if configured, and can open it |
| `publish_as_new_world.py` | publish again as a separate world rather than replacing |
| `open_my_world.py` | open the published world in a browser |
| `sign_in.py` | the sign-in press; the flow itself is `properties/sign_in_flow.py` |
| `get_node.py` | fetch the Node runtime, verified, when the machine has none |
| `export_veml.py` / `import_veml.py` | File > Export / Import, document only |
| `socket_operators.py` | placement sockets on an object |

## Writing the document

`exporters/veml_exporter.py` collects scene data with `bpy` and hands every
byte of XML to `exporters/veml40_writer.py`, which is bpy-free. Entities come
from `entity_exporter.py`; geometry leaves through `mesh_exporter.py` as glb.

Keep that split when adding anything. Collect in the exporter, serialise in
the writer.

## Sign-in, in one paragraph

The add-on is an OAuth 2.1 public client that names no identity service and
hardcodes no host: the authorize and token addresses, the client id and the
loopback ports are preferences, empty in a source build. A press mints a PKCE
verifier and a state, listens on `127.0.0.1:<port>/callback` (the first free
listed port, or any free one when none are listed), and opens the authorize
address in a browser, where the person signs in by any method the provider
offers. A timer picks up the single-use code that comes back with the same
state and redeems it outbound for a token. A code crosses the loopback, never
a token — a code is worthless without the verifier, which never leaves the
add-on. Ports are listed because many providers match redirect URIs exactly.

## Adding a property the panel draws

Add it to the relevant group in `properties/`, then draw it in the panel. The
installed-add-on check asserts that every `prop(veml, "…")` a panel draws
exists on the installed property group, so a panel that draws a field nobody
defined fails before a person ever sees the error.
