from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QCheckBox
from PyQt5.QtCore import pyqtSignal
from widgets.notification import NotificationBanner
from ui.dialogs import DatabaseDialog
from utils.settings import load_settings, save_settings


class SettingsPage(QWidget):
    theme_changed = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent); root = QVBoxLayout(self); title = QLabel("Settings"); title.setObjectName("pageTitle"); root.addWidget(title)
        self.banner = NotificationBanner("Preferences are saved locally for this desktop profile."); root.addWidget(self.banner)
        row = QHBoxLayout(); self.theme = QComboBox(); self.theme.addItems(["dark", "light"]); self.chart = QComboBox(); self.chart.addItems(["Bar", "Line", "Pie", "Scatter", "Histogram", "Box Plot"]); self.font = QSpinBox(); self.font.setRange(8, 18)
        for label, widget in [("Theme", self.theme), ("Default chart type", self.chart), ("Font size", self.font)]: row.addWidget(QLabel(label)); row.addWidget(widget)
        root.addLayout(row); save = QPushButton("Save settings"); save.clicked.connect(self.save); db = QPushButton("Database connection…"); db.clicked.connect(self.db_dialog); root.addWidget(save); root.addWidget(db); root.addStretch()
        values = load_settings(); self.theme.setCurrentText(values["theme"]); self.chart.setCurrentText(values["chart_type"]); self.font.setValue(values["font_size"])

    def save(self):
        ok = save_settings({"theme": self.theme.currentText(), "chart_type": self.chart.currentText(), "font_size": self.font.value()})
        self.theme_changed.emit(self.theme.currentText())
        self.banner.setText("Settings saved locally." if ok else "Could not save settings."); self.banner.set_level("success" if ok else "error")

    def db_dialog(self):
        dialog = DatabaseDialog(self)
        if dialog.exec_():
            self.banner.setText(f"{dialog.config()['type']} connection profile saved for the UI adapter."); self.banner.set_level("success")