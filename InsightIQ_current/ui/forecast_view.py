from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from widgets.chart_widget import ChartWidget
from widgets.metric_card import MetricCard
from widgets.notification import NotificationBanner
from services.forecast_service import ForecastService


class ForecastPage(QWidget):
    def __init__(self, data_service, parent=None):
        super().__init__(parent); self.data_service = data_service; self.service = ForecastService()
        root = QVBoxLayout(self); title = QLabel("Forecasting"); title.setObjectName("pageTitle"); root.addWidget(title)
        controls = QHBoxLayout(); self.date = QComboBox(); self.value = QComboBox(); self.model = QComboBox(); self.model.addItems(ForecastService.MODELS); self.horizon = QSlider(Qt.Horizontal); self.horizon.setRange(3, 30); self.horizon.setValue(7); run = QPushButton("Run forecast"); run.clicked.connect(self.run)
        for label, widget in [("Date", self.date), ("Value", self.value), ("Model", self.model), ("Horizon", self.horizon)]: controls.addWidget(QLabel(label)); controls.addWidget(widget)
        controls.addWidget(run); root.addLayout(controls)
        self.banner = NotificationBanner("Supports Holt-Winters, ARIMA and Prophet with graceful local fallback."); root.addWidget(self.banner)
        cards = QHBoxLayout(); self.cards = [MetricCard("MAE"), MetricCard("RMSE", accent="#34d399"), MetricCard("MAPE", accent="#f59e0b")]; [cards.addWidget(c) for c in self.cards]; root.addLayout(cards)
        self.chart = ChartWidget(); root.addWidget(self.chart, 2); self.results = QTableWidget(0, 4); self.results.setHorizontalHeaderLabels(["Date", "Forecast", "Lower", "Upper"]); root.addWidget(self.results, 1); self.refresh_fields(); self.run()

    def refresh_fields(self):
        frame = self.data_service.data; self.date.clear(); self.value.clear()
        self.date.addItems([str(c) for c in frame.columns]); self.value.addItems([str(c) for c in frame.select_dtypes(include="number").columns])
        if "date" in [str(c) for c in frame.columns]: self.date.setCurrentText("date")
        if "revenue" in [str(c) for c in frame.columns]: self.value.setCurrentText("revenue")

    def run(self):
        try:
            result = self.service.forecast(self.data_service.data, self.date.currentText(), self.value.currentText(), self.horizon.value(), self.model.currentText())
            self.cards[0].set_value(f"{result['mae']:.2f}"); self.cards[1].set_value(f"{result['rmse']:.2f}"); self.cards[2].set_value(f"{result['mape']:.1f}%")
            self.chart.ax.clear(); self.chart.ax.plot(result["history"]["Date"], result["history"]["Actual"], color="#60a5fa", label="Historical"); self.chart.ax.plot(result["forecast"]["Date"], result["forecast"]["Forecast"], color="#34d399", label="Forecast"); self.chart.ax.fill_between(result["forecast"]["Date"], result["forecast"]["Lower"], result["forecast"]["Upper"], color="#34d399", alpha=.18); self.chart.ax.legend(); self.chart.ax.set_title("Historical + forecast"); self.chart.apply_theme(); self.chart.canvas.draw_idle()
            table = result["forecast"]; self.results.setRowCount(len(table))
            for row in range(len(table)):
                for col, key in enumerate(["Date", "Forecast", "Lower", "Upper"]): self.results.setItem(row, col, QTableWidgetItem(str(table.iloc[row][key])))
            self.banner.setText(f"{result['model']} forecast ready • {self.horizon.value()} future periods.")
            self.banner.set_level("warning" if result["mape"] > 20 else "success")
        except Exception as exc: self.banner.setText(str(exc)); self.banner.set_level("error")