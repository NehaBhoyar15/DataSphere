from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 4), facecolor="#111827")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.canvas)
        self.apply_theme()

    def apply_theme(self):
        self.ax.set_facecolor("#111827")
        self.ax.tick_params(colors="#cbd5e1")
        for spine in self.ax.spines.values():
            spine.set_color("#334155")
        self.canvas.draw_idle()

    def clear(self, message="Select controls and click Refresh chart"):
        self.ax.clear()
        self.ax.set_facecolor("#111827")
        self.ax.text(.5, .5, message, color="#94a3b8", ha="center", va="center")
        self.ax.set_axis_off()
        self.canvas.draw_idle()