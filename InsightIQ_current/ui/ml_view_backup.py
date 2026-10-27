
"""Professional NLP analysis page for InsightIQ Analytics."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
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
                background-color: #F7F8FC;
                color: #24213A;
                font-family: "Segoe UI";
            }

            QLabel#pageTitle {
                color: #24213A;
                font-size: 25px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #77758D;
                font-size: 12px;
            }

            QLabel#sectionTitle {
                color: #302B4D;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#metricValue {
                color: #5B45B5;
                font-size: 23px;
                font-weight: 700;
            }

            QLabel#metricLabel {
                color: #77758D;
                font-size: 11px;
            }

            QFrame#panel, QFrame#metricCard {
                background-color: #FFFFFF;
                border: 1px solid #E9E6F3;
                border-radius: 12px;
            }

            QComboBox {
                background: #FFFFFF;
                color: #302B4D;
                border: 1px solid #DDD8EE;
                border-radius: 7px;
                padding: 9px 12px;
                min-width: 180px;
            }

            QComboBox:focus {
                border: 1px solid #8B78D6;
            }

            QPushButton#analyzeButton {
                background-color: #7357C8;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 20px;
                font-weight: 600;
            }

            QPushButton#analyzeButton:hover {
                background-color: #6245B5;
            }

            QPushButton#analyzeButton:disabled {
                background-color: #BDB4DA;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                background: #F0EDF7;
                width: 8px;
                margin: 2px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #C8BDE7;
                min-height: 30px;
                border-radius: 4px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Main page layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer_layout.addWidget(scroll)

        content = QWidget()
        content.setObjectName("nlpContent")
        content.setStyleSheet("QWidget#nlpContent { background: #F7F8FC; }")
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)

        # Page heading
        heading = QVBoxLayout()
        heading.setSpacing(5)

        title = QLabel("Text & Sentiment Analysis")
        title.setObjectName("pageTitle")
        heading.addWidget(title)

        subtitle = QLabel(
            "Understand sentiment and discover the most important "
            "words in your dataset."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        heading.addWidget(subtitle)

        root.addLayout(heading)

        # Controls panel
        controls_panel = QFrame()
        controls_panel.setObjectName("panel")

        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(18, 16, 18, 16)
        controls_layout.setSpacing(10)

        control_title = QLabel("Analysis settings")
        control_title.setObjectName("sectionTitle")
        controls_layout.addWidget(control_title)

        control_row = QHBoxLayout()
        control_row.setSpacing(12)

        column_label = QLabel("Text column")
        column_label.setStyleSheet(
            "color: #68647F; font-size: 12px; font-weight: 600;"
        )
        control_row.addWidget(column_label)

        self.column = QComboBox()
        self.column.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        control_row.addWidget(self.column, 1)

        self.run_button = QPushButton("Analyze text")
        self.run_button.setObjectName("analyzeButton")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.clicked.connect(self.analyze)
        control_row.addWidget(self.run_button)

        controls_layout.addLayout(control_row)
        root.addWidget(controls_panel)

        # Status / insights banner
        self.banner = NotificationBanner(
            "Choose a text column and select Analyze text."
        )
        root.addWidget(self.banner)

        # Summary metric cards
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)

        self.total_label = self._add_metric(
            metrics_row, "TEXT RECORDS", "—"
        )
        self.positive_label = self._add_metric(
            metrics_row, "POSITIVE", "—"
        )
        self.negative_label = self._add_metric(
            metrics_row, "NEGATIVE", "—"
        )
        self.neutral_label = self._add_metric(
            metrics_row, "NEUTRAL", "—"
        )

        root.addLayout(metrics_row)

        # Charts in two separate panels
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        sentiment_panel, sentiment_layout = self._create_panel(
            "Sentiment distribution",
            "Overview of positive, negative and neutral text."
        )
        self.chart = ChartWidget()
        self.chart.setMinimumHeight(270)
        self.chart.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        sentiment_layout.addWidget(self.chart, 1)
        charts_row.addWidget(sentiment_panel, 1)

        keyword_panel, keyword_layout = self._create_panel(
            "Key phrases & words",
            "Frequently occurring words found in your text."
        )
        self.keywords_chart = ChartWidget()
        self.keywords_chart.setMinimumHeight(270)
        self.keywords_chart.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        keyword_layout.addWidget(self.keywords_chart, 1)
        charts_row.addWidget(keyword_panel, 1)

        root.addLayout(charts_row)

        # Detailed results table below the charts
        table_panel, table_layout = self._create_panel(
            "Text analysis results",
            "Review the analyzed records and their available details."
        )

        self.table = DataTable()
        self.table.setMinimumHeight(260)
        self.table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        table_layout.addWidget(self.table, 1)

        root.addWidget(table_panel)
        root.addStretch(1)

        self.refresh_fields()
        self.analyze()

    @staticmethod
    def _create_panel(title_text, subtitle_text):
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(0)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(7)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(
            "color: #88849C; font-size: 11px;"
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        return panel, layout

    @staticmethod
    def _add_metric(layout, label_text, value_text):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setMinimumWidth(0)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 13, 15, 13)
        card_layout.setSpacing(5)

        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        card_layout.addWidget(label)

        value = QLabel(value_text)
        value.setObjectName("metricValue")
        card_layout.addWidget(value)

        layout.addWidget(card, 1)
        return value

    def refresh_fields(self):
        """Refresh available text columns from the current dataset."""
        self.column.clear()

        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self.column.addItem("No dataset loaded")
            self.run_button.setEnabled(False)
            return

        text_columns = list(
            data.select_dtypes(
                include=["object", "string", "category"]
            ).columns
        )

        self.column.addItems([str(c) for c in text_columns])
        self.run_button.setEnabled(bool(text_columns))

        if not text_columns:
            self.banner.setText(
                "No text columns found. Load a dataset containing "
                "text data to use NLP analysis."
            )
            self.banner.set_level("error")

    def analyze(self):
        """Run the existing local NLP analysis service."""
        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self._show_error("No dataset is loaded.")
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
                    f"Analysis complete · Top words: {top_words}"
                )
            else:
                self.banner.setText(
                    "Analysis complete. No frequent keywords were found."
                )

            self.banner.set_level("success")

        except Exception as exc:
            self._show_error(str(exc))

        finally:
            self.run_button.setEnabled(True)
            self.run_button.setText("Analyze text")

    def _update_metrics(self, counts, total_rows):
        """Update the summary cards using the NLP service result."""
        normalized = {
            str(key).lower(): int(value)
            for key, value in counts.items()
        }

        positive = sum(
            value for key, value in normalized.items()
            if "positive" in key
        )
        negative = sum(
            value for key, value in normalized.items()
            if "negative" in key
        )
        neutral = sum(
            value for key, value in normalized.items()
            if "neutral" in key
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
                labels,
                values,
                color=colors,
                width=0.58,
                zorder=3,
            )

            ax.bar_label(
                bars,
                padding=4,
                fontsize=9,
                color="#57516E",
            )

        ax.set_ylabel("Number of records", fontsize=9)
        ax.tick_params(axis="x", labelsize=9, rotation=0)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.2, zorder=0)
        ax.set_axisbelow(True)

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#E6E1F0")

        self.chart.apply_theme()
        self.chart.canvas.draw_idle()

    def _draw_keywords(self, keywords):
        ax = self.keywords_chart.ax
        ax.clear()

        top_words = keywords[:10]

        if not top_words:
            ax.text(
                0.5, 0.5,
                "No keywords available",
                ha="center",
                va="center",
                color="#88849C",
                transform=ax.transAxes,
            )
            ax.set_axis_off()
        else:
            words = [str(word) for word, _ in top_words][::-1]
            values = [int(count) for _, count in top_words][::-1]

            bars = ax.barh(
                words,
                values,
                color="#A18BE6",
                height=0.62,
                zorder=3,
            )

            ax.bar_label(
                bars,
                padding=4,
                fontsize=8,
                color="#57516E",
            )

            ax.tick_params(axis="y", labelsize=8)
            ax.tick_params(axis="x", labelsize=8)
            ax.grid(axis="x", linestyle="--", alpha=0.2, zorder=0)
            ax.set_axisbelow(True)

            for spine in ("top", "right", "left"):
                ax.spines[spine].set_visible(False)

            ax.spines["bottom"].set_color("#E6E1F0")

        self.keywords_chart.apply_theme()
        self.keywords_chart.canvas.draw_idle()

    def _show_error(self, message):
        self.banner.setText(f"NLP analysis: {message}")
        self.banner.set_level("error")

        self.total_label.setText("—")
        self.positive_label.setText("—")
        self.negative_label.setText("—")
        self.neutral_label.setText("—")
