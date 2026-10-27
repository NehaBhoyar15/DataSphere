
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt


class KPICard(QFrame):
    def __init__(self, label, value="—", accent="#B9A5EB", parent=None):
        super().__init__(parent)

        self.setObjectName("kpiCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(112)

        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FBF9FF,
                    stop: 0.55 #F5F0FE,
                    stop: 1 #F0EBFC
                );
                border: 1px solid #E8DFF8;
                border-left: 4px solid {accent};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 14, 16)
        layout.setSpacing(8)

        self.label = QLabel(label.upper())
        self.label.setStyleSheet("""
            color: #817494;
            font-size: 9pt;
            font-weight: 600;
            background: transparent;
            border: none;
        """)

        self.value = QLabel(str(value))
        self.value.setStyleSheet("""
            color: #403354;
            font-size: 23pt;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        self.value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addStretch()

    def set_value(self, value):
        self.value.setText(str(value))
