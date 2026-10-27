
"""Professional NLP analysis page for InsightIQ Analytics."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)

from widgets.chart_widget import ChartWidget
from widgets.data_table import DataTable
from widgets.notification import NotificationBanner
from services.nlp_service import NLPService


class NLPPage(QWidget):
    def __init__(self, data_service, parent=None):
        super().__init__(parent)

        self.data_service = data_service
        self.service = NLPService()

        self.setObjectName("nlpPage")
        self.setStyleSheet("""
            QWidget#nlpPage {
                background: #F7F8FC;
                color: #292544;
                font-family: "Segoe UI";
            }
            QLabel#pageTitle {
                font-size: 25px;
                font-weight: 700;
                color: #292544;
            }
            QLabel#subtitle {
                font-size: 12px;
                color: #77758D;
            }
            QLabel#sectionTitle {
                font-size: 14px;
                font-weight: 700;
                color: #383052;
            }
            QLabel#metricValue {
                font-size: 23px;
                font-weight: 700;
                color: #7357C8;
            }
            QLabel#metricLabel {
                font-size: 11px;
                color: #77758D;
            }
            QFrame#panel, QFrame#metricCard {
                background: white;
                border: 1px solid #E8E5F1;
                border-radius: 12px;
            }
            QComboBox {
                background: white;
                color: #302B4D;
                border: 1px solid #DDD8EE;
                border-radius: 7px;
                padding: 9px;
                min-width: 140px;
            }
            QPushButton#analyzeButton {
                background: #7357C8;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton#analyzeButton:hover {
                background: #6245B5;
            }
            QPushButton#analyzeButton:disabled {
                background: #C9C2DE;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #F0EDF7;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C8BDE7;
                min-height: 25px;
                border-radius: 4px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("nlpContent")
        content.setStyleSheet(
            "QWidget#nlpContent { background: #F7F8FC; }"
        )
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(26, 24, 26, 28)
        root.setSpacing(16)

        title = QLabel("Text & Sentiment Analysis")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Analyze text sentiment and discover frequently used words."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        controls = self._panel("Analysis settings")
        controls_layout = controls.layout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Text column"))

        self.column = QComboBox()
        self.column.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        row.addWidget(self.column, 1)

        self.run_button = QPushButton("Analyze text")
        self.run_button.setObjectName("analyzeButton")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.clicked.connect(self.analyze)
        row.addWidget(self.run_button)

        controls_layout.addLayout(row)
        root.addWidget(controls)

        self.banner = NotificationBanner(
            "Choose a text column and select Analyze text."
        )
        root.addWidget(self.banner)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)

        self.total_label = self._add_metric(
            metrics, "TEXT RECORDS"
        )
        self.positive_label = self._add_metric(
            metrics, "POSITIVE"
        )
        self.negative_label = self._add_metric(
            metrics, "NEGATIVE"
        )
        self.neutral_label = self._add_metric(
            metrics, "NEUTRAL"
        )

        root.addLayout(metrics)

        charts = QHBoxLayout()
        charts.setSpacing(14)

        sentiment_panel = self._panel("Sentiment distribution")
        self.chart = ChartWidget()
        self.chart.setMinimumHeight(280)
        sentiment_panel.layout().addWidget(self.chart)
        charts.addWidget(sentiment_panel, 1)

        keyword_panel = self._panel("Top keywords")
        self.keywords_chart = ChartWidget()
        self.keywords_chart.setMinimumHeight(280)
        keyword_panel.layout().addWidget(self.keywords_chart)
        charts.addWidget(keyword_panel, 1)

        root.addLayout(charts)

        table_panel = self._panel("Text analysis results")
        self.table = DataTable()
        self.table.setMinimumHeight(260)
        table_panel.layout().addWidget(self.table)
        root.addWidget(table_panel)

        root.addStretch()

        self.refresh_fields()
        self.analyze()

    @staticmethod
    def _panel(title_text):
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(12)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        return panel

    @staticmethod
    def _add_metric(layout, label_text):
        card = QFrame()
        card.setObjectName("metricCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 13, 14, 13)

        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        card_layout.addWidget(label)

        value = QLabel("—")
        value.setObjectName("metricValue")
        card_layout.addWidget(value)

        layout.addWidget(card, 1)
        return value

    def refresh_fields(self):
        self.column.clear()

        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self.column.addItem("No dataset loaded")
            self.run_button.setEnabled(False)
            return

        text_columns = data.select_dtypes(
            include=["object", "string", "category"]
        ).columns.tolist()

        self.column.addItems([str(c) for c in text_columns])
        self.run_button.setEnabled(bool(text_columns))

        if not text_columns:
            self.banner.setText(
                "No text columns found in the current dataset."
            )
            self.banner.set_level("error")

    def analyze(self):
        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self._show_error("Please load a dataset first.")
            return

        column = self.column.currentText()

        if not column or column == "No dataset loaded":
            self._show_error(
                "No text column is available in this dataset."
            )
            return

        self.run_button.setEnabled(False)
        self.run_button.setText("Analyzing...")

        try:
            result = self.service.analyze(data, column)

            counts = result.get("counts", {})
            keywords = result.get("keywords", [])
            rows = result.get("rows", [])

            self._update_metrics(counts, len(data))
            self._draw_sentiment(counts)
            self._draw_keywords(keywords)
            self.table.set_frame(rows)

            if keywords:
                top_words = ", ".join(
                    f"{word} ({count})"
                    for word, count in keywords[:5]
                )
                self.banner.setText(
                    f"Analysis complete. Top words: {top_words}"
                )
            else:
                self.banner.setText(
                    "Analysis complete. No frequent keywords found."
                )

            self.banner.set_level("success")

        except Exception as exc:
            self._show_error(str(exc))

        finally:
            self.run_button.setEnabled(
                self.column.count() > 0
                and self.column.currentText() != "No dataset loaded"
            )
            self.run_button.setText("Analyze text")

    def _update_metrics(self, counts, total_rows):
        normalized = {
            str(key).lower(): int(value)
            for key, value in counts.items()
        }

        positive = sum(
            v for k, v in normalized.items() if "positive" in k
        )
        negative = sum(
            v for k, v in normalized.items() if "negative" in k
        )
        neutral = sum(
            v for k, v in normalized.items() if "neutral" in k
        )

        self.total_label.setText(f"{total_rows:,}")
        self.positive_label.setText(f"{positive:,}")
        self.negative_label.setText(f"{negative:,}")
        self.neutral_label.setText(f"{neutral:,}")

    def _draw_sentiment(self, counts):
        ax = self.chart.ax
        ax.clear()

        labels = list(counts.keys())
        values = list(counts.values())
        colors = []

        for label in labels:
            name = str(label).lower()
            if "positive" in name:
                colors.append("#7C6AD8")
            elif "negative" in name:
                colors.append("#E58B9A")
            else:
                colors.append("#A9A2C4")

        if labels:
            bars = ax.bar(
                labels, values, color=colors, width=0.58, zorder=3
            )
            ax.bar_label(
                bars, padding=4, fontsize=9, color="#57516E"
            )
            ax.set_ylabel("Records")
            ax.grid(axis="y", linestyle="--", alpha=0.2)
            ax.set_axisbelow(True)
        else:
            ax.text(
                0.5, 0.5, "No sentiment data",
                ha="center", va="center",
                transform=ax.transAxes,
            )

        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=8)

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

        self.chart.apply_theme()
        self.chart.canvas.draw_idle()

    def _draw_keywords(self, keywords):
        ax = self.keywords_chart.ax
        ax.clear()

        top_words = keywords[:10]

        if not top_words:
            ax.text(
                0.5, 0.5, "No keywords available",
                ha="center", va="center",
                transform=ax.transAxes,
            )
        else:
            words = [str(word) for word, _ in top_words][::-1]
            values = [int(count) for _, count in top_words][::-1]

            bars = ax.barh(
                words, values, color="#A18BE6", height=0.62
            )
            ax.bar_label(
                bars, padding=4, fontsize=8, color="#57516E"
            )
            ax.tick_params(axis="y", labelsize=8)
            ax.tick_params(axis="x", labelsize=8)
            ax.grid(axis="x", linestyle="--", alpha=0.2)
            ax.set_axisbelow(True)

        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

        self.keywords_chart.apply_theme()
        self.keywords_chart.canvas.draw_idle()

    def _show_error(self, message):
        self.banner.setText(f"NLP analysis: {message}")
        self.banner.set_level("error")

        for label in (
            self.total_label,
            self.positive_label,
            self.negative_label,
            self.neutral_label,
        ):
            label.setText("—")
