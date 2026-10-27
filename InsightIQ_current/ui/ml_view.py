
"""Professional Machine Learning workspace for InsightIQ Analytics."""

import os
import joblib
import pandas as pd

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QGridLayout, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QSizePolicy
)

from services.ml_service import MLService
from widgets.chart_widget import ChartWidget


class MLPage(QWidget):
    def __init__(self, data_service, parent=None):
        super().__init__(parent)

        self.data_service = data_service
        self.service = MLService()
        self.last_result = None

        self.setObjectName("mlPage")
        self.setStyleSheet("""
            QWidget#mlPage {
                background: #F7F8FC;
                color: #292544;
                font-family: "Segoe UI";
            }
            QLabel#title {
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
                min-width: 130px;
            }
            QPushButton {
                background: #7357C8;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #6245B5;
            }
            QPushButton:disabled {
                background: #C9C2DE;
                color: white;
            }
            QPushButton#secondaryButton {
                background: #EEEAF8;
                color: #514184;
                border: 1px solid #DDD6F0;
            }
            QTableWidget {
                background: white;
                alternate-background-color: #F8F7FC;
                color: #302B4D;
                border: 1px solid #E8E5F1;
                gridline-color: #EEEBF5;
                border-radius: 8px;
            }
            QHeaderView::section {
                background: #F0EDFA;
                color: #514878;
                padding: 8px;
                border: none;
                font-weight: 600;
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
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(26, 24, 26, 28)
        root.setSpacing(17)

        title = QLabel("Machine Learning Studio")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel(
            "Train models, evaluate performance and explore important features."
        )
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        # Model configuration
        controls = self._panel("Model configuration")
        control_layout = controls.layout()

        row = QHBoxLayout()
        row.setSpacing(12)

        row.addWidget(QLabel("Target column"))
        self.target_combo = QComboBox()
        self.target_combo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        row.addWidget(self.target_combo, 2)

        row.addWidget(QLabel("Algorithm"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(MLService.MODELS)
        row.addWidget(self.model_combo, 2)

        row.addWidget(QLabel("Test data"))
        self.test_combo = QComboBox()
        self.test_combo.addItems(["20%", "25%", "30%"])
        row.addWidget(self.test_combo, 1)

        control_layout.addLayout(row)

        button_row = QHBoxLayout()

        self.train_button = QPushButton("Train model")
        self.train_button.clicked.connect(self.train_model)
        button_row.addWidget(self.train_button)

        save_button = QPushButton("Save model")
        save_button.setObjectName("secondaryButton")
        save_button.clicked.connect(self.save_model)
        button_row.addWidget(save_button)

        load_button = QPushButton("Load model")
        load_button.setObjectName("secondaryButton")
        load_button.clicked.connect(self.load_model)
        button_row.addWidget(load_button)

        button_row.addStretch()
        control_layout.addLayout(button_row)
        root.addWidget(controls)

        self.status = QLabel(
            "Choose a target column and click Train model."
        )
        self.status.setWordWrap(True)
        self.status.setStyleSheet(
            "background:#EFECFA; color:#55458A; padding:12px;"
            "border-radius:8px;"
        )
        root.addWidget(self.status)

        # Metric cards
        metrics = QGridLayout()
        metrics.setSpacing(12)

        self.metric_values = {}
        metric_names = [
            ("score", "MODEL SCORE"),
            ("error", "MAE / ERROR"),
            ("rmse", "RMSE"),
            ("rows", "TRAINING ROWS"),
        ]

        for index, (key, label_text) in enumerate(metric_names):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 14, 15, 14)

            label = QLabel(label_text)
            label.setObjectName("metricLabel")
            card_layout.addWidget(label)

            value = QLabel("—")
            value.setObjectName("metricValue")
            card_layout.addWidget(value)

            self.metric_values[key] = value
            metrics.addWidget(card, 0, index)

        root.addLayout(metrics)

        # Charts
        charts = QHBoxLayout()
        charts.setSpacing(14)

        importance_panel = self._panel("Feature importance")
        self.importance_chart = ChartWidget()
        self.importance_chart.setMinimumHeight(300)
        importance_panel.layout().addWidget(self.importance_chart)
        charts.addWidget(importance_panel, 1)

        prediction_panel = self._panel("Actual vs predicted")
        self.prediction_chart = ChartWidget()
        self.prediction_chart.setMinimumHeight(300)
        prediction_panel.layout().addWidget(self.prediction_chart)
        charts.addWidget(prediction_panel, 1)

        root.addLayout(charts)

        # Results
        results_panel = self._panel("Prediction results")
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(260)
        results_panel.layout().addWidget(self.results_table)
        root.addWidget(results_panel)

        root.addStretch()

        self.refresh()

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

    def refresh(self):
        """Refresh the available target columns."""
        current = self.target_combo.currentText()
        self.target_combo.clear()

        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self.target_combo.addItem("No dataset loaded")
            self.train_button.setEnabled(False)
            return

        self.target_combo.addItems([str(c) for c in data.columns])
        index = self.target_combo.findText(current)

        if index >= 0:
            self.target_combo.setCurrentIndex(index)

        self.train_button.setEnabled(True)

    def train_model(self):
        data = getattr(self.data_service, "data", None)

        if data is None or data.empty:
            self._show_error("Please load a dataset first.")
            return

        target = self.target_combo.currentText()

        if not target or target == "No dataset loaded":
            self._show_error("Select a valid target column.")
            return

        model_name = self.model_combo.currentText()
        test_size = int(self.test_combo.currentText().replace("%", "")) / 100

        self.train_button.setEnabled(False)
        self.train_button.setText("Training...")

        try:
            result = self.service.train(
                data,
                target,
                model_name,
                test_size=test_size,
            )

            self.last_result = result
            self._show_metrics(result, len(data))
            self._draw_importance(result)
            self._draw_predictions(result)
            self._fill_results(result)

            if result["classification"]:
                score = f"{result['accuracy'] * 100:.2f}% accuracy"
            else:
                score = f"R² = {result['r2']:.3f}"

            self.status.setText(
                f"{model_name} trained successfully. {score}"
            )
            self.status.setStyleSheet(
                "background:#E8F6EE; color:#246B45; padding:12px;"
                "border-radius:8px;"
            )

        except Exception as exc:
            self._show_error(str(exc))

        finally:
            self.train_button.setEnabled(True)
            self.train_button.setText("Train model")

    def _show_metrics(self, result, total_rows):
        if result["classification"]:
            self.metric_values["score"].setText(
                f"{result['accuracy'] * 100:.1f}%"
            )
            self.metric_values["error"].setText("—")
            self.metric_values["rmse"].setText("—")
        else:
            self.metric_values["score"].setText(
                f"{result['r2']:.3f}"
            )
            self.metric_values["error"].setText(
                f"{result['mae']:,.2f}"
            )
            self.metric_values["rmse"].setText(
                f"{result['rmse']:,.2f}"
            )

        self.metric_values["rows"].setText(f"{total_rows:,}")

    def _draw_importance(self, result):
        ax = self.importance_chart.ax
        ax.clear()

        frame = result["importance"].head(10).iloc[::-1]

        if frame.empty:
            ax.text(
                0.5, 0.5, "No feature importance available",
                ha="center", va="center", color="#94A3B8",
                transform=ax.transAxes,
            )
        else:
            ax.barh(
                frame["Feature"].astype(str),
                frame["Importance"],
                color="#A18BE6",
            )
            ax.tick_params(axis="y", labelsize=8)
            ax.set_xlabel("Relative importance", color="#CBD5E1")
            ax.grid(axis="x", alpha=0.2)

        self.importance_chart.apply_theme()
        self.importance_chart.canvas.draw_idle()

    def _draw_predictions(self, result):
        ax = self.prediction_chart.ax
        ax.clear()

        actual = result["actual"]
        predicted = result["predicted"]
        count = min(len(actual), len(predicted), 100)

        if count == 0:
            ax.text(
                0.5, 0.5, "No predictions available",
                ha="center", va="center", color="#94A3B8",
                transform=ax.transAxes,
            )
        else:
            actual_values = pd.to_numeric(
                pd.Series(actual[:count]), errors="coerce"
            )
            predicted_values = pd.to_numeric(
                pd.Series(predicted[:count]), errors="coerce"
            )

            valid = actual_values.notna() & predicted_values.notna()
            actual_values = actual_values[valid]
            predicted_values = predicted_values[valid]

            ax.plot(
                range(len(actual_values)),
                actual_values,
                label="Actual",
                color="#A78BFA",
                linewidth=2,
            )
            ax.plot(
                range(len(predicted_values)),
                predicted_values,
                label="Predicted",
                color="#34D399",
                linewidth=2,
            )
            ax.set_xlabel("Test sample")
            ax.legend(frameon=False)

        self.prediction_chart.apply_theme()
        self.prediction_chart.canvas.draw_idle()

    def _fill_results(self, result):
        actual = result["actual"]
        predicted = result["predicted"]

        self.results_table.clear()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(
            ["Actual", "Predicted"]
        )
        self.results_table.setRowCount(min(len(actual), 200))

        for row in range(min(len(actual), 200)):
            self.results_table.setItem(
                row, 0, QTableWidgetItem(str(actual[row]))
            )
            self.results_table.setItem(
                row, 1, QTableWidgetItem(str(predicted[row]))
            )

        self.results_table.resizeColumnsToContents()

    def save_model(self):
        if not self.last_result:
            self._show_error("Train a model before saving it.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save trained model",
            "insightiq_model.joblib",
            "InsightIQ Model (*.joblib)",
        )

        if not path:
            return

        try:
            joblib.dump(
                {
                    "model": self.last_result["model"],
                    "model_name": self.last_result["model_name"],
                    "features": self.last_result["features"],
                    "classification": self.last_result["classification"],
                },
                path,
            )
            self.status.setText(f"Model saved: {os.path.basename(path)}")
        except Exception as exc:
            self._show_error(f"Could not save model: {exc}")

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load trained model",
            "",
            "InsightIQ Model (*.joblib)",
        )

        if not path:
            return

        try:
            saved = joblib.load(path)

            if not isinstance(saved, dict) or "model" not in saved:
                raise ValueError("This file is not a supported InsightIQ model.")

            model = saved["model"]
            features = saved.get("features", [])

            self.last_result = {
                "model": model,
                "model_name": saved.get("model_name", "Loaded model"),
                "features": features,
                "classification": saved.get("classification", False),
                "importance": self.service._feature_importance(
                    model, features
                ),
                "actual": [],
                "predicted": [],
            }

            self._draw_importance(self.last_result)
            self._draw_predictions(self.last_result)
            self._fill_results(self.last_result)

            self.status.setText(
                f"Model loaded: {os.path.basename(path)}. "
                "Train again to evaluate it on the current dataset."
            )
        except Exception as exc:
            self._show_error(f"Could not load model: {exc}")

    def _show_error(self, message):
        self.status.setText(f"ML workspace: {message}")
        self.status.setStyleSheet(
            "background:#FCEBEC; color:#A12D43; padding:12px;"
            "border-radius:8px;"
        )
