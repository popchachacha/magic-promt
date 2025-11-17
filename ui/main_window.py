from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
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
    QTextEdit,
)

from prompt_graph import PromptGraph
from ui.localization import Translator


@dataclass
class StageEntry:
    node_id: str
    label: str
    status: str
    description: str
    collects: List[str]


class StageSidebar(QWidget):
    """Left panel with stages derived from the PromptGraph."""

    stage_selected = Signal(str)

    def __init__(self, translator: Translator, stages: Iterable[StageEntry]) -> None:
        super().__init__()
        self.translator = translator
        self._stages = list(stages)
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        heading = QLabel(translator.get("sidebar.heading"))
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        self.progress_label = QLabel()
        self.progress_label.setProperty("class", "muted")
        layout.addWidget(self.progress_label)

        self.list_widget = QListWidget()
        self._populate_list()
        self.list_widget.currentItemChanged.connect(self._handle_selection)
        layout.addWidget(self.list_widget)

        self.preset_label = QLabel(f"{translator.get('sidebar.preset_label')}: —")
        self.preset_label.setObjectName("PresetLabel")
        layout.addWidget(self.preset_label)
        layout.addStretch()

    def _populate_list(self) -> None:
        self.list_widget.clear()
        for index, stage in enumerate(self._stages):
            item = QListWidgetItem(self._format_stage_label(index, stage))
            item.setData(Qt.UserRole, stage.node_id)
            self.list_widget.addItem(item)

    def _format_stage_label(self, index: int, stage: StageEntry) -> str:
        return f"{index + 1}. {stage.label} · {stage.status}"

    def update_stages(self, stages: Iterable[StageEntry]) -> None:
        self._stages = list(stages)
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            stage = self._stages[index]
            item.setText(self._format_stage_label(index, stage))

    def select_stage(self, node_id: str) -> None:
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.data(Qt.UserRole) == node_id:
                self.list_widget.setCurrentRow(row)
                self._update_progress(row)
                break

    def _handle_selection(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if not current:
            return
        node_id = current.data(Qt.UserRole)
        self.stage_selected.emit(node_id)
        self._update_progress(self.list_widget.row(current))

    def _update_progress(self, index: int) -> None:
        total = len(self._stages)
        template = self.translator.get("sidebar.progress")
        self.progress_label.setText(template.format(current=index + 1, total=total))


class CanvasView(QWidget):
    """Central area with current node details and prompt previews."""

    def __init__(self, translator: Translator, current_stage: StageEntry) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.translator = translator
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_label = QLabel(current_stage.label)
        self.title_label.setProperty("class", "title")
        layout.addWidget(self.title_label)

        self.description = QLabel(translator.get("app.tagline"))
        self.description.setWordWrap(True)
        layout.addWidget(self.description)

        template_heading = QLabel(translator.get("canvas.template_heading"))
        template_heading.setProperty("class", "subtitle")
        layout.addWidget(template_heading)

        self.template_body = QLabel(current_stage.description)
        self.template_body.setWordWrap(True)
        self.template_body.setProperty("class", "muted")
        layout.addWidget(self.template_body)

        collects_heading = QLabel(translator.get("canvas.collects_heading"))
        collects_heading.setProperty("class", "subtitle")
        layout.addWidget(collects_heading)

        self.collects_container = QHBoxLayout()
        self.collects_container.setSpacing(8)
        layout.addLayout(self.collects_container)
        self._render_collects(current_stage.collects)

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

    def _render_collects(self, collects: Iterable[str]) -> None:
        while self.collects_container.count():
            item = self.collects_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for field in collects:
            chip = QLabel(field.replace("_", " ").title())
            chip.setProperty("class", "chip")
            self.collects_container.addWidget(chip)
        self.collects_container.addStretch()

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

    def update_stage(self, stage: StageEntry) -> None:
        self.title_label.setText(stage.label)
        self.template_body.setText(stage.description)
        self._render_collects(stage.collects)


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

        notes = QLabel(translator.get("insight.notes"))
        notes.setProperty("class", "subtitle")
        layout.addWidget(notes)

        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText(translator.get("insight.notes_placeholder"))
        layout.addWidget(notes_edit)

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

        self.stages = list(self._build_stage_entries())
        self.sidebar = StageSidebar(self.translator, self.stages)
        self.sidebar.stage_selected.connect(self._handle_stage_selected)
        self.canvas = CanvasView(self.translator, self.stages[0])
        insight = InsightPanel(self.translator)

        splitter.addWidget(self._wrap_scroll(self.sidebar))
        splitter.addWidget(self._wrap_scroll(self.canvas))
        splitter.addWidget(self._wrap_scroll(insight))
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        self.setCentralWidget(splitter)

        if self.stages:
            self.sidebar.select_stage(self.stages[0].node_id)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFrameStyle(QFrame.NoFrame)
        return scroll

    def _build_stage_entries(self) -> Iterable[StageEntry]:
        label_map = self._stage_label_map()
        for node_id, node in self.graph.nodes.items():
            yield StageEntry(
                node_id=node_id,
                label=label_map.get(node_id, node_id),
                status=self.translator.get("sidebar.pending"),
                description=node.prompt_template,
                collects=node.collects,
            )

    def _stage_label_map(self) -> Dict[str, str]:
        return {
            "idea:seed": self.translator.get("canvas.idea_seed"),
            "story:genre": self.translator.get("canvas.story_genre"),
            "style:visual_language": self.translator.get("canvas.style_visual"),
            "technique:camera": self.translator.get("canvas.technique_camera"),
            "delivery:export": self.translator.get("canvas.delivery_export"),
        }

    def _handle_stage_selected(self, node_id: str) -> None:
        target_index = next(
            (index for index, stage in enumerate(self.stages) if stage.node_id == node_id),
            0,
        )
        updated = []
        for index, stage in enumerate(self.stages):
            if index < target_index:
                status = self.translator.get("sidebar.completed")
            elif index == target_index:
                status = self.translator.get("sidebar.active")
            else:
                status = self.translator.get("sidebar.pending")
            updated.append(
                StageEntry(
                    node_id=stage.node_id,
                    label=stage.label,
                    status=status,
                    description=stage.description,
                    collects=stage.collects,
                )
            )
        self.stages = updated
        self.sidebar.update_stages(self.stages)
        self.canvas.update_stage(self.stages[target_index])


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
