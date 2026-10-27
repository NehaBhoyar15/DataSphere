from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
                              QLineEdit, QFileDialog, QDateEdit)
from PyQt5.QtCore import QDate
from widgets.chart_widget import ChartWidget
from widgets.notification import NotificationBanner
from services.chart_service import ChartService


class ChartsPage(QWidget):
    def __init__(self, data_service, parent=None):
        super().__init__(parent); self.data_service = data_service
        root = QVBoxLayout(self); title = QLabel("Chart studio"); title.setObjectName("pageTitle"); root.addWidget(title)
        controls = QHBoxLayout()
        self.type = QComboBox(); self.type.addItems(["Bar", "Line", "Pie", "Scatter", "Histogram", "Box Plot"])
        self.x = QComboBox(); self.y = QComboBox(); self.color = QComboBox(); self.color.addItem("None")
        self.title = QLineEdit("Analytics chart"); self.title.setToolTip("Chart title")
        for label, box in [("Chart", self.type), ("X-axis", self.x), ("Y-axis", self.y), ("Color", self.color)]:
            controls.addWidget(QLabel(label)); controls.addWidget(box)
        controls.addWidget(self.title, 2)
        refresh = QPushButton("Refresh chart"); refresh.clicked.connect(self.refresh_chart)
        clear = QPushButton("Clear"); clear.clicked.connect(lambda: self.chart.clear())
        controls.addWidget(refresh); controls.addWidget(clear); root.addLayout(controls)
        dates = QHBoxLayout(); dates.addWidget(QLabel("Date range (optional)"))
        self.start = QDateEdit(QDate.currentDate().addYears(-5)); self.end = QDateEdit(QDate.currentDate().addYears(5))
        self.start.setCalendarPopup(True); self.end.setCalendarPopup(True)
        dates.addWidget(self.start); dates.addWidget(self.end); dates.addStretch(); root.addLayout(dates)
        self.banner = NotificationBanner("Choose fields to explore the local dataset."); root.addWidget(self.banner)
        self.chart = ChartWidget(); root.addWidget(self.chart, 1)
        export = QHBoxLayout()
        for text, ext in [("Export PNG", "png"), ("Export SVG", "svg"), ("Export HTML", "html")]:
            button = QPushButton(text); button.clicked.connect(lambda checked=False, e=ext: self.export(e)); export.addWidget(button)
        export.addStretch(); root.addLayout(export); self.refresh_fields()

    def refresh_fields(self):
        cols = [str(c) for c in self.data_service.data.columns]; numeric = [str(c) for c in self.data_service.data.select_dtypes(include="number").columns]
        for box, values in [(self.x, cols), (self.y, numeric), (self.color, ["None"] + cols)]:
            current = box.currentText(); box.blockSignals(True); box.clear(); box.addItems(values)
            if current in values: box.setCurrentText(current)
            box.blockSignals(False)

    def refresh_chart(self):
        frame = self.data_service.data
        date_col = self.x.currentText()
        if date_col in frame.columns:
            parsed = __import__("pandas").to_datetime(frame[date_col], errors="coerce")
            if parsed.notna().sum() > 0:
                start = self.start.date().toPyDate()
                end = self.end.date().toPyDate()
                frame = frame[(parsed.dt.date >= start) & (parsed.dt.date <= end)]
        ChartService.render(self.chart.ax, frame, self.type.currentText(), self.x.currentText(),
                            self.y.currentText(), None if self.color.currentText() == "None" else self.color.currentText(),
                            self.title.text())
        self.chart.apply_theme(); self.chart.canvas.draw_idle()

    def export(self, ext):
        path, _ = QFileDialog.getSaveFileName(self, "Export chart", f"chart.{ext}", f"{ext.upper()} (*.{ext})")
        if not path: return
        try:
            if ext == "png": ChartService.export_png(self.chart.figure, path)
            elif ext == "svg": ChartService.export_svg(self.chart.figure, path)
            else:
                if not ChartService.export_html(self.data_service.data, self.type.currentText(), self.x.currentText(), self.y.currentText(), self.title.text(), path):
                    raise RuntimeError("Plotly is not installed; install requirements.txt for HTML export.")
            self.banner.setText(f"Chart exported to {path}"); self.banner.set_level("success")
        except Exception as exc:
            self.banner.setText(str(exc)); self.banner.set_level("error")