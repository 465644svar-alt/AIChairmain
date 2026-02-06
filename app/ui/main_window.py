from __future__ import annotations

import asyncio
import json
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from ..core.branching import ConversationTree
from ..core.council import CouncilOrchestrator
from ..core.storage import ConversationStorage
from ..core.types import ConversationNode


class CouncilWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, orchestrator: CouncilOrchestrator, question: str, models: dict[str, str], chairman_provider: str, chairman_model: str):
        super().__init__()
        self.orchestrator = orchestrator
        self.question = question
        self.models = models
        self.chairman_provider = chairman_provider
        self.chairman_model = chairman_model

    def run(self) -> None:
        try:
            result = asyncio.run(
                self.orchestrator.run(self.question, self.models, self.chairman_provider, self.chairman_model)
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, orchestrator: CouncilOrchestrator, storage: ConversationStorage, log_handler):
        super().__init__()
        self.setWindowTitle("AI Chairman - LLM Council")
        self.resize(1300, 850)
        self.orchestrator = orchestrator
        self.storage = storage
        self.log_handler = log_handler
        self.tree = ConversationTree()
        self.current_result: dict | None = None
        self.worker_thread: QThread | None = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.chat_tab = self._build_chat_tab()
        self.stage1_view = QTextEdit(readOnly=True)
        self.stage2_view = QTextEdit(readOnly=True)
        self.ranking_view = QTextEdit(readOnly=True)
        self.settings_tab = self._build_settings_tab()
        self.history_tab = self._build_history_tab()
        self.logs_tab = self._build_logs_tab()

        self.tabs.addTab(self.chat_tab, "Chat")
        self.tabs.addTab(self.stage1_view, "Stage 1")
        self.tabs.addTab(self.stage2_view, "Stage 2")
        self.tabs.addTab(self.ranking_view, "Ranking")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.logs_tab, "Logs")

        self.refresh_history()
        self.refresh_logs()

    def _build_chat_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        splitter = QSplitter()
        layout.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.branch_tree = QTreeWidget()
        self.branch_tree.setHeaderLabels(["Branch nodes"])
        left_layout.addWidget(self.branch_tree)

        btn_set_active = QPushButton("Set Active Branch")
        btn_set_active.clicked.connect(self.set_active_branch)
        left_layout.addWidget(btn_set_active)

        btn_continue = QPushButton("Continue from here")
        btn_continue.clicked.connect(self.continue_from_selected)
        left_layout.addWidget(btn_continue)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.timeline = QTextEdit(readOnly=True)
        right_layout.addWidget(self.timeline)
        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("Введите вопрос...")
        right_layout.addWidget(self.question_input)

        controls = QHBoxLayout()
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_question)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_run)
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_chat)
        controls.addWidget(self.send_btn)
        controls.addWidget(self.cancel_btn)
        controls.addWidget(self.export_btn)
        right_layout.addLayout(controls)

        self.progress_label = QLabel("Idle")
        right_layout.addWidget(self.progress_label)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([350, 950])
        return widget

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        self.models_input = QLineEdit("gpt:gpt-4o-mini,deepseek:deepseek-chat,claude:claude-3-5-sonnet,mistral:mistral-small,groq:llama-3.1-70b")
        self.chairman_provider_input = QLineEdit("gpt")
        self.chairman_model_input = QLineEdit("gpt-4o")
        self.timeout_input = QLineEdit("60")
        form.addRow("Models provider:model", self.models_input)
        form.addRow("Chairman provider", self.chairman_provider_input)
        form.addRow("Chairman model", self.chairman_model_input)
        form.addRow("Timeout (sec)", self.timeout_input)
        return tab

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        btns = QHBoxLayout()
        load_btn = QPushButton("Open conversation")
        load_btn.clicked.connect(self.load_selected_history)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_history)
        btns.addWidget(load_btn)
        btns.addWidget(refresh_btn)
        layout.addLayout(btns)
        return tab

    def _build_logs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.logs_view = QTextEdit(readOnly=True)
        layout.addWidget(self.logs_view)
        btn = QPushButton("Export logs")
        btn.clicked.connect(self.export_logs)
        layout.addWidget(btn)
        return tab

    def parse_models(self) -> dict[str, str]:
        pairs = [x.strip() for x in self.models_input.text().split(",") if x.strip()]
        out = {}
        for p in pairs:
            if ":" in p:
                provider, model = p.split(":", 1)
                out[provider.strip()] = model.strip()
        return out

    def send_question(self) -> None:
        question = self.question_input.toPlainText().strip()
        if not question:
            return
        self.progress_label.setText("Stage1 running...")
        parent_id = self.tree.active_node_id
        self.tree.add_node(ConversationNode.new("user", question, parent_id))
        self.render_tree()
        self.render_timeline()

        models = self.parse_models()
        self.orchestrator.timeout = float(self.timeout_input.text() or "60")
        worker = CouncilWorker(
            self.orchestrator,
            question,
            models,
            self.chairman_provider_input.text().strip(),
            self.chairman_model_input.text().strip(),
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.on_council_finished)
        worker.failed.connect(self.on_council_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.start()
        self.worker_thread = thread
        self.worker = worker

    def on_council_finished(self, result: dict) -> None:
        self.current_result = result
        self.progress_label.setText("Stage3 completed")
        content = result.get("stage3", {}).get("content") or "(empty)"
        node = ConversationNode.new("assistant", content, self.tree.active_node_id, stage_data=result)
        self.tree.add_node(node)
        self.render_tree()
        self.render_timeline()

        self.stage1_view.setPlainText(json.dumps(result.get("stage1", {}), ensure_ascii=False, indent=2))
        self.stage2_view.setPlainText(json.dumps(result.get("stage2", {}), ensure_ascii=False, indent=2))
        self.ranking_view.setPlainText(json.dumps(result.get("stage2", {}).get("aggregate", {}), ensure_ascii=False, indent=2))

        payload = {
            "tree": self.tree.to_dict(),
            "active_branch_id": self.tree.active_node_id,
            "settings": {
                "models": self.parse_models(),
                "chairman_provider": self.chairman_provider_input.text().strip(),
                "chairman_model": self.chairman_model_input.text().strip(),
            },
            "latest_result": result,
        }
        self.storage.save(payload)
        self.refresh_history()
        self.refresh_logs()

    def on_council_failed(self, error: str) -> None:
        QMessageBox.critical(self, "Pipeline failed", error)
        self.progress_label.setText("Failed")
        self.refresh_logs()

    def cancel_run(self) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.quit()
            self.progress_label.setText("Cancelled")

    def render_timeline(self) -> None:
        lines = []
        for node in self.tree.lineage():
            lines.append(f"[{node.created_at}] {node.role.upper()}: {node.content}")
            if node.stage_data:
                lines.append("  └─ stage data attached (expand in tabs)")
        self.timeline.setPlainText("\n\n".join(lines))

    def render_tree(self) -> None:
        self.branch_tree.clear()

        def add_items(parent_item, parent_id):
            for child_id in self.tree.children.get(parent_id, []):
                node = self.tree.nodes[child_id]
                text = f"{node.role}: {node.content[:40]}"
                item = QTreeWidgetItem([text])
                item.setData(0, 1, node.id)
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.branch_tree.addTopLevelItem(item)
                add_items(item, node.id)

        add_items(None, None)
        self.branch_tree.expandAll()

    def set_active_branch(self) -> None:
        item = self.branch_tree.currentItem()
        if not item:
            return
        node_id = item.data(0, 1)
        self.tree.set_active(node_id)
        self.render_timeline()

    def continue_from_selected(self) -> None:
        item = self.branch_tree.currentItem()
        if item:
            self.tree.set_active(item.data(0, 1))
            self.progress_label.setText("Branch selected. Enter next question.")

    def export_chat(self) -> None:
        if not self.tree.nodes:
            return
        directory = QFileDialog.getExistingDirectory(self, "Choose export directory")
        if not directory:
            return
        include_stage = QCheckBox("include")
        include_stage.setChecked(True)
        include = include_stage.isChecked()
        active_path = Path(directory) / "chat_active_branch.md"
        full_json = Path(directory) / "chat_full_tree.json"

        active_lines = []
        for node in self.tree.lineage():
            active_lines.append(f"## {node.role} ({node.created_at})\n\n{node.content}\n")
            if include and node.stage_data:
                active_lines.append("```json\n" + json.dumps(node.stage_data, ensure_ascii=False, indent=2) + "\n```\n")
        active_path.write_text("\n".join(active_lines), encoding="utf-8")
        full_json.write_text(json.dumps(self.tree.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Export", f"Saved to {directory}")

    def refresh_history(self) -> None:
        self.history_list.clear()
        self.history_list.addItems(self.storage.list_ids())

    def load_selected_history(self) -> None:
        item = self.history_list.currentItem()
        if not item:
            return
        payload = self.storage.load(item.text())
        self.tree = ConversationTree.from_dict(payload["tree"])
        self.render_tree()
        self.render_timeline()

    def refresh_logs(self) -> None:
        self.logs_view.setPlainText("\n".join(self.log_handler.dump()))

    def export_logs(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose log export directory")
        if not directory:
            return
        out = Path(directory) / "logs_export.txt"
        out.write_text("\n".join(self.log_handler.dump()), encoding="utf-8")
        QMessageBox.information(self, "Logs", f"Logs exported to {out}")
