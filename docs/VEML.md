# VEML, the format this add-on writes

This add-on writes **VEML 4.0**. The format is specified elsewhere, on
purpose: a world is a document meant to outlive any one tool that makes it,
and a parallel reference kept beside an exporter drifts from the thing it
describes.

- **The schema** — `veml-4.0.xsd`. The add-on carries a verified copy and
  validates every document it emits against it before the world ships. A
  document that does not validate is not written, so the copy inside the
  installed add-on is the one your worlds were actually checked against.
- **The specification** — the VEML 4.0 draft, where element meaning, profiles
  and the sidecar convention are defined.

**Where to get them, honestly stated.** The 4.0 schema and draft are not yet
published separately; the public VEML repository still carries 3.0:

<https://github.com/Five-Squared-Interactive/VEML>

Until 4.0 is published there, the schema that travels inside this add-on is
the authoritative copy you can read, and
[the add-on's issue tracker](https://github.com/Five-Squared-Interactive/WorldKit-VEML-Blender-Plugin/issues)
is the place to ask about the format. Publishing 4.0 is tracked work, not an
oversight we are hoping nobody notices.

## What replaced the old reference

Earlier releases of this add-on shipped a `VEML_REFERENCE.md` describing
VEML **3.0** — document structure, entity types, transforms, sockets. It was
written when the exporter was the only consumer of the format and was never
updated when 4.0 landed. It documented elements that have changed and a
namespace that is no longer emitted, which is worse than documenting nothing.

If you are reading an old copy: the namespace it shows,
`http://www.fivesqd.com/schemas/veml/3.0`, is not what this add-on writes.

## A world, in one glance

What the button leaves on disk:

```
my-world/
├── index.veml                      the world document
└── assets/
    └── model.<hash>.glb            geometry and materials, named by content
```

`index.veml` names the assets beside it by relative path. The hash in an
asset's name is of its bytes, so the same asset is the same URL forever and a
changed one is a new URL — which is what lets a visitor's browser cache it
permanently.
