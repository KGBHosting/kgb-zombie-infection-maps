# KGB Zombie Infection Maps

Three original **development maps** for classic Counter-Strike 1.6 zombie infection. Humans prepare, defend and survive; zombies attack through multiple approaches. There is no escape objective. These are new layouts, not recreations or decompilations of customer, Valve or community maps.

Version **0.1.0** is a **development candidate**. Local source/build/static qualification passed. An initial development smoke check of courtyard download/rendering and its central stairs completed on 2026-11-11; full three-map movement,32-slot capacity, gameplay and rotation acceptance remain pending. Do not describe the pack as gameplay-verified or production-ready.

| Map | Layout and defense positions |
| --- | --- |
| `zm_kgb_courtyard_v1` | Covered courtyard fort, a raised central position and two covered side arcades. Each has separate north/south stairs. Flank alleys run behind the arcades. |
| `zm_kgb_depot_v1` | Industrial depot with two loading platforms linked by a catwalk. Each platform has north/south stairs; players can also approach over the catwalk. Crates break ground-level sightlines. |
| `zm_kgb_containment_v1` | Containment facility with four rooms around a central control dais. Each room has two opposed entrances and two stair approaches to its raised position. |

Every map has 32 distinct `info_player_start` (CT) and 32 distinct `info_player_deathmatch` (T) origins. This matters for the infection core: every player begins the round as a human on CT, so a conventional 16 CT +16 T layout is insufficient evidence of 32-player startup capacity. The engine's server slot maximum remains 32;64 origins do not mean 64-player support.

All client textures are original procedural pixels embedded in each BSP. The maps require no custom WAD, model, sound, sprite or sky files. The ceiling is a textured physical surface, not a reference to a separately distributed skybox. Lighting and VIS are compiled into standard BSP30 lumps. There are no objective, escape, map-change, forced-command, weapon-loadout or plugin entities.

## License and public provenance

Original map geometry, `.map` source, first-party tools and procedural textures are **CC0-1.0**, including commercial use and redistribution. See [LICENSE](LICENSE) and [the complete CC0 text](licenses/CC0-1.0.txt). `tools/generate.py` produces every map brush and texture pixel; no third-party art is used.

The build compiler is independently licensed software. Its public source, exact commit, submodules, official dependency downloads and checksums are recorded in [tools/toolchain.json](tools/toolchain.json). The qualified compiler is [ericw-tools 2.0.0-alpha11](https://github.com/ericwa/ericw-tools/tree/c243aa348c9e5a1838bb69cf6c3ff20bebd94a8a), built from source. Its documented `-hlbsp` mode emits the Half-Life/GoldSrc format with the appropriate player hull dimensions. Embree and oneTBB are official pinned build-only dependency archives. No compiler executable or dependency is shipped in the runtime ZIP.

## Rebuild and inspect

Requires Docker, Git, curl, Python 3 and Make. Tool downloads are public; the build itself runs with networking disabled. The image uses `linux/amd64`, including on an Apple Silicon host.

```sh
make generate
make toolchain
make compile
make validate
make test
make repro
make preview
make package
```

`make toolchain` pins the Ubuntu image digest, compiler source/submodule commits and dependency archive SHA256 hashes. Apt package versions are recorded in `evidence/toolchain-packages.txt`; the apt repository is not snapshot-pinned. The qualified local image and executable hashes are recorded. A fresh compiler image must independently qualify its outputs; cross-platform byte equality has not been tested.

Both local builds use one worker for BSP/VIS/light, full VIS and `light -extra`. No BSP2, BSPX, `.lit` or engine extensions are requested. The qualified local compiler source has one upstream enum comparison warning in `common/bspinfo.cc:732`; all three **map compilation passes** are warning/error/leak-free. That compiler warning has not been patched or hidden.

## Verification and limits

The local qualification in `evidence/qualification.json` checks:

- BSP30 headers/lump bounds, supported entity classes and all embedded texture mips/palettes.
-32 CT +32 T unique spawn origins, nonoverlapping player boxes, floor support and empty standing/crouching compiled player hulls.
- Existing RGB lighting and visibility data, with no objective or external asset entity references.
- A 32-unit grid over actual compiled floor levels: standing-hull path checks with at most 18-unit steps connect both spawn regions and named approaches to the defense positions. Each move is sampled in four subsegments. This is a bounded static check, not a GoldSrc movement simulation.
- Two independent output-directory builds producing identical BSP bytes.

Eight focused tests include negative controls that corrupt a local map copy: overlapping/blocked spawns, missing embedded texture data, wrong BSP version, unknown entity, missing lighting and invalid lump bounds. They never alter a server.

The compiler's SVG previews in `evidence/*.compiled-preview.svg` show actual compiled geometry from above. They are **offline previews**, not client screenshots. Crate roofs, decorative ledges and jump routes are not certified by the ordinary-walk grid. Simultaneous32-client spawning, performance, real movement, infection gameplay, balance and download behavior remain live acceptance requirements in [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## Runtime package contract

`dist/kgb-zombie-infection-maps-0.1.0.zip` contains exactly:

```text
kgb_zombie_infection_mapcycle.txt
maps/zm_kgb_courtyard_v1.bsp
maps/zm_kgb_depot_v1.bsp
maps/zm_kgb_containment_v1.bsp
```

The cycle lists courtyard, depot and containment in that order, one basename per line. The pack leaves `mapcycle.txt` and stock maps untouched. Courtyard is the proposed managed startup default. Source, license and build provenance belong in separate release artifacts. Installation must use explicit managed-file mappings with pinned hashes and must refuse collisions with unowned files; it must not blindly extract arbitrary archives.

`dist/manifest.json` records per-file SHA256/SHA512 and archive bytes/hashes. Published filenames/version pins must be immutable. A later map change requires a new version and fresh qualification.
