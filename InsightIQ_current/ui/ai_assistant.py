"""AI Data Assistant page for InsightIQ Analytics."""

from html import escape

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QShortcut,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.ai_service import AIService
from widgets.notification import NotificationBanner


class AIAssistantPage(QWidget):
    """Interactive local data-analysis assistant."""

    EXAMPLE_PROMPTS = [
        "Give me a complete summary of my dataset",
        "What is the average revenue?",
        "Which region generated the highest revenue?",
        "Which product sold the most units?",
        "Show monthly revenue trends",
        "Compare regions by revenue",
        "Find missing values",
        "Find duplicate rows",
        "Show numeric correlations",
        "List column names",
    ]

    def __init__(self, data_service, parent=None):
        super().__init__(parent)

        self.data_service = data_service
        self.service = AIService()
        self.last_response = {}
        self.question_count = 0

        self.setObjectName("aiAssistantPage")
        self._build_ui()
        self._connect_shortcuts()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(10)

        title = QLabel("AI Data Assistant")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Ask questions about your dataset and discover useful insights."
        )
        subtitle.setObjectName("panelSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        self.banner = NotificationBanner(
            "Ready to analyse your data.", level="info"
        )
        root.addWidget(self.banner)

        chat_header = QHBoxLayout()
        chat_title = QLabel("Conversation")
        chat_title.setObjectName("panelTitle")
        chat_header.addWidget(chat_title)
        chat_header.addStretch()

        self.message_count = QLabel("0 questions")
        self.message_count.setObjectName("panelSubtitle")
        chat_header.addWidget(self.message_count)
        root.addLayout(chat_header)

        self.history = QTextEdit()
        self.history.setObjectName("aiConversationHistory")
        self.history.setReadOnly(True)
        self.history.setAcceptRichText(True)
        self.history.setPlaceholderText(
            "Your questions and analysis results will appear here."
        )
        self.history.setMinimumHeight(150)
        root.addWidget(self.history, 3)

        examples_header = QLabel("Try asking")
        examples_header.setObjectName("panelTitle")
        root.addWidget(examples_header)

        examples = QHBoxLayout()
        examples.setSpacing(8)

        # Keep the row compact while still providing useful examples.
        for prompt in self.EXAMPLE_PROMPTS[:4]:
            button = QPushButton(prompt)
            button.setMinimumHeight(32)
            button.setToolTip(prompt)
            button.clicked.connect(
                lambda checked=False, text=prompt: self._use_prompt(text)
            )
            examples.addWidget(button)

        root.addLayout(examples)

        input_title = QLabel("Ask your question")
        input_title.setObjectName("panelTitle")
        root.addWidget(input_title)

        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(8)

        self.input = QTextEdit()
        self.input.setObjectName("aiQuestionInput")
        self.input.setPlaceholderText(
            "Example: Which region generated the highest revenue?"
        )
        self.input.setFixedHeight(68)
        prompt_row.addWidget(self.input, 1)

        self.send_button = QPushButton("Analyse")
        self.send_button.setMinimumWidth(100)
        self.send_button.setMinimumHeight(42)
        self.send_button.clicked.connect(self.ask)
        prompt_row.addWidget(self.send_button)

        self.clear_button = QPushButton("Clear chat")
        self.clear_button.setMinimumHeight(42)
        self.clear_button.clicked.connect(self.clear_chat)
        prompt_row.addWidget(self.clear_button)

        root.addLayout(prompt_row)

        keyboard_hint = QLabel(
            "Tip: Press Ctrl + Enter to analyse your question."
        )
        keyboard_hint.setObjectName("panelSubtitle")
        root.addWidget(keyboard_hint)

        sql_header = QHBoxLayout()
        sql_title = QLabel("Generated SQL Preview")
        sql_title.setObjectName("panelTitle")
        sql_header.addWidget(sql_title)
        sql_header.addStretch()

        self.copy_sql_button = QPushButton("Copy SQL")
        self.copy_sql_button.clicked.connect(self.copy_sql)
        sql_header.addWidget(self.copy_sql_button)
        root.addLayout(sql_header)

        self.sql = QTextEdit()
        self.sql.setObjectName("aiSqlPreview")
        self.sql.setReadOnly(True)
        self.sql.setPlaceholderText(
            "SQL preview will appear here when available."
        )
        self.sql.setFixedHeight(75)
        root.addWidget(self.sql)

        sql_note = QLabel(
            "SQL is shown as a preview only. Generated SQL is not executed "
            "against your database."
        )
        sql_note.setObjectName("panelSubtitle")
        sql_note.setWordWrap(True)
        root.addWidget(sql_note)

        result_header = QHBoxLayout()
        result_title = QLabel("Analysis Results")
        result_title.setObjectName("panelTitle")
        result_header.addWidget(result_title)
        result_header.addStretch()

        self.result_count = QLabel("0 results")
        self.result_count.setObjectName("panelSubtitle")
        result_header.addWidget(self.result_count)
        root.addLayout(result_header)

        self.result = QTableWidget(0, 2)
        self.result.setObjectName("aiResultsTable")
        self.result.setHorizontalHeaderLabels(["Metric", "Value"])
        self.result.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.result.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.result.verticalHeader().setVisible(False)
        self.result.setAlternatingRowColors(True)
        self.result.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result.setMinimumHeight(100)
        self.result.setMaximumHeight(220)
        root.addWidget(self.result, 1)

    def _connect_shortcuts(self):
        self.submit_shortcut = QShortcut(
            QKeySequence("Ctrl+Return"), self.input
        )
        self.submit_shortcut.activated.connect(self.ask)

        self.submit_shortcut_alt = QShortcut(
            QKeySequence("Ctrl+Enter"), self.input
        )
        self.submit_shortcut_alt.activated.connect(self.ask)

    def _use_prompt(self, prompt):
        self.input.setPlainText(prompt)
        self.input.setFocus()

    def _get_dataframe(self):
        """Return the current DataService DataFrame."""
        frame = getattr(self.data_service, "data", None)
        if frame is None:
            return None
        return frame

    def ask(self):
        """Analyse the current dataset and display the response."""
        question = self.input.toPlainText().strip()

        if not question:
            self.banner.setText("Please enter a question first.")
            self.banner.set_level("warning")
            self.input.setFocus()
            return

        frame = self._get_dataframe()
        if frame is None:
            self.banner.setText(
                "No dataset is loaded. Load a dataset and try again."
            )
            self.banner.set_level("warning")
            return

        if not self.send_button.isEnabled():
            return

        self.send_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.send_button.setText("Analysing...")
        self.banner.setText("Analysing your question...")
        self.banner.set_level("info")
        QApplication.processEvents()

        try:
            response = self.service.ask(question, frame)
            if not isinstance(response, dict):
                raise TypeError(
                    "AIService.ask() must return a dictionary."
                )

            answer = str(
                response.get("answer", "No answer was returned.")
            )
            sql = str(response.get("sql", ""))

            self.last_response = response
            self._append_conversation(question, answer, response)
            self.sql.setPlainText(sql)
            self._populate_results(response, frame)

            self.question_count += 1
            self._update_question_count()
            self.input.clear()

            self.banner.setText("Analysis completed successfully.")
            self.banner.set_level("success")

        except Exception as exc:
            self.banner.setText(
                f"Could not analyse the question: {exc}"
            )
            self.banner.set_level("error")

        finally:
            self.send_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.send_button.setText("Analyse")

    def _append_conversation(self, question, answer, response):
        """Append safely escaped question and answer to conversation history."""
        safe_question = escape(question).replace("\n", "<br>")
        safe_answer = escape(answer).replace("\n", "<br>")
        mode = escape(str(response.get("mode", "Local analysis")))

        html = (
            '<div style="margin: 8px 0;">'
            '<p style="margin-bottom: 4px;">'
            '<b style="color:#6556D9;">You</b></p>'
            f'<p style="margin-top: 0;">{safe_question}</p>'
            '<p style="margin-bottom: 4px;">'
            '<b style="color:#159D9A;">InsightIQ Assistant</b></p>'
            f'<p style="margin-top: 0;">{safe_answer}</p>'
            f'<p style="color:#64748B; font-size:11px;">Mode: {mode}</p>'
            '<hr></div>'
        )

        self.history.append(html)
        scrollbar = self.history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _populate_results(self, response, frame):
        """Display detailed metrics returned by AIService."""
        self.result.setRowCount(0)
        details = response.get("details", [])

        if isinstance(details, list):
            for item in details:
                if isinstance(item, dict):
                    metric = item.get("Metric", item.get("metric", "Result"))
                    value = item.get("Value", item.get("value", ""))
                    self.add_result(metric, value)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    self.add_result(item[0], item[1])

        if self.result.rowCount() == 0:
            self.add_result("Dataset rows", len(frame.index))
            self.add_result("Dataset columns", len(frame.columns))
            self.add_result("Missing cells", int(frame.isna().sum().sum()))
            self.add_result("Duplicate rows", int(frame.duplicated().sum()))

        count = self.result.rowCount()
        self.result_count.setText(
            f"{count} {'result' if count == 1 else 'results'}"
        )
        self.result.resizeRowsToContents()

    def add_result(self, metric, value):
        """Add one result row with safe display formatting."""
        row = self.result.rowCount()
        self.result.insertRow(row)

        metric_item = QTableWidgetItem(str(metric))
        value_item = QTableWidgetItem(self._format_value(value))

        metric_item.setFlags(metric_item.flags() & ~Qt.ItemIsEditable)
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)

        self.result.setItem(row, 0, metric_item)
        self.result.setItem(row, 1, value_item)

    @staticmethod
    def _format_value(value):
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:,.4f}".rstrip("0").rstrip(".")
        return str(value)

    def _update_question_count(self):
        count = self.question_count
        self.message_count.setText(
            f"{count} {'question' if count == 1 else 'questions'}"
        )

    def copy_sql(self):
        query = self.sql.toPlainText().strip()

        if not query:
            self.banner.setText("No SQL preview is available to copy.")
            self.banner.set_level("warning")
            return

        QApplication.clipboard().setText(query)
        self.banner.setText("SQL preview copied to clipboard.")
        self.banner.set_level("success")

    def clear_chat(self):
        self.history.clear()
        self.sql.clear()
        self.result.setRowCount(0)
        self.result_count.setText("0 results")
        self.question_count = 0
        self._update_question_count()
        self.last_response = {}

        self.banner.setText("Conversation cleared.")
        self.banner.set_level("success")
        self.input.setFocus()