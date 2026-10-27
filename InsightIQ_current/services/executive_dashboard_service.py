"""MySQL-backed executive dashboard service for InsightIQ Analytics."""

import pandas as pd
from db_connection import get_connection


class ExecutiveDashboardService:
    def __init__(self):
        self.last_error = ""

    def load_sales(self):
        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    sale_date AS date,
                    product_name,
                    category,
                    region,
                    quantity AS units_sold,
                    revenue
                FROM sales
                ORDER BY sale_date
            """)

            records = cursor.fetchall()
            frame = pd.DataFrame(records)

            if frame.empty:
                self.last_error = "No sales records found."
                return frame

            frame["date"] = pd.to_datetime(
                frame["date"], errors="coerce"
            )
            frame["revenue"] = pd.to_numeric(
                frame["revenue"], errors="coerce"
            ).fillna(0)
            frame["units_sold"] = pd.to_numeric(
                frame["units_sold"], errors="coerce"
            ).fillna(0)

            frame = frame.dropna(subset=["date"])
            self.last_error = ""
            return frame

        except Exception as exc:
            self.last_error = str(exc)
            return pd.DataFrame()

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    @staticmethod
    def summarize(frame):
        if frame.empty:
            return {
                "revenue": 0.0,
                "units": 0,
                "products": 0,
                "regions": 0,
            }

        return {
            "revenue": float(frame["revenue"].sum()),
            "units": int(frame["units_sold"].sum()),
            "products": int(frame["product_name"].nunique()),
            "regions": int(frame["region"].nunique()),
        }

    @staticmethod
    def top_products(frame, limit=5):
        if frame.empty:
            return pd.DataFrame(
                columns=["product_name", "revenue"]
            )

        return (
            frame.groupby("product_name", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .head(limit)
        )

    @staticmethod
    def top_regions(frame, limit=5):
        if frame.empty:
            return pd.DataFrame(
                columns=["region", "revenue"]
            )

        return (
            frame.groupby("region", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .head(limit)
        )

    @staticmethod
    def daily_trend(frame):
        if frame.empty:
            return pd.DataFrame(columns=["date", "revenue"])

        return (
            frame.groupby(frame["date"].dt.date)["revenue"]
            .sum()
            .rename_axis("date")
            .reset_index()
        )

    @staticmethod
    def previous_period_change(current, previous):
        if previous == 0:
            return None if current == 0 else float("inf")

        return ((current - previous) / abs(previous)) * 100
