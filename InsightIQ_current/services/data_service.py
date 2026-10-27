
"""Dataset service for the AI Data Analytics Assistant.

Loads data from MySQL when available, with support for CSV/Excel
uploads and a local demo dataset fallback.
"""

import numpy as np
import pandas as pd
from db_connection import get_connection


class DataService:
    DEMO_ROWS = 120

    def __init__(self):
        self.source = "Local demo dataset"
        self.data = self._build_demo_dataset()
        self.load_mysql_sales()

    # ------------------------------------------------------------------
    # Demo dataset
    # ------------------------------------------------------------------
    def _build_demo_dataset(self):
        rng = np.random.default_rng(42)
        n = self.DEMO_ROWS

        dates = pd.date_range("2025-01-01", periods=n, freq="D")
        regions = rng.choice(["North", "South", "East", "West"], size=n)
        base = 4200 + 900 * np.sin(np.linspace(0, 6.5, n))

        revenue = base + rng.normal(0, 260, n)
        revenue = np.round(np.clip(revenue, 500, None), 2)

        units_sold = np.round(
            np.clip(revenue / rng.uniform(18, 26, n), 5, None)
        ).astype(float)

        cost = np.round(revenue * rng.uniform(0.45, 0.7, n), 2)
        profit = np.round(revenue - cost, 2)

        feedback_bank = [
            "Great product, really happy with the quality and speed.",
            "Delivery was late and the packaging was damaged.",
            "Support team was helpful and resolved my issue quickly.",
            "Average experience, nothing special but it works.",
            "Terrible service, I want a refund immediately.",
            "Love the new update, works perfectly on my device.",
            "The price is too high compared to competitors.",
            "Excellent value for money, will buy again.",
            "Not satisfied, the item stopped working after a week.",
            "Customer service was slow to respond but polite.",
        ]

        customer_feedback = rng.choice(feedback_bank, size=n)

        frame = pd.DataFrame({
            "date": dates,
            "region": regions,
            "revenue": revenue,
            "units_sold": units_sold,
            "cost": cost,
            "profit": profit,
            "customer_feedback": customer_feedback,
        })

        missing_idx = rng.choice(
            n, size=max(3, n // 25), replace=False
        )
        frame.loc[missing_idx, "profit"] = np.nan

        missing_idx2 = rng.choice(
            n, size=max(2, n // 40), replace=False
        )
        frame.loc[missing_idx2, "customer_feedback"] = None

        return frame

    # ------------------------------------------------------------------
    # MySQL loading
    # ------------------------------------------------------------------
    def load_mysql_sales(self):
        """Load sales records from MySQL into the active dataframe."""
        connection = None

        try:
            connection = get_connection()

            if connection is None:
                print("MySQL unavailable. Using demo dataset.")
                return False

            query = """
                SELECT
                    sale_date AS date,
                    product_name,
                    category,
                    region,
                    quantity AS units_sold,
                    revenue
                FROM sales
                ORDER BY sale_date
            """

            frame = pd.read_sql(query, connection)

            if frame.empty:
                print("MySQL sales table is empty. Using demo dataset.")
                return False

            self.data = frame
            self.source = "MySQL sales database"

            print(f"Loaded {len(frame)} sales records from MySQL.")
            return True

        except Exception as error:
            print(f"MySQL data loading failed: {error}")
            print("Using the available dataset instead.")
            return False

        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # CSV and Excel loading
    # ------------------------------------------------------------------
    def load_file(self, path):
        """Load a CSV or Excel file into the active dataset."""
        lower = str(path).lower()

        if lower.endswith((".xlsx", ".xls")):
            frame = pd.read_excel(path)
        elif lower.endswith(".csv"):
            frame = pd.read_csv(path)
        else:
            raise ValueError(
                "Unsupported file type. Use .csv, .xlsx, or .xls."
            )

        if frame.empty:
            raise ValueError("The selected file has no rows.")

        self.data = frame
        self.source = str(path)
        return self.data

    # ------------------------------------------------------------------
    # Reset demo data
    # ------------------------------------------------------------------
    def reset_demo(self):
        self.data = self._build_demo_dataset()
        self.source = "Local demo dataset"
        return self.data

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summary(self):
        frame = self.data

        return {
            "rows": int(len(frame)),
            "columns": int(frame.shape[1]),
            "missing": int(frame.isna().sum().sum()),
            "numeric": int(
                len(frame.select_dtypes(include="number").columns)
            ),
        }

    def quality(self):
        frame = self.data

        report = pd.DataFrame({
            "Column": frame.columns,
            "Type": [str(dtype) for dtype in frame.dtypes],
            "Missing %": [
                round(frame[col].isna().mean() * 100, 1)
                for col in frame.columns
            ],
            "Unique": [
                int(frame[col].nunique(dropna=True))
                for col in frame.columns
            ],
        })

        return report

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------
    def filtered(self, search_text="", columns=None):
        frame = self.data

        if columns:
            keep = [col for col in columns if col in frame.columns]
            if keep:
                frame = frame[keep]

        search_text = (search_text or "").strip().lower()

        if not search_text:
            return frame

        mask = frame.apply(
            lambda row: row.astype(str)
            .str.lower()
            .str.contains(search_text, na=False)
            .any(),
            axis=1,
        )

        return frame[mask]
