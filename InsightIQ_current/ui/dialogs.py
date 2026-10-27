from PyQt5.QtWidgets import (QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox,
                              QLabel, QVBoxLayout)


class DatabaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database connection")
        self.setMinimumWidth(390)
        layout = QVBoxLayout(self)
        info = QLabel("Connection settings are kept in this UI as an adapter for Person 2's database layer.")
        info.setWordWrap(True)
        layout.addWidget(info)
        form = QFormLayout()
        self.db_type = QComboBox(); self.db_type.addItems(["SQLite", "PostgreSQL", "MySQL"])
        self.host = QLineEdit("localhost")
        self.port = QLineEdit("5432")
        self.username = QLineEdit()
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        self.database = QLineEdit("analytics")
        for label, widget in [("Database type", self.db_type), ("Host", self.host), ("Port", self.port),
                              ("Username", self.username), ("Password", self.password), ("Database name", self.database)]:
            form.addRow(label, widget)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def config(self):
        return {"type": self.db_type.currentText(), "host": self.host.text(),
                "port": self.port.text(), "username": self.username.text(),
                "database": self.database.text()}