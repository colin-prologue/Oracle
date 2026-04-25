<!-- ORACLE ARTIFACT — canonical copy in the Hindsight repo. Cross-project philosophy. Do not treat as a rule of the source project. -->

## PHI-010 — Templates and starter kits should ship dependency-free

**Date:** 2026-04-25
**Domain:** architecture
**Source Project:** Claude-Root
**Source:** Removing the vector memory server from the Claude-Root speckit template reduced its dependency footprint from Python/uv/Ollama/LanceDB/FastMCP to zero, making it immediately usable on any project.

### Philosophy
A reusable workflow template's value degrades with every runtime dependency it requires. Infrastructure choices that serve the template author become adoption friction for every downstream user; optional capabilities belong in separate, opt-in layers.

### Why I Hold This
The Claude-Root template required Ollama (local AI server), LanceDB, FastMCP, Python 3.10+, and uv just to use the speckit workflow — none of which had anything to do with the workflow itself. Every new user of the template inherited setup steps the author had already sunk. Extracting the memory server to an archive branch eliminated the barrier entirely.

### Where It Applies
Any starter kit, scaffolding tool, project template, or boilerplate: speckit-style workflow templates, framework generators, cookiecutter templates, GitHub template repos. Most load-bearing when the template's purpose is process or convention (not a tech demo of a specific dependency).

### Known Tensions
Some templates are explicitly demos of a specific technology (a React starter should have React). The principle is least applicable when the dependency IS the point. It is most applicable when the dependency is incidental infrastructure the author found useful but the user may not need.

### Open to Revision When
A dependency becomes universally available with zero setup (e.g., if Ollama ships as a macOS system service that every developer already has). At that point it stops being adoption friction.
