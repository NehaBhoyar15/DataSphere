"""Executive Dashboard UI for InsightIQ Analytics."""

import os
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QComboBox, QSizePolicy, QFileDialog, QMessageBox,
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.ticker import FuncFormatter

from services.executive_dashboard_service import ExecutiveDashboardService


class ExecutiveDashboard(QWidget):
    def __init__(self, data_service=None, parent=None):
        super().__init__(parent)
        self.service = ExecutiveDashboardService()
        self.all_data = None
        self.filtered_data = None
        self.previous_data = None
        self.last_insights = []

        self.setObjectName("executiveDashboard")
        self.setStyleSheet("""
            QWidget#executiveDashboard { background:#F4F7FB; color:#172B4D; font-family:Segoe UI; }
            QLabel#pageTitle { font-size:25px; font-weight:700; color:#14213D; }
            QLabel#subtitle { font-size:12px; color:#64748B; }
            QFrame#kpiCard, QFrame#panel { background:white; border:1px solid #E3E8F0; border-radius:13px; }
            QLabel#kpiTitle { color:#64748B; font-size:12px; font-weight:600; }
            QLabel#kpiValue { color:#172B4D; font-size:22px; font-weight:700; }
            QLabel#kpiChange { font-size:10px; font-weight:600; }
            QLabel#panelTitle { font-size:14px; font-weight:700; color:#172B4D; }
            QLabel#insightText { font-size:12px; color:#334155; padding:4px 0; }
            QComboBox { background:white; border:1px solid #D7DFEA; border-radius:7px; padding:7px 10px; min-width:115px; }
            QPushButton { background:#2563EB; color:white; border:none; border-radius:7px; padding:9px 13px; font-weight:600; }
            QPushButton:hover { background:#1D4ED8; }
            QPushButton:disabled { background:#94A3B8; }
            QPushButton#secondaryButton { background:#0F766E; }
            QPushButton#secondaryButton:hover { background:#115E59; }
        """)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_column = QVBoxLayout()
        title = QLabel("Executive Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Sales performance, period comparisons and business insights")
        subtitle.setObjectName("subtitle")
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        header.addLayout(title_column, 1)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["All time", "Last 7 days", "Last 30 days", "Last 90 days"])
        self.period_combo.currentTextChanged.connect(self.apply_filters)
        self.refresh_button = QPushButton("Refresh data")
        self.refresh_button.clicked.connect(self.load_data)
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setObjectName("secondaryButton")
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_excel_button = QPushButton("Export Excel")
        self.export_excel_button.clicked.connect(self.export_excel)
        header.addWidget(self.period_combo)
        header.addWidget(self.refresh_button)
        header.addWidget(self.export_csv_button)
        header.addWidget(self.export_excel_button)
        root.addLayout(header)

        self.status_label = QLabel("Loading sales data...")
        self.status_label.setObjectName("subtitle")
        root.addWidget(self.status_label)

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        root.addLayout(self.kpi_grid)
        self.kpi_cards = {}
        definitions = [
            ("Revenue", "Total revenue", "#2563EB"),
            ("Units Sold", "Total units sold", "#0D9488"),
            ("Products", "Unique products", "#7C3AED"),
            ("Regions", "Sales regions", "#D97706"),
        ]
        for index, (key, caption, accent) in enumerate(definitions):
            card = QFrame()
            card.setObjectName("kpiCard")
            card.setMinimumHeight(108)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 10, 14, 10)
            layout.setSpacing(4)
            heading = QLabel(caption)
            heading.setObjectName("kpiTitle")
            value = QLabel("—")
            value.setObjectName("kpiValue")
            value.setStyleSheet(f"color:{accent};")
            value.setWordWrap(True)
            change = QLabel("Waiting for data")
            change.setObjectName("kpiChange")
            change.setStyleSheet("color:#64748B;")
            change.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(value)
            layout.addWidget(change)
            self.kpi_cards[key] = {"value": value, "change": change}
            self.kpi_grid.addWidget(card, 0, index)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        trend_panel = self.make_panel("Revenue Performance")
        self.trend_figure = Figure(figsize=(7, 3), dpi=100)
        self.trend_canvas = FigureCanvasQTAgg(self.trend_figure)
        self.trend_canvas.setMinimumHeight(220)
        self.trend_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        trend_panel.layout().addWidget(self.trend_canvas)
        products_panel = self.make_panel("Top Products by Revenue")
        self.product_figure = Figure(figsize=(5, 3), dpi=100)
        self.product_canvas = FigureCanvasQTAgg(self.product_figure)
        self.product_canvas.setMinimumHeight(220)
        self.product_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        products_panel.layout().addWidget(self.product_canvas)
        charts_row.addWidget(trend_panel, 3)
        charts_row.addWidget(products_panel, 2)
        root.addLayout(charts_row, 3)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        regions_panel = self.make_panel("Top Regions by Revenue")
        self.region_figure = Figure(figsize=(5, 2.8), dpi=100)
        self.region_canvas = FigureCanvasQTAgg(self.region_figure)
        self.region_canvas.setMinimumHeight(190)
        self.region_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        regions_panel.layout().addWidget(self.region_canvas)
        insights_panel = self.make_panel("Smart Insights")
        self.insights_label = QLabel("Insights will appear after data loads.")
        self.insights_label.setObjectName("insightText")
        self.insights_label.setWordWrap(True)
        self.insights_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        insights_panel.layout().addWidget(self.insights_label)
        insights_panel.layout().addStretch(1)
        bottom_row.addWidget(regions_panel, 1)
        bottom_row.addWidget(insights_panel, 1)
        root.addLayout(bottom_row, 2)

    def make_panel(self, title):
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("panelTitle")
        layout.addWidget(heading)
        return panel

    def load_data(self):
        self.status_label.setText("Loading sales data...")
        self.refresh_button.setEnabled(False)
        try:
            self.all_data = self.service.load_sales()
            if self.all_data.empty:
                error = self.service.last_error or "No records found."
                self.clear_dashboard()
                self.status_label.setText(f"Could not load sales data: {error}")
                return
            self.all_data["date"] = pd.to_datetime(self.all_data["date"], errors="coerce")
            self.all_data["revenue"] = pd.to_numeric(self.all_data["revenue"], errors="coerce").fillna(0)
            self.all_data["units_sold"] = pd.to_numeric(self.all_data["units_sold"], errors="coerce").fillna(0)
            self.all_data = self.all_data.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            self.status_label.setText(f"{len(self.all_data):,} sales records loaded from MySQL")
            self.apply_filters()
        except Exception as exc:
            self.clear_dashboard()
            self.status_label.setText(f"Dashboard error: {exc}")
        finally:
            self.refresh_button.setEnabled(True)

    def clear_dashboard(self):
        for card in self.kpi_cards.values():
            card["value"].setText("—")
            card["change"].setText("")
        for figure, canvas in ((self.trend_figure, self.trend_canvas), (self.product_figure, self.product_canvas), (self.region_figure, self.region_canvas)):
            figure.clear()
            canvas.draw()
        self.insights_label.setText("No insights available.")
        self.last_insights = []

    def apply_filters(self, *_):
        if self.all_data is None or self.all_data.empty:
            return
        frame = self.all_data.copy()
        self.previous_data = frame.iloc[0:0].copy()
        period = self.period_combo.currentText()
        if period != "All time":
            days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}.get(period)
            if days:
                latest = frame["date"].max().normalize()
                start = latest - pd.Timedelta(days=days - 1)
                previous_start = start - pd.Timedelta(days=days)
                end = latest + pd.Timedelta(days=1)
                current_mask = (frame["date"] >= start) & (frame["date"] < end)
                previous_mask = (frame["date"] >= previous_start) & (frame["date"] < start)
                self.previous_data = frame[previous_mask].copy()
                frame = frame[current_mask].copy()
        self.filtered_data = frame
        self.update_dashboard()

    @staticmethod
    def format_money(value):
        return f"₹{float(value):,.2f}"

    @staticmethod
    def format_change(current, previous):
        if previous == 0:
            if current == 0:
                return "No change vs previous period", "#64748B"
            return "New activity vs previous period", "#0D9488"
        percent = ((current - previous) / abs(previous)) * 100
        if percent > 0:
            return f"↑ {percent:.1f}% vs previous period", "#0D9488"
        if percent < 0:
            return f"↓ {abs(percent):.1f}% vs previous period", "#DC2626"
        return "→ 0.0% vs previous period", "#64748B"

    def set_kpi(self, key, value, current, previous):
        card = self.kpi_cards[key]
        card["value"].setText(value)
        if previous is None or previous.empty:
            card["change"].setText("Comparison unavailable")
            card["change"].setStyleSheet("color:#64748B;")
            return
        if key == "Revenue":
            previous_value = float(previous["revenue"].sum())
        elif key == "Units Sold":
            previous_value = float(previous["units_sold"].sum())
        elif key == "Products":
            previous_value = float(previous["product_name"].nunique())
        else:
            previous_value = float(previous["region"].nunique())
        text, color = self.format_change(float(current), previous_value)
        card["change"].setText(text)
        card["change"].setStyleSheet(f"color:{color}; font-size:10px; font-weight:600;")

    def update_dashboard(self):
        frame = self.filtered_data
        if frame is None or frame.empty:
            self.clear_dashboard()
            self.status_label.setText("No sales records in the selected period.")
            return
        summary = self.service.summarize(frame)
        previous = self.previous_data
        self.set_kpi("Revenue", self.format_money(summary["revenue"]), summary["revenue"], previous)
        self.set_kpi("Units Sold", f'{summary["units"]:,.0f}', summary["units"], previous)
        self.set_kpi("Products", f'{summary["products"]:,}', summary["products"], previous)
        self.set_kpi("Regions", f'{summary["regions"]:,}', summary["regions"], previous)
        self.draw_trend(frame)
        self.draw_ranking_chart(self.product_figure, self.product_canvas, self.service.top_products(frame, limit=5), "product_name", "#2563EB")
        self.draw_ranking_chart(self.region_figure, self.region_canvas, self.service.top_regions(frame, limit=5), "region", "#0D9488")
        self.build_insights(frame)

    def draw_ranking_chart(self, figure, canvas, data, label_column, color):
        figure.clear()
        axis = figure.add_subplot(111)
        if data is None or data.empty:
            axis.text(0.5, 0.5, "No ranking data available", ha="center", va="center", transform=axis.transAxes, color="#64748B")
            axis.set_axis_off()
        else:
            data = data.sort_values("revenue", ascending=True).copy()
            labels = data[label_column].astype(str).tolist()
            values = data["revenue"].astype(float).tolist()
            positions = list(range(len(labels)))
            bars = axis.barh(positions, values, color=color, height=0.58)
            axis.set_yticks(positions)
            axis.set_yticklabels(labels, fontsize=8)
            axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: self.short_money(value)))
            axis.tick_params(axis="x", labelsize=8, colors="#64748B")
            axis.tick_params(axis="y", length=0, colors="#334155")
            axis.grid(axis="x", alpha=0.18)
            axis.set_axisbelow(True)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.spines["left"].set_visible(False)
            axis.spines["bottom"].set_color("#E2E8F0")
            maximum = max(values) if values else 0
            axis.set_xlim(0, maximum * 1.22 if maximum > 0 else 1)
            for bar, value in zip(bars, values):
                axis.text(bar.get_width() + (maximum * 0.025 if maximum else 0.01), bar.get_y() + bar.get_height() / 2, self.short_money(value), va="center", fontsize=7, color="#334155")
        figure.tight_layout(pad=1.3)
        canvas.draw()

    @staticmethod
    def short_money(value):
        value = float(value)
        if abs(value) >= 10_000_000:
            return f"₹{value / 10_000_000:.1f}Cr"
        if abs(value) >= 100_000:
            return f"₹{value / 100_000:.1f}L"
        if abs(value) >= 1_000:
            return f"₹{value / 1_000:.1f}K"
        return f"₹{value:.0f}"

        
    def draw_trend(self, frame):
        self.trend_figure.clear()
        self.trend_figure.set_facecolor("white")
        axis = self.trend_figure.add_subplot(111)
        axis.set_facecolor("white")

        trend = self.service.daily_trend(frame)

        if trend is None or trend.empty:
            axis.text(
                0.5, 0.5, "No revenue data available",
                ha="center", va="center",
                transform=axis.transAxes,
                color="#64748B", fontsize=11,
            )
            axis.set_axis_off()
        else:
            trend = trend.copy()
            trend["date"] = pd.to_datetime(
                trend["date"], errors="coerce"
            )
            trend["revenue"] = pd.to_numeric(
                trend["revenue"], errors="coerce"
            )
            trend = trend.dropna(
                subset=["date", "revenue"]
            ).sort_values("date").reset_index(drop=True)

            if trend.empty:
                axis.text(
                    0.5, 0.5, "No valid revenue values",
                    ha="center", va="center",
                    transform=axis.transAxes,
                    color="#64748B",
                )
                axis.set_axis_off()
            else:
                dates = trend["date"]
                revenues = trend["revenue"].astype(float)
                positions = list(range(len(trend)))

                axis.fill_between(
                    positions, revenues.tolist(),
                    color="#2563EB", alpha=0.10,
                )
                axis.plot(
                    positions, revenues.tolist(),
                    color="#2563EB", linewidth=2.4,
                    marker="o" if len(trend) <= 30 else None,
                    markersize=4, markerfacecolor="white",
                    markeredgewidth=1.8,
                )

                # Display exact revenue values on chart points.
                if len(trend) <= 15:
                    for x, value in zip(positions, revenues):
                        axis.annotate(
                            self.format_money(value),
                            (x, value),
                            textcoords="offset points",
                            xytext=(0, 9),
                            ha="center", fontsize=8,
                            color="#172B4D",
                        )

                step = max(1, len(dates) // 6)
                ticks = list(range(0, len(dates), step))
                if positions[-1] not in ticks:
                    ticks.append(positions[-1])

                axis.set_xticks(ticks)
                axis.set_xticklabels(
                    [
                        dates.iloc[i].strftime("%d %b")
                        for i in ticks
                    ],
                    rotation=20, ha="right", fontsize=8,
                )

                axis.yaxis.set_major_formatter(
                    FuncFormatter(
                        lambda value, _: self.short_money(value)
                    )
                )
                axis.tick_params(
                    axis="y", labelsize=8, colors="#64748B"
                )
                axis.tick_params(
                    axis="x", colors="#64748B", length=0
                )
                axis.grid(axis="y", alpha=0.18)
                axis.set_axisbelow(True)

                for spine in ("top", "right", "left"):
                    axis.spines[spine].set_visible(False)
                axis.spines["bottom"].set_color("#E2E8F0")

                # Revenue direction indicator.
                if len(revenues) >= 2:
                    first = float(revenues.iloc[0])
                    last = float(revenues.iloc[-1])

                    if first > 0:
                        change = ((last - first) / first) * 100
                        direction = (
                            "↑" if change > 0
                            else "↓" if change < 0
                            else "→"
                        )
                        axis.set_title(
                            f"{direction} {change:+.1f}% "
                            "from first to last day",
                            loc="left", fontsize=9,
                            color="#334155", pad=10,
                        )

        self.trend_figure.tight_layout(pad=1.5)
        self.trend_canvas.draw()

       

            # Show readable date labels without crowding the x-axis.
        step = max(1, (len(dates) + 5) // 6)
        ticks = list(range(0, len(dates), step))
        if ticks[-1] != len(dates) - 1:
            ticks.append(len(dates) - 1)
            axis.set_xticks(ticks)
            axis.set_xticklabels(
                [dates.iloc[i].strftime("%d %b") for i in ticks],
                rotation=20, ha="right", fontsize=8,
            )

            # Keep the actual revenue values visible on the Y-axis.
            axis.yaxis.set_major_formatter(
                FuncFormatter(lambda value, _: self.short_money(value))
            )
            axis.tick_params(axis="y", labelsize=8, colors="#475569", labelleft=True)
            axis.tick_params(axis="x", labelsize=8, colors="#64748B")
            axis.grid(axis="y", alpha=0.20, linestyle="--")
            axis.set_axisbelow(True)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.spines["left"].set_visible(False)
            axis.spines["bottom"].set_color("#E2E8F0")
            axis.margins(x=0.04, y=0.22)

            # Label every point for short periods; for long periods label up to
            # about 10 evenly spaced points so the graph remains readable.
            if len(positions) <= 14:
                label_positions = positions
            else:
                count = min(10, len(positions))
                label_positions = sorted({
                    round(i * (len(positions) - 1) / (count - 1))
                    for i in range(count)
                }) if count > 1 else [len(positions) - 1]

            for i in label_positions:
                value = revenues[i]
                axis.annotate(
                    self.short_money(value),
                    (positions[i], value),
                    textcoords="offset points",
                    xytext=(0, 8 if i % 2 == 0 else -14),
                    ha="center", va="center", fontsize=7,
                    color="#1E3A8A",
                    bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "none", "alpha": 0.88},
                    clip_on=True,
                )

        self.trend_figure.tight_layout(pad=1.5)
        self.trend_canvas.draw()

    def build_insights(self, frame):
        total_revenue = float(frame["revenue"].sum())
        total_units = float(frame["units_sold"].sum())
        product_data = self.service.top_products(frame, limit=1)
        region_data = self.service.top_regions(frame, limit=1)
        messages = [f"Total revenue for this period: {self.format_money(total_revenue)}.", f"Total units sold: {total_units:,.0f}."]
        if total_units > 0:
            messages.append(f"Average revenue per unit: {self.format_money(total_revenue / total_units)}.")
        if not product_data.empty:
            best = product_data.iloc[0]
            product_revenue = float(best["revenue"])
            share = product_revenue / total_revenue * 100 if total_revenue else 0
            messages.append(f"Top product: {best['product_name']} ({self.format_money(product_revenue)}, {share:.1f}% of total revenue).")
        if not region_data.empty:
            best_region = region_data.iloc[0]
            region_revenue = float(best_region["revenue"])
            share = region_revenue / total_revenue * 100 if total_revenue else 0
            messages.append(f"Leading region: {best_region['region']} ({self.format_money(region_revenue)}, {share:.1f}% of total revenue).")
        if self.previous_data is not None and not self.previous_data.empty:
            old_revenue = float(self.previous_data["revenue"].sum())
            comparison, _ = self.format_change(total_revenue, old_revenue)
            messages.append(f"Revenue comparison: {comparison}.")
        daily = self.service.daily_trend(frame)
        if len(daily) >= 2:
            first = float(daily.iloc[0]["revenue"])
            last = float(daily.iloc[-1]["revenue"])
            if first > 0:
                change = ((last - first) / first) * 100
                if change > 0:
                    messages.append(f"Daily revenue increased {change:.1f}% from the first to the last day in this selection.")
                elif change < 0:
                    messages.append(f"Daily revenue decreased {abs(change):.1f}% from the first to the last day in this selection.")
                else:
                    messages.append("Daily revenue was equal on the first and last days in this selection.")
            elif last > 0:
                messages.append("The last recorded day had revenue; the first day had no revenue to calculate a percentage change.")
        self.last_insights = messages
        self.insights_label.setText("\n\n".join("• " + message for message in messages))

    def export_summary(self):
        frame = self.filtered_data
        if frame is None or frame.empty:
            raise ValueError("There is no sales data in the selected period to export.")
        summary = self.service.summarize(frame)
        previous = self.previous_data
        rows = [
            ("Report", "InsightIQ Analytics — Executive Dashboard"),
            ("Selected period", self.period_combo.currentText()),
            ("Generated at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Sales records", len(frame)),
            ("Total revenue (INR)", float(summary["revenue"])),
            ("Units sold", float(summary["units"])),
            ("Unique products", int(summary["products"])),
            ("Sales regions", int(summary["regions"])),
        ]
        if previous is not None and not previous.empty:
            old_revenue = float(previous["revenue"].sum())
            change_text, _ = self.format_change(float(summary["revenue"]), old_revenue)
            rows.append(("Revenue vs previous period", change_text))
        return pd.DataFrame(rows, columns=["Metric", "Value"])

    def export_csv(self):
        if self.filtered_data is None or self.filtered_data.empty:
            QMessageBox.warning(self, "No data", "There is no sales data to export for this period.")
            return
        default_name = f"InsightIQ_Report_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV Report", default_name, "CSV files (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            summary_df = self.export_summary()
            insights_df = pd.DataFrame({"Smart Insights": self.last_insights or ["No insights available."]})
            sales_df = self.filtered_data.copy()
            sales_df["date"] = pd.to_datetime(sales_df["date"]).dt.strftime("%Y-%m-%d")
            with open(path, "w", encoding="utf-8-sig", newline="") as handle:
                handle.write("INSIGHTIQ ANALYTICS — EXECUTIVE REPORT\n\nKPI SUMMARY\n")
                summary_df.to_csv(handle, index=False)
                handle.write("\nSMART INSIGHTS\n")
                insights_df.to_csv(handle, index=False)
                handle.write("\nSALES DATA\n")
                sales_df.to_csv(handle, index=False)
            QMessageBox.information(self, "Export complete", f"CSV report saved successfully:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not export CSV report:\n{exc}")

    def export_excel(self):
        if self.filtered_data is None or self.filtered_data.empty:
            QMessageBox.warning(self, "No data", "There is no sales data to export for this period.")
            return
        default_name = f"InsightIQ_Report_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel Report", default_name, "Excel workbook (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            summary_df = self.export_summary()
            insights_df = pd.DataFrame({"Smart Insights": self.last_insights or ["No insights available."]})
            sales_df = self.filtered_data.copy()
            sales_df["date"] = pd.to_datetime(sales_df["date"]).dt.strftime("%Y-%m-%d")
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                summary_df.to_excel(writer, sheet_name="KPI Summary", index=False)
                insights_df.to_excel(writer, sheet_name="Smart Insights", index=False)
                sales_df.to_excel(writer, sheet_name="Sales Data", index=False)
                for sheet in writer.book.worksheets:
                    sheet.freeze_panes = "A2"
                    sheet.auto_filter.ref = sheet.dimensions
                    for column_cells in sheet.columns:
                        max_length = max((len(str(cell.value)) if cell.value is not None else 0) for cell in column_cells)
                        sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 48)
                    for cell in sheet[1]:
                        cell.font = cell.font.copy(bold=True, color="FFFFFF")
                        cell.fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="2563EB")
            QMessageBox.information(self, "Export complete", f"Excel report saved successfully:\n{path}")
        except ImportError:
            QMessageBox.critical(self, "Excel dependency missing", "Install Excel support in your active virtual environment:\npip install openpyxl")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not export Excel report:\n{exc}")
