
"""Professional notification banner for InsightIQ Analytics."""

from PyQt5.QtWidgets import QLabel


class NotificationBanner(QLabel):
    """Display compact status messages with level-based styling."""

    LEVEL_STYLES = {
        "info": {
            "background": "#EEF2FF",
            "foreground": "#3730A3",
            "border": "#C7D2FE",
        },
        "success": {
            "background": "#ECFDF5",
            "foreground": "#065F46",
            "border": "#A7F3D0",
        },
        "warning": {
            "background": "#FFFBEB",
            "foreground": "#92400E",
            "border": "#FDE68A",
        },
        "error": {
            "background": "#FEF2F2",
            "foreground": "#991B1B",
            "border": "#FECACA",
        },
    }

    def __init__(self, text="", level="info", parent=None):
        super().__init__(text, parent)

        self.setObjectName("notificationBanner")
        self.setWordWrap(True)
        self.setMinimumHeight(36)
        self.setMargin(0)
        self.set_level(level)

    def set_level(self, level):
        """Update the banner's appearance for the requested level."""
        level = str(level).strip().lower()

        if level not in self.LEVEL_STYLES:
            level = "info"

        self.level = level
        style = self.LEVEL_STYLES[level]

        self.setStyleSheet(
            f"""
            QLabel#notificationBanner {{
                background-color: {style["background"]};
                color: {style["foreground"]};
                border: 1px solid {style["border"]};
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            """
        )
