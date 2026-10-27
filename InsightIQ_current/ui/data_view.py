from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
                              QLineEdit, QComboBox, QProgressBar, QAbstractItemView)
from PyQt5.QtCore import QThread, pyqtSignal
from widgets.data_table import DataTable
from widgets.notification import NotificationBanner
from utils.file_manager import add_recent_file


class LoadWorker(QThread):
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)
    def __init__(self, service, path):
        super().__init__(); self.service = service; self.path = path
    def run(self):
        try: self.loaded.emit(self.service.load_file(self.path))
        except Exception as exc: self.failed.emit(str(exc))


class DataPage(QWidget):
    data_changed = pyqtSignal()
    def __init__(self, data_service, parent=None):
        super().__init__(parent); self.data_service = data_service; self.worker = None
        root = QVBoxLayout(self)
        top = QHBoxLayout(); title = QLabel("Data workspace"); title.setObjectName("pageTitle")
        top.addWidget(title); top.addStretch()
        self.open_btn = QPushButton("Open file"); self.open_btn.clicked.connect(self.choose_file)
        self.demo_btn = QPushButton("Reset demo data"); self.demo_btn.clicked.connect(self.reset_demo)
        top.addWidget(self.open_btn); top.addWidget(self.demo_btn); root.addLayout(top)
        self.banner = NotificationBanner("Drag a CSV or Excel file anywhere onto the window, or use Open file.")
        root.addWidget(self.banner)
        controls = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search all rows…"); self.search.textChanged.connect(self.apply_filter)
        self.columns = QComboBox(); self.columns.setEditable(False); self.columns.setToolTip("Choose visible columns")
        self.columns.currentIndexChanged.connect(self.apply_filter)
        clear = QPushButton("Clear filter"); clear.clicked.connect(self.clear_filter)
        refresh = QPushButton("Refresh"); refresh.clicked.connect(self.refresh)
        controls.addWidget(self.search, 2); controls.addWidget(QLabel("Visible columns")); controls.addWidget(self.columns, 1)
        controls.addWidget(clear); controls.addWidget(refresh); root.addLayout(controls)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); root.addWidget(self.progress)
        self.meta = QLabel(); self.meta.setObjectName("muted"); root.addWidget(self.meta)
        self.table = DataTable(); self.table.setDragEnabled(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        root.addWidget(self.table, 1); self.refresh()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open dataset", "", "Data files (*.csv *.xlsx *.xls)")
        if path: self.load_path(path)

    def load_path(self, path):
        self.progress.show(); self.open_btn.setEnabled(False)
        self.worker = LoadWorker(self.data_service, path)
        self.worker.loaded.connect(lambda _: self.load_done(path))
        self.worker.failed.connect(self.load_failed); self.worker.start()

    def load_done(self, path):
        add_recent_file(path); self.progress.hide(); self.open_btn.setEnabled(True)
        self.banner.setText(f"Loaded {path}"); self.banner.set_level("success"); self.refresh(); self.data_changed.emit()

    def load_failed(self, message):
        self.progress.hide(); self.open_btn.setEnabled(True); self.banner.setText(f"Could not load file: {message}"); self.banner.set_level("error")

    def reset_demo(self):
        self.data_service.reset_demo(); self.banner.setText("Local demo dataset restored."); self.banner.set_level("success"); self.refresh(); self.data_changed.emit()

    def refresh(self):
        frame = self.data_service.data
        self.columns.blockSignals(True); self.columns.clear(); self.columns.addItem("All columns"); self.columns.addItems([str(c) for c in frame.columns]); self.columns.blockSignals(False)
        self.apply_filter()

    def apply_filter(self):
        choice = self.columns.currentText()
        selected = None if choice in ("", "All columns") else [choice]
        frame = self.data_service.filtered(self.search.text(), selected)
        stats = self.data_service.summary()
        self.meta.setText(f"{len(frame):,} visible rows • {len(frame.columns):,} columns • source: {self.data_service.source}")
        self.table.set_frame(frame)

    def clear_filter(self):
        self.search.clear(); self.columns.setCurrentIndex(0); self.apply_filter()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".csv", ".xlsx", ".xls")): self.load_path(path); break