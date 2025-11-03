from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from prompt_graph import PromptGraph
from ui.localization import Translator


@dataclass
class StageEntry:
    node_id: str
    label: str
    status: str


class StageSidebar(QWidget):
    """Left panel with stages derived from the PromptGraph."""

    def __init__(self, translator: Translator, stages: Iterable[StageEntry]) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        heading = QLabel(translator.get("sidebar.heading"))
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        self.list_widget = QListWidget()
        for stage in stages:
            item = QListWidgetItem(stage.label)
            item.setData(Qt.UserRole, stage.node_id)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        self.preset_label = QLabel(f"{translator.get('sidebar.preset_label')}: —")
        self.preset_label.setObjectName("PresetLabel")
        layout.addWidget(self.preset_label)
        layout.addStretch()


class CanvasView(QWidget):
    """Central area with current node details and prompt previews."""

    def __init__(self, translator: Translator, current_stage: StageEntry) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(current_stage.label)
        title.setProperty("class", "title")
        layout.addWidget(title)

        description = QLabel(translator.get("app.tagline"))
        description.setWordWrap(True)
        layout.addWidget(description)

        buttons = QHBoxLayout()
        generate = QPushButton(translator.get("actions.generate"))
        regenerate = QPushButton(translator.get("actions.regenerate"))
        regenerate.setObjectName("GhostButton")
        buttons.addWidget(generate)
        buttons.addWidget(regenerate)
        buttons.addStretch()
        layout.addLayout(buttons)

        previews = QHBoxLayout()
        preview_ru = self._build_preview(translator.get("canvas.prompt_ru"), placeholder="—")
        preview_en = self._build_preview(translator.get("canvas.prompt_en"), placeholder="—")
        previews.addWidget(preview_ru)
        previews.addWidget(preview_en)
        layout.addLayout(previews)

    @staticmethod
    def _build_preview(title: str, placeholder: str) -> QWidget:
        container = QFrame()
        container.setObjectName("Panel")
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(8)

        label = QLabel(title)
        label.setProperty("class", "subtitle")
        content = QLabel(placeholder)
        content.setProperty("class", "muted")
        content.setWordWrap(True)

        inner_layout.addWidget(label)
        inner_layout.addWidget(content)
        inner_layout.addStretch()
        return container


class InsightPanel(QWidget):
    """Right-hand column with templates, history, and tags."""

    def __init__(self, translator: Translator) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        templates = QLabel(translator.get("insight.templates"))
        templates.setProperty("class", "subtitle")
        layout.addWidget(templates)

        layout.addWidget(QLabel("• Neon cityscape\n• Cozy coffee shop\n• Futuristic dashboard"))

        history = QLabel(translator.get("insight.history"))
        history.setProperty("class", "subtitle")
        layout.addWidget(history)
        layout.addWidget(QLabel("— v0.1 Initial idea\n— v0.2 Added color palette"))

        tags = QLabel(translator.get("insight.tags"))
        tags.setProperty("class", "subtitle")
        layout.addWidget(tags)
        layout.addWidget(QLabel("#dreamy  #cinematic  #neon"))

        layout.addStretch()

        export = QPushButton(translator.get("actions.export"))
        layout.addWidget(export)


class MainWindow(QMainWindow):
    """Main application window composed of three panels."""

    def __init__(self, graph: PromptGraph, translator: Translator) -> None:
        super().__init__()
        self.graph = graph
        self.translator = translator
        self.setWindowTitle(translator.get("app.title"))
        self.resize(1280, 780)
        self._setup_layout()

    def _setup_layout(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        stages = list(self._build_stage_entries())
        sidebar = StageSidebar(self.translator, stages)
        canvas = CanvasView(self.translator, stages[0])
        insight = InsightPanel(self.translator)

        splitter.addWidget(self._wrap_scroll(sidebar))
        splitter.addWidget(self._wrap_scroll(canvas))
        splitter.addWidget(self._wrap_scroll(insight))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        self.setCentralWidget(splitter)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFrameStyle(QFrame.NoFrame)
        return scroll

    def _build_stage_entries(self) -> Iterable[StageEntry]:
        label_map = self._stage_label_map()
        for node_id in self.graph.nodes:
            yield StageEntry(
                node_id=node_id,
                label=label_map.get(node_id, node_id),
                status=self.translator.get("sidebar.pending"),
            )

    def _stage_label_map(self) -> Dict[str, str]:
        return {
            "idea:seed": self.translator.get("canvas.idea_seed"),
            "story:genre": self.translator.get("canvas.story_genre"),
            "style:visual_language": self.translator.get("canvas.style_visual"),
            "technique:camera": self.translator.get("canvas.technique_camera"),
            "delivery:export": self.translator.get("canvas.delivery_export"),
        }


def run_headless(window_factory: callable) -> Tuple[bool, str]:
    """
    Helper used by smoke tests to ensure the UI can instantiate.

    Returns tuple(success, message).
    """
    app = QApplication.instance()
    created_app = False
    if app is None:
        created_app = True
        app = QApplication([])
    success = True
    message = "UI instantiated"
    try:
        window = window_factory()
        QTimer.singleShot(0, window.close)
        if created_app:
            QTimer.singleShot(0, app.quit)
        window.show()
        app.processEvents()
    except Exception as exc:  # pragma: no cover - runtime guard
        success = False
        message = str(exc)
    finally:
        if created_app:
            app.exit()
    return success, message
