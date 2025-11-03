# Prompt Graph Design

The Prompt Graph formalises how the assistant navigates from a raw idea to a refined prompt. It is intentionally declarative so we can expand scenarios without touching the core dialogue engine.

## Core Concepts

- **Layer** — a logical step in the journey (e.g., `idea`, `story`, `style`, `technique`, `delivery`).
- **Node** — a concrete question or action inside a layer. Nodes contain:
  - `id`: stable identifier (e.g., `story:genre`).
  - `prompt`: system/user message template presented to the LLM.
  - `collect`: fields we expect to store (e.g., `genre`, `mood`).
  - `transforms`: optional post-processing hooks.
- **Edge** — transition rules between nodes. Conditions depend on collected data (e.g., skip `technique` if the user selected `photography` preset).
- **Preset** — a reusable configuration for specific domains (branding, characters, environments, UI mockups).

## Data Flow

1. Start with an **entry node** (`idea:seed`) that captures the raw request.
2. Progress through layers via edges, enriching the context with structured data.
3. At each node, the engine composes an instruction using the `prompt` template and current context, then queries the local LLM.
4. The engine stores responses in a conversation state tree that mirrors the graph.
5. Once terminal nodes are reached, a final assembler builds the bilingual prompt package (`ru`, `en`, metadata).

## Extensibility

- Layers can be toggled on/off per template by modifying the edge map.
- New presets introduce domain-specific nodes while reusing shared layers.
- Because nodes are declarative, UI builders can introspect the graph to render cards, preview states, and enable drag-and-drop reordering of layers.

## Example Flow

```
idea:seed      → story:genre → story:beats → style:visual_language
                         ↘                 ↘
                          story:references  technique:camera
                                               ↘
                                                delivery:export
```

## Storage Schema (Draft)

| Table          | Purpose                               |
|----------------|---------------------------------------|
| `projects`     | Top-level prompt projects             |
| `graph_state`  | Captured answers per node             |
| `presets`      | Available presets and metadata        |
| `exports`      | Saved bilingual prompt outputs        |

This schema maps one-to-one with the `PromptGraph` primitives defined in `prompt_graph.py`.
