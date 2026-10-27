"""Time-series forecasting adapter with graceful local fallback.

Supports Holt-Winters and ARIMA via statsmodels (a hard requirement of
this project) and Prophet when the optional ``prophet`` package is
installed. Any failure — too little data, a model that won't converge,
a missing optional package — falls back to a simple naive/drift forecast
so the page always returns a usable result instead of raising.
"""
import numpy as np
import pandas as pd


class ForecastService:
    MODELS = ["Holt-Winters", "ARIMA", "Prophet"]

    def forecast(self, frame, date_col, value_col, horizon, model_name):
        if frame is None or frame.empty:
            raise ValueError("No data is loaded.")
        if date_col not in frame.columns or value_col not in frame.columns:
            raise ValueError("Choose a date and a value column before forecasting.")

        horizon = max(1, int(horizon))
        working = frame[[date_col, value_col]].copy()
        working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
        working[value_col] = pd.to_numeric(working[value_col], errors="coerce")
        working = working.dropna().sort_values(date_col)
        if len(working) < 5:
            raise ValueError("Need at least 5 dated, numeric rows to forecast.")

        dates = working[date_col].reset_index(drop=True)
        values = working[value_col].reset_index(drop=True)
        step = self._infer_step(dates)

        # Backtest: hold out the tail of the known series to score accuracy.
        holdout = min(horizon, max(1, len(values) // 4), len(values) - 2)
        train_values = values.iloc[:-holdout] if holdout else values
        actual_holdout = values.iloc[-holdout:] if holdout else values.iloc[-1:]
        backtest_forecast, _ = self._run_model(train_values, holdout, model_name)
        mae, rmse, mape = self._score(actual_holdout.to_numpy(), backtest_forecast)

        # Full-data fit to project real future periods.
        future_forecast, resid_std = self._run_model(values, horizon, model_name)
        future_dates = [dates.iloc[-1] + step * (i + 1) for i in range(horizon)]
        band = 1.28 * (resid_std if resid_std else max(values.std(), 1e-6))

        history = pd.DataFrame({"Date": dates, "Actual": values})
        forecast_table = pd.DataFrame({
            "Date": future_dates,
            "Forecast": np.round(future_forecast, 2),
            "Lower": np.round(future_forecast - band, 2),
            "Upper": np.round(future_forecast + band, 2),
        })

        return {
            "model": model_name,
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "history": history,
            "forecast": forecast_table,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _infer_step(dates):
        if len(dates) < 2:
            return pd.Timedelta(days=1)
        diffs = dates.diff().dropna()
        if diffs.empty:
            return pd.Timedelta(days=1)
        return diffs.median()

    def _run_model(self, series, steps, model_name):
        name = (model_name or "").lower()
        try:
            if "prophet" in name:
                return self._forecast_prophet(series, steps)
            if "arima" in name:
                return self._forecast_arima(series, steps)
            return self._forecast_holt_winters(series, steps)
        except Exception:
            return self._forecast_naive(series, steps)

    @staticmethod
    def _forecast_holt_winters(series, steps):
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        values = series.to_numpy(dtype=float)
        seasonal_periods = 7 if len(values) >= 14 else None
        model = ExponentialSmoothing(
            values,
            trend="add",
            seasonal="add" if seasonal_periods else None,
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        ).fit(optimized=True)
        forecast = np.asarray(model.forecast(steps), dtype=float)
        resid_std = float(np.nanstd(model.resid)) if hasattr(model, "resid") else None
        return forecast, resid_std

    @staticmethod
    def _forecast_arima(series, steps):
        from statsmodels.tsa.arima.model import ARIMA

        values = series.to_numpy(dtype=float)
        model = ARIMA(values, order=(1, 1, 1)).fit()
        forecast = np.asarray(model.forecast(steps), dtype=float)
        resid_std = float(np.nanstd(model.resid)) if hasattr(model, "resid") else None
        return forecast, resid_std

    @staticmethod
    def _forecast_prophet(series, steps):
        from prophet import Prophet

        frame = pd.DataFrame({
            "ds": pd.date_range("2000-01-01", periods=len(series), freq="D"),
            "y": series.to_numpy(dtype=float),
        })
        model = Prophet(daily_seasonality=False, yearly_seasonality=False)
        model.fit(frame)
        future = model.make_future_dataframe(periods=steps)
        result = model.predict(future)
        forecast = result["yhat"].to_numpy()[-steps:]
        residuals = frame["y"].to_numpy() - result["yhat"].to_numpy()[: len(frame)]
        return forecast, float(np.nanstd(residuals))

    @staticmethod
    def _forecast_naive(series, steps):
        values = series.to_numpy(dtype=float)
        if len(values) >= 2:
            recent = values[-min(10, len(values)):]
            drift = float(np.mean(np.diff(recent)))
        else:
            drift = 0.0
        last = float(values[-1])
        forecast = np.array([last + drift * (i + 1) for i in range(steps)])
        resid_std = float(np.nanstd(values)) if len(values) > 1 else 1.0
        return forecast, resid_std

    @staticmethod
    def _score(actual, predicted):
        actual = np.asarray(actual, dtype=float)
        predicted = np.asarray(predicted[: len(actual)], dtype=float)
        if len(actual) == 0:
            return 0.0, 0.0, 0.0
        errors = actual - predicted
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        nonzero = actual != 0
        mape = float(np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100) if nonzero.any() else 0.0
        return mae, rmse, mape
