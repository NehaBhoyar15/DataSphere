
"""Main application window for InsightIQ Analytics."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QMessageBox,
)

from ui.sidebar import Sidebar
from ui.executive_dashboard import ExecutiveDashboard as DashboardPage
from ui.data_view import DataPage
from ui.chart_view import ChartsPage
from ui.ml_view import MLPage
from ui.clustering_view import ClusteringPage
from ui.nlp_view import NLPPage
from ui.ai_assistant import AIAssistantPage
from ui.forecast_view import ForecastPage
from ui.settings_view import SettingsPage
from services.data_service import DataService
from services.user_service import UserService
from widgets.user_profile import EditProfileDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("InsightIQ Analytics")
        self.resize(1440, 920)
        self.setMinimumSize(1100, 700)
        self.setAcceptDrops(True)

        self.data_service = DataService()
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()

        self.pages = {
            "Dashboard": DashboardPage(self.data_service),
            "Data": DataPage(self.data_service),
            "Charts": ChartsPage(self.data_service),
            "ML": MLPage(self.data_service),
            "Clustering": ClusteringPage(self.data_service),
            "NLP": NLPPage(self.data_service),
            "AI Assistant": AIAssistantPage(self.data_service),
            "Forecasting": ForecastPage(self.data_service),
            "Settings": SettingsPage(),
        }

        self.page_map = self.pages

        # Load the selected user's profile from MySQL.
        self.user_service = UserService()
        self.profile_user_id = 1

        dashboard_page = self.pages.get("Dashboard")
        if dashboard_page and hasattr(dashboard_page, "user_profile"):
            profile = self.user_service.get_user(self.profile_user_id)

            if profile:
                dashboard_page.user_profile.set_profile(
                    profile["user_id"],
                    profile["username"],
                    profile["email"],
                )

            dashboard_page.user_profile.edit_requested.connect(
                self.edit_user_profile
            )


        for page in self.pages.values():
            self.stack.addWidget(page)

        self.sidebar.page_selected.connect(self.navigate)
        self.sidebar.toggle_requested.connect(
    lambda collapsed: self.stack.setMinimumWidth(0)
)

        data_page = self.pages["Data"]
        if hasattr(data_page, "data_changed"):
            data_page.data_changed.connect(self.refresh_pages)

        settings_page = self.pages["Settings"]
        if hasattr(settings_page, "theme_changed"):
            settings_page.theme_changed.connect(self.apply_theme)

        container = QWidget()
        container.setObjectName("appContainer")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(container)

        self.statusBar().showMessage("InsightIQ Analytics is ready")
        self.apply_theme("light")
        self.navigate("Dashboard")


    def edit_user_profile(self):
        profile = self.user_service.get_user(self.profile_user_id)

        if not profile:
            QMessageBox.warning(
                self,
                "User Profile",
                "Could not load this user's profile from MySQL.",
            )
            return

        dialog = EditProfileDialog(
            profile["username"],
            profile["email"],
            self,
        )

        if dialog.exec_() != dialog.Accepted:
            return

        success, message = self.user_service.update_user(
            self.profile_user_id,
            dialog.name_input.text(),
            dialog.email_input.text(),
        )

        if success:
            dashboard = self.pages.get("Dashboard")
            if dashboard and hasattr(dashboard, "user_profile"):
                updated = self.user_service.get_user(
                    self.profile_user_id
                )
                if updated:
                    dashboard.user_profile.set_profile(
                        updated["user_id"],
                        updated["username"],
                        updated["email"],
                    )

            QMessageBox.information(
                self, "User Profile", message
            )
        else:
            QMessageBox.warning(
                self, "Could not save profile", message
            )

    def navigate(self, name):
        page = self.pages.get(name)

        if page is None:
            return

        self.stack.setCurrentWidget(page)
        self.sidebar.select(name)
        self.statusBar().showMessage(
            f"{name} workspace",
            2500,
        )

    def refresh_pages(self, *args):
        for name in (
            "Dashboard",
            "Charts",
            "ML",
            "NLP",
            "Forecasting",
        ):
            page = self.pages.get(name)

            if page and hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass

    def apply_theme(self, theme="light"):
        self.setStyleSheet(self.stylesheet(theme))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(
                url.toLocalFile().lower().endswith(
                    (".csv", ".xlsx", ".xls")
                )
                for url in urls
            ):
                event.acceptProposedAction()
                return

        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()

        for url in urls:
            path = url.toLocalFile()

            if path.lower().endswith((".csv", ".xlsx", ".xls")):
                data_page = self.pages.get("Data")
                self.navigate("Data")

                # Use the data page's existing file-opening method.
                for method_name in (
                    "open_file",
                    "load_file",
                    "import_file",
                ):
                    method = getattr(data_page, method_name, None)
                    if callable(method):
                        method(path)
                        event.acceptProposedAction()
                        return

                QMessageBox.information(
                    self,
                    "Open dataset",
                    "Please use the Data page to import this file.",
                )
                return

        event.ignore()

    @staticmethod
    def stylesheet(theme="light"):
        if theme == "light":
            return """
                QMainWindow, QWidget#appContainer {
                    background-color: #F6F7FB;
                    color: #25243A;
                }

                QStatusBar {
                    background-color: #FFFFFF;
                    color: #77758A;
                    border-top: 1px solid #E8E8F0;
                }

                QToolTip {
                    background-color: #292544;
                    color: white;
                    border: 1px solid #7566B5;
                    padding: 5px;
                }

                QScrollArea {
                    border: none;
                    background: transparent;
                }

                QLineEdit, QTextEdit, QPlainTextEdit,
                QComboBox, QSpinBox, QDoubleSpinBox {
                    background-color: #FFFFFF;
                    color: #29263D;
                    border: 1px solid #DEDFEB;
                    border-radius: 7px;
                    padding: 7px;
                    selection-background-color: #DCD4FF;
                    selection-color: #292544;
                }

                QTableWidget, QTableView {
                    background-color: #FFFFFF;
                    alternate-background-color: #F7F6FC;
                    color: #29263D;
                    gridline-color: #EAE8F2;
                    border: 1px solid #E7E5EF;
                    border-radius: 8px;
                }

                QHeaderView::section {
                    background-color: #F0EDFA;
                    color: #514878;
                    border: none;
                    padding: 8px;
                    font-weight: 600;
                }

                QProgressBar {
                    background-color: #EAE7F3;
                    color: #514878;
                    border: none;
                    border-radius: 5px;
                    text-align: center;
                    min-height: 10px;
                }

                QProgressBar::chunk {
                    background-color: #8067D8;
                    border-radius: 5px;
                }

                QScrollBar:vertical {
                    background: transparent;
                    width: 9px;
                    margin: 2px;
                }

                QScrollBar::handle:vertical {
                    background: #D0CBE1;
                    border-radius: 4px;
                    min-height: 25px;
                }

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                }

                QPushButton {
                    border-radius: 7px;
                }
            """

        return """
            QMainWindow, QWidget#appContainer {
                background-color: #111827;
                color: #E5E7EB;
            }

            QStatusBar {
                background-color: #111827;
                color: #9CA3AF;
                border-top: 1px solid #273449;
            }

            QToolTip {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #475569;
                padding: 5px;
            }

            QLineEdit, QTextEdit, QPlainTextEdit,
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 7px;
                padding: 7px;
            }

            QTableWidget, QTableView {
                background-color: #1F2937;
                alternate-background-color: #263244;
                color: #E5E7EB;
                gridline-color: #374151;
                border: 1px solid #374151;
                border-radius: 8px;
            }

            QHeaderView::section {
                background-color: #273449;
                color: #D1D5DB;
                border: none;
                padding: 8px;
            }

            QProgressBar {
                background-color: #374151;
                color: white;
                border: none;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #60A5FA;
                border-radius: 5px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 9px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #4B5563;
                border-radius: 4px;
                min-height: 25px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
