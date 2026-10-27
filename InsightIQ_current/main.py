
"""Entry point for InsightIQ Analytics."""

import sys
import math
import random

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QLinearGradient,
    QRadialGradient,
    QPen,
)
from PyQt5.QtCore import Qt, QTimer

from ui.main_window import MainWindow


class InsightIQSplash(QSplashScreen):
    def __init__(self):
        self.canvas_width = 640
        self.canvas_height = 360

        pixmap = QPixmap(self.canvas_width, self.canvas_height)
        pixmap.fill(Qt.transparent)

        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.setFixedSize(self.canvas_width, self.canvas_height)

        self.frame = 0
        self.progress = 0

        random.seed(15)
        self.particles = [
            (
                random.randint(10, self.canvas_width - 10),
                random.randint(10, self.canvas_height - 10),
                random.randint(1, 3),
                random.uniform(0, math.pi * 2),
            )
            for _ in range(35)
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def animate(self):
        self.frame += 1
        self.progress = (self.progress + 1.4) % 101
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background gradient
        background = QLinearGradient(
            0, 0, self.canvas_width, self.canvas_height
        )
        background.setColorAt(0.0, QColor("#17112F"))
        background.setColorAt(0.5, QColor("#30205C"))
        background.setColorAt(1.0, QColor("#59418C"))

        painter.fillRect(self.rect(), background)

        # Soft central glow
        glow = QRadialGradient(320, 125, 230)
        glow.setColorAt(0.0, QColor(190, 160, 255, 65))
        glow.setColorAt(1.0, QColor(130, 90, 220, 0))
        painter.fillRect(self.rect(), glow)

        # Floating particles
        painter.setPen(Qt.NoPen)

        for x, y, radius, phase in self.particles:
            float_y = math.sin(
                self.frame * 0.035 + phase
            ) * 7

            alpha = int(
                45 + 65 * abs(
                    math.sin(self.frame * 0.025 + phase)
                )
            )

            painter.setBrush(QColor(224, 211, 255, alpha))
            painter.drawEllipse(
                int(x), int(y + float_y), radius, radius
            )

        # Glowing IQ logo
        pulse = 1 + 0.035 * math.sin(self.frame * 0.08)
        logo_size = int(72 * pulse)
        logo_x = (self.canvas_width - logo_size) // 2
        logo_y = 43

        painter.setBrush(QColor(190, 160, 255, 30))
        painter.drawRoundedRect(
            logo_x - 13,
            logo_y - 13,
            logo_size + 26,
            logo_size + 26,
            26,
            26,
        )

        logo_gradient = QLinearGradient(
            logo_x, logo_y,
            logo_x + logo_size, logo_y + logo_size,
        )
        logo_gradient.setColorAt(0.0, QColor("#C4B5FD"))
        logo_gradient.setColorAt(1.0, QColor("#8B5CF6"))

        painter.setBrush(logo_gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 130), 1))
        painter.drawRoundedRect(
            logo_x, logo_y, logo_size, logo_size, 19, 19
        )

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(
            logo_x, logo_y, logo_size, logo_size,
            Qt.AlignCenter, "IQ",
        )

        # Application name
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 25, QFont.Bold))
        painter.drawText(
            20, 150, self.canvas_width - 40, 45,
            Qt.AlignCenter, "InsightIQ Analytics",
        )

        # Tagline
        painter.setPen(QColor("#D8CCF5"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(
            20, 197, self.canvas_width - 40, 25,
            Qt.AlignCenter, "YOUR DATA. YOUR DISCOVERIES.",
        )

        # Progress track
        bar_x = 180
        bar_y = 270
        bar_width = 280
        bar_height = 5

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 40))
        painter.drawRoundedRect(
            bar_x, bar_y, bar_width, bar_height, 3, 3
        )

        # Animated progress fill
        filled_width = int(
            bar_width * self.progress / 100
        )

        progress_gradient = QLinearGradient(
            bar_x, bar_y, bar_x + bar_width, bar_y
        )
        progress_gradient.setColorAt(0.0, QColor("#A78BFA"))
        progress_gradient.setColorAt(1.0, QColor("#F0ABFC"))

        painter.setBrush(progress_gradient)
        painter.drawRoundedRect(
            bar_x, bar_y, filled_width, bar_height, 3, 3
        )

        # Footer
        painter.setPen(QColor("#BBA9E5"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(
            20, 300, self.canvas_width - 40, 22,
            Qt.AlignCenter, "INITIALIZING ANALYTICS WORKSPACE",
        )

        painter.end()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("InsightIQ Analytics")
    app.setOrganizationName("Analytics Studio")

    splash = InsightIQSplash()
    splash.show()
    app.processEvents()

    try:
        window = MainWindow()
        window.show()
        splash.finish(window)
        splash.timer.stop()
    except Exception:
        splash.timer.stop()
        splash.close()
        raise

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())