 
"""User profile card and MySQL-backed profile editor."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDialogButtonBox
)


class EditProfileDialog(QDialog):
    def __init__(self, username, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Profile")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit(username)
        self.email_input = QLineEdit(email)

        form.addRow("Full name:", self.name_input)
        form.addRow("Email address:", self.email_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Missing name", "Enter your name.")
            return

        email = self.email_input.text().strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(
                self, "Invalid email", "Enter a valid email address."
            )
            return

        self.accept()


class UserProfileCard(QFrame):
    edit_requested = pyqtSignal()

    def __init__(
        self, user_id=1, username="Admin",
        email="admin@aianalytics.com", parent=None
    ):
        super().__init__(parent)

        self.user_id = str(user_id)
        self.username = username
        self.email = email

        self.setObjectName("userProfileCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(150)

        self.setStyleSheet("""
            QFrame#userProfileCard {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
            }
            QLabel { background: transparent; border: none; }
            QLabel#avatar {
                background: #E8F0FE;
                color: #285DB5;
                border-radius: 27px;
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#profileName {
                color: #172B4D;
                font-size: 17px;
                font-weight: bold;
            }
            QLabel#subtitle, QLabel#fieldLabel {
                color: #64748B;
                font-size: 11px;
            }
            QLabel#fieldLabel { font-weight: bold; }
            QLabel#fieldValue {
                color: #1E293B;
                font-size: 12px;
            }
            QPushButton {
                background: #EFF6FF;
                color: #2563EB;
                border: 1px solid #DBEAFE;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #DBEAFE; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 15, 18, 15)
        root.setSpacing(14)

        top = QHBoxLayout()
        self.avatar = QLabel()
        self.avatar.setObjectName("avatar")
        self.avatar.setFixedSize(54, 54)
        self.avatar.setAlignment(Qt.AlignCenter)

        identity = QVBoxLayout()
        self.name_label = QLabel()
        self.name_label.setObjectName("profileName")
        self.subtitle_label = QLabel("InsightIQ Analytics")
        self.subtitle_label.setObjectName("subtitle")
        identity.addWidget(self.name_label)
        identity.addWidget(self.subtitle_label)

        top.addWidget(self.avatar)
        top.addLayout(identity, 1)

        self.edit_button = QPushButton("Edit Profile")
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        top.addWidget(self.edit_button, 0, Qt.AlignTop)
        root.addLayout(top)

        details = QHBoxLayout()
        self.id_value = self._add_detail(details, "USER ID", "")
        self.email_value = self._add_detail(details, "EMAIL ADDRESS", "")
        root.addLayout(details)

        self.set_profile(self.user_id, self.username, self.email)

    def _add_detail(self, layout, heading, value):
        column = QVBoxLayout()
        label = QLabel(heading)
        label.setObjectName("fieldLabel")
        value_label = QLabel(value)
        value_label.setObjectName("fieldValue")
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        column.addWidget(label)
        column.addWidget(value_label)
        layout.addLayout(column, 1)
        return value_label

    def set_profile(self, user_id, username, email):
        self.user_id = str(user_id)
        self.username = str(username)
        self.email = str(email)

        self.name_label.setText(self.username)
        self.id_value.setText(self.user_id)
        self.email_value.setText(self.email)

        words = self.username.strip().split()
        self.avatar.setText(
            "".join(word[0] for word in words[:2]).upper() or "U"
        )

