"""
Declarative Prompt Graph primitives used to guide the multi-layer prompt workflow.

The graph is intentionally lightweight: it can be loaded from static JSON/YAML,
manipulated in memory, and rendered inside the UI to keep the engine and
presentation in sync.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


Condition = Callable[["GraphContext"], bool]
Transform = Callable[[Dict[str, str], "GraphContext"], Dict[str, str]]


@dataclass
class Node:
    """Single actionable step inside the prompt graph."""

    id: str
    layer: str
    prompt_template: str
    collects: List[str]
    summary_key: Optional[str] = None
    transforms: List[Transform] = field(default_factory=list)


@dataclass
class Edge:
    """Directional link between two nodes with an optional condition."""

    source: str
    target: str
    condition: Optional[Condition] = None


@dataclass
class PromptGraph:
    """Collection of nodes and edges describing a multi-layer prompt journey."""

    nodes: Dict[str, Node]
    edges: List[Edge]
    entrypoint: str

    def next_nodes(self, node_id: str, context: "GraphContext") -> List[Node]:
        """Resolve the next nodes reachable from `node_id` given the current context."""
        return [
            self.nodes[edge.target]
            for edge in self.edges
            if edge.source == node_id and (edge.condition is None or edge.condition(context))
        ]


@dataclass
class GraphContext:
    """Holds state accumulated while traversing the graph."""

    answers: Dict[str, Dict[str, str]] = field(default_factory=dict)
    preset: Optional[str] = None

    def store_answer(self, node: Node, payload: Dict[str, str]) -> None:
        """Attach collected payload to the node."""
        enriched = payload
        for transform in node.transforms:
            enriched = transform(enriched, self)
        self.answers[node.id] = enriched


def default_graph() -> PromptGraph:
    """Seed graph used by the CLI MVP and as a baseline for the UI."""
    nodes = {
        "idea:seed": Node(
            id="idea:seed",
            layer="idea",
            prompt_template="Собери исходную идею пользователя для генерации изображения.",
            collects=["concept", "audience", "goal"],
            summary_key="concept",
        ),
        "story:genre": Node(
            id="story:genre",
            layer="story",
            prompt_template="Уточни жанр, настроение и ключевые элементы сюжета.",
            collects=["genre", "mood", "key_elements"],
        ),
        "style:visual_language": Node(
            id="style:visual_language",
            layer="style",
            prompt_template="Определи визуальный стиль, цветовую палитру и источники вдохновения.",
            collects=["visual_style", "color_palette", "inspiration"],
        ),
        "technique:camera": Node(
            id="technique:camera",
            layer="technique",
            prompt_template="Если уместно, задай технические параметры (камера, объектив, освещение).",
            collects=["camera", "lens", "lighting"],
        ),
        "delivery:export": Node(
            id="delivery:export",
            layer="delivery",
            prompt_template="Собери финальный промпт и переведи его на русский и английский.",
            collects=["prompt_ru", "prompt_en"],
        ),
    }

    edges = [
        Edge(source="idea:seed", target="story:genre"),
        Edge(source="story:genre", target="style:visual_language"),
        Edge(source="style:visual_language", target="technique:camera"),
        Edge(
            source="technique:camera",
            target="delivery:export",
            condition=lambda ctx: ctx.answers.get("technique:camera", {}).get("camera") is not None,
        ),
        Edge(
            source="style:visual_language",
            target="delivery:export",
            condition=lambda ctx: ctx.answers.get("style:visual_language") is not None,
        ),
    ]

    return PromptGraph(nodes=nodes, edges=edges, entrypoint="idea:seed")
