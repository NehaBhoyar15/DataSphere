
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, Qt


class Sidebar(QFrame):
    page_selected = pyqtSignal(str)
    toggle_requested = pyqtSignal(bool)

    PAGES = [
        ("📊", "Dashboard"),
        ("📁", "Data"),
        ("📈", "Charts"),
        ("🤖", "ML"),
        ("🔗", "Clustering"),
        ("💬", "NLP"),
        ("✨", "AI Assistant"),
        ("🔮", "Forecasting"),
        ("⚙️", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.collapsed = False
        self.setObjectName("sidebar")
        self.setMinimumWidth(205)
        self.setMaximumWidth(220)
        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FBF9FF,
                    stop:1 #F1EAFD
                );
                border-right: 1px solid #E3D9F7;
            }

            QLabel#brand {
                color: #403354;
                font-size: 25px;
                font-weight: 800;
                background: transparent;
            }

            QLabel#subtitle, QLabel#sectionLabel {
                color: #9182AC;
                font-size: 10px;
                font-weight: 700;
                background: transparent;
            }

            QFrame#divider {
                background: #E4DAF5;
                border: none;
                max-height: 1px;
                min-height: 1px;
            }

            QPushButton#toggleButton {
                background: #EEE7FC;
                color: #6849B7;
                border: 1px solid #E2D5F8;
                border-radius: 8px;
                font-size: 20px;
                font-weight: 700;
                padding: 4px;
            }

            QPushButton#toggleButton:hover {
                background: #E4D8FA;
            }

            QPushButton#navButton {
                background: transparent;
                color: #514364;
                border: 1px solid transparent;
                border-radius: 9px;
                text-align: left;
                padding: 9px 10px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#navButton:hover {
                background: #EEE7FC;
                color: #6244B5;
                border: 1px solid #E5DAFA;
            }

            QPushButton#navButton:checked {
                background: #E3D8FB;
                color: #5937B5;
                border: 1px solid #D3C2F5;
                font-weight: 700;
            }

            QLabel#status {
                color: #6749AD;
                background: #EAE2FB;
                border: 1px solid #DCCEF7;
                border-radius: 8px;
                padding: 9px 5px;
                font-size: 10px;
                font-weight: 700;
            }

            QLabel#footer {
                color: #9284A8;
                font-size: 10px;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(7)

        toggle_row = QHBoxLayout()
        self.toggle_button = QPushButton("‹")
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setFixedSize(36, 34)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setToolTip("Collapse sidebar")
        self.toggle_button.clicked.connect(self.toggle_sidebar)

        toggle_row.addStretch()
        toggle_row.addWidget(self.toggle_button)
        layout.addLayout(toggle_row)

        self.brand = QLabel("InsightIQ")
        self.brand.setObjectName("brand")
        layout.addWidget(self.brand)

        self.subtitle = QLabel("ANALYTICS STUDIO")
        self.subtitle.setObjectName("subtitle")
        layout.addWidget(self.subtitle)

        self.divider = QFrame()
        self.divider.setObjectName("divider")
        layout.addWidget(self.divider)

        self.section = QLabel("WORKSPACE")
        self.section.setObjectName("sectionLabel")
        layout.addWidget(self.section)

        self.buttons = {}

        for icon, name in self.PAGES:
            button = QPushButton(f"{icon}   {name}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(42)
            button.setMaximumHeight(46)
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )
            button.setToolTip(name)
            button.clicked.connect(
                lambda checked=False, page=name:
                self.page_selected.emit(page)
            )

            layout.addWidget(button)
            self.buttons[name] = button

        layout.addStretch(1)

        self.status = QLabel("●  WORKSPACE READY")
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        self.footer = QLabel("Your data. Your insights.")
        self.footer.setObjectName("footer")
        self.footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.footer)

    def toggle_sidebar(self):
        self.set_collapsed(not self.collapsed)

    def set_collapsed(self, collapsed):
        self.collapsed = collapsed

        if collapsed:
            self.setFixedWidth(76)
            self.toggle_button.setText("›")
            self.toggle_button.setToolTip("Expand sidebar")
        else:
            self.setMinimumWidth(205)
            self.setMaximumWidth(220)
            self.toggle_button.setText("‹")
            self.toggle_button.setToolTip("Collapse sidebar")

        self.brand.setVisible(not collapsed)
        self.subtitle.setVisible(not collapsed)
        self.section.setVisible(not collapsed)
        self.status.setVisible(not collapsed)
        self.footer.setVisible(not collapsed)

        for icon, name in self.PAGES:
            button = self.buttons[name]

            if collapsed:
                button.setText(icon)
                button.setStyleSheet("""
                    QPushButton#navButton {
                        text-align: center;
                        padding: 6px 2px;
                        font-size: 23px;
                    }
                """)
            else:
                button.setText(f"{icon}   {name}")
                button.setStyleSheet("")

            button.setToolTip(name)

        self.toggle_requested.emit(collapsed)

    def select(self, name):
        for page, button in self.buttons.items():
            button.setChecked(page == name)
