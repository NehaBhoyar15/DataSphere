"""Local machine-learning training adapter.

Runs entirely on scikit-learn so the ML workspace is usable without
Person 1's model backend. ``train`` returns a plain dict contract that
``ui/ml_view.py`` already expects (importance frame, metrics, actual vs.
predicted, and the fitted estimator for save/load)."""
import numpy as np
import pandas as pd


class MLService:
    MODELS = ["Random Forest", "Linear Model", "Decision Tree", "K-Nearest Neighbors", "Gradient Boosting"]

    def train(self, frame, target, model_name, test_size=0.2, stratify=False):
        if frame is None or frame.empty:
            raise ValueError("No data is loaded.")
        if not target or target not in frame.columns:
            raise ValueError("Choose a target column before training.")

        from sklearn.model_selection import train_test_split

        working = frame.dropna(subset=[target]).copy()
        numeric_cols = [c for c in working.select_dtypes(include="number").columns if c != target]
        if len(numeric_cols) < 1:
            raise ValueError("Need at least one numeric feature besides the target.")

        working = working.dropna(subset=numeric_cols)
        if len(working) < 10:
            raise ValueError("Not enough complete rows to train a model.")

        X = working[numeric_cols].to_numpy(dtype=float)
        y_raw = working[target]

        classification = self._is_classification(y_raw)
        if classification:
            y = y_raw.astype(str).to_numpy()
        else:
            y = pd.to_numeric(y_raw, errors="coerce").to_numpy(dtype=float)

        test_size = min(max(test_size, 0.1), 0.5)
        strat = y if (stratify and classification and len(set(y)) > 1) else None
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=strat
            )
        except ValueError:
            # Falls back when stratification is impossible for the split size.
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

        model = self._build_model(model_name, classification)
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)

        importance = self._feature_importance(model, numeric_cols)

        result = {
            "model": model,
            "model_name": model_name,
            "features": numeric_cols,
            "importance": importance,
            "classification": classification,
            "actual": list(y_test) if not classification else list(y_test),
            "predicted": list(predicted),
        }

        if classification:
            from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score

            result["accuracy"] = float(accuracy_score(y_test, predicted))
            labels = sorted(set(y_test) | set(predicted))
            result["confusion"] = confusion_matrix(y_test, predicted, labels=labels)
            if len(labels) == 2 and hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(X_test)[:, 1]
                    result["auc"] = float(roc_auc_score((y_test == labels[1]).astype(int), proba))
                except Exception:
                    pass
            # Numeric-friendly actual/predicted for the results table.
            result["actual"] = [self._to_numeric_label(v, labels) for v in y_test]
            result["predicted"] = [self._to_numeric_label(v, labels) for v in predicted]
        else:
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

            result["mae"] = float(mean_absolute_error(y_test, predicted))
            result["rmse"] = float(mean_squared_error(y_test, predicted) ** 0.5)
            result["r2"] = float(r2_score(y_test, predicted))

        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _is_classification(series):
        if series.dtype == object or str(series.dtype).startswith("category"):
            return True
        nunique = series.nunique(dropna=True)
        if pd.api.types.is_integer_dtype(series) and nunique <= 10:
            return True
        return False

    @staticmethod
    def _to_numeric_label(value, labels):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(labels.index(value))

    @staticmethod
    def _build_model(model_name, classification):
        name = (model_name or "").lower()
        if classification:
            if "linear" in name:
                from sklearn.linear_model import LogisticRegression
                return LogisticRegression(max_iter=1000)
            if "decision" in name:
                from sklearn.tree import DecisionTreeClassifier
                return DecisionTreeClassifier(random_state=42)
            if "neighbor" in name or "knn" in name:
                from sklearn.neighbors import KNeighborsClassifier
                return KNeighborsClassifier()
            if "gradient" in name or "boost" in name:
                from sklearn.ensemble import GradientBoostingClassifier
                return GradientBoostingClassifier(random_state=42)
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=200, random_state=42)

        if "linear" in name:
            from sklearn.linear_model import LinearRegression
            return LinearRegression()
        if "decision" in name:
            from sklearn.tree import DecisionTreeRegressor
            return DecisionTreeRegressor(random_state=42)
        if "neighbor" in name or "knn" in name:
            from sklearn.neighbors import KNeighborsRegressor
            return KNeighborsRegressor()
        if "gradient" in name or "boost" in name:
            from sklearn.ensemble import GradientBoostingRegressor
            return GradientBoostingRegressor(random_state=42)
        from sklearn.ensemble import RandomForestRegressor
        return RandomForestRegressor(n_estimators=200, random_state=42)

    @staticmethod
    def _feature_importance(model, feature_names):
        if hasattr(model, "feature_importances_"):
            values = np.asarray(model.feature_importances_, dtype=float)
        elif hasattr(model, "coef_"):
            coef = np.asarray(model.coef_, dtype=float)
            values = np.abs(coef).reshape(-1) if coef.ndim > 1 else np.abs(coef)
            if values.shape[0] != len(feature_names):
                values = np.resize(values, len(feature_names))
        else:
            values = np.full(len(feature_names), 1.0 / max(len(feature_names), 1))

        total = values.sum()
        if total > 0:
            values = values / total
        return pd.DataFrame({"Feature": feature_names, "Importance": values}).sort_values(
            "Importance", ascending=False
        )
