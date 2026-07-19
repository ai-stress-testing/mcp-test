# Enterprise Doc — <project>

This doc UPDATES OVER TIME. The spec-driven PM (`agents/pm/project-manager`)
classifies new work against it during decomposition and extends it when a
decomposition reveals a concept, tier, class, or term that isn't here yet.
Stale entries are deleted, not preserved — this is a living reference, not
an append-only log.

## Tiering

The strategic / tactical / operational layers of the project: what
decides, what plans, what executes. One line per layer — who/what sits
there, not a narrative.

- **Strategic** — <what decides direction>
- **Tactical** — <what plans/decomposes toward that direction>
- **Operational** — <what executes>

## Ontology

The project's core concepts and the relations between them. State
relations explicitly ("X owns Y", "A verifies B") — an ontology is edges,
not just nodes.

- <Concept> —(relation)→ <Concept>

## Taxonomy

Classification trees actually in use — teams → roles, artifact types,
issue classes. Only what's real today; a tree entry with nothing in it
gets deleted, not left as a placeholder.

- <Category>
  - <Subcategory>

## Semantics

The glossary. Terms with exact meanings, one line each, so agents and
humans stop redefining words mid-project.

- **<Term>** — <exact meaning>
