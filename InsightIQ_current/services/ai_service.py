"""Local analytics engine for InsightIQ Analytics.

All analysis runs locally against a Pandas DataFrame.
SQL is generated for preview only and is never executed.
"""

import re
from difflib import get_close_matches

import pandas as pd


class AIService:
    """Understand dataset questions and calculate answers using Pandas."""

    ALIASES = {
        "revenue": [
            "sales", "sales amount", "income", "turnover",
            "total sales", "sales revenue", "amount", "total revenue",
        ],
        "units_sold": [
            "units", "quantity", "qty", "unit sold", "units sold",
            "number of units", "items sold", "quantity sold",
        ],
        "product_name": ["product", "item", "products", "product name"],
        "category": ["product category", "type", "categories"],
        "region": ["location", "area", "territory", "state", "zone"],
        "date": [
            "day", "time", "sale date", "order date",
            "transaction date", "sales date", "timestamp",
        ],
        "profit": ["earnings", "net profit", "profit amount"],
        "cost": ["expense", "expenses", "costs", "cost amount"],
    }

    METRIC_PREFERENCES = [
        "revenue", "profit", "units_sold", "cost",
    ]

    def ask(self, question, data):
        """Return answer, SQL preview, and structured result details."""
        question = str(question or "").strip()
        frame = self._get_frame(data)

        if frame is None or frame.empty:
            return self._response(
                "No dataset is loaded, or the active dataset is empty. "
                "Load data from MySQL, CSV, or Excel first.",
                "-- Load a non-empty dataset before generating SQL.",
                frame,
            )

        if not question:
            return self._response(
                "Please enter a question about your dataset.",
                "-- Enter a question to generate a SQL preview.",
                frame,
            )

        try:
            answer, details = self._analyse(question, frame)
        except Exception as exc:
            answer = (
                "I couldn't complete that analysis safely. "
                "Check the question and dataset, then try again. "
                f"Error type: {type(exc).__name__}."
            )
            details = []

        try:
            sql = self._generate_sql(question, frame)
        except Exception:
            sql = (
                "-- Could not generate a matching SQL preview.\n"
                "-- No SQL was executed."
            )

        return self._response(answer, sql, frame, details)

    @staticmethod
    def _get_frame(data):
        """Return a copy so analysis does not mutate the active dataset."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if data is None:
            return None
        try:
            return pd.DataFrame(data)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _response(answer, sql, frame, details=None):
        return {
            "answer": str(answer),
            "sql": str(sql),
            "demo": True,
            "mode": "Local Pandas analysis",
            "details": details or [],
            "rows": int(len(frame)) if frame is not None else 0,
            "columns": int(frame.shape[1]) if frame is not None else 0,
        }

    @staticmethod
    def _normalise(value):
        value = str(value).lower().replace("_", " ").replace("-", " ")
        value = re.sub(r"[^a-z0-9.% ]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _column_name(cls, column):
        return cls._normalise(column)

    @classmethod
    def _aliases_for(cls, column):
        name = cls._column_name(column)
        aliases = []

        for canonical, values in cls.ALIASES.items():
            all_names = [canonical] + values
            if name in [cls._normalise(v) for v in all_names]:
                aliases.extend(all_names)

        return list(dict.fromkeys(cls._normalise(v) for v in aliases))

    @classmethod
    def _find_column(cls, question, data):
        """Find an explicitly mentioned column or known alias."""
        q = cls._normalise(question)
        columns = list(data.columns)

        for column in sorted(
            columns,
            key=lambda item: len(cls._column_name(item)),
            reverse=True,
        ):
            name = cls._column_name(column)
            if name and re.search(r"\b" + re.escape(name) + r"\b", q):
                return column

        for column in columns:
            for alias in cls._aliases_for(column):
                if alias and re.search(r"\b" + re.escape(alias) + r"\b", q):
                    return column

        candidates = []
        for column in columns:
            candidates.append((cls._column_name(column), column))
            candidates.extend(
                (alias, column) for alias in cls._aliases_for(column)
            )

        for word in q.split():
            if len(word) < 4:
                continue
            matches = get_close_matches(
                word,
                list(dict.fromkeys(name for name, _ in candidates)),
                n=1,
                cutoff=0.90,
            )
            if matches:
                for name, column in candidates:
                    if name == matches[0]:
                        return column

        return None

    @classmethod
    def _find_dimension(cls, question, data):
        """Identify a categorical column such as product, region or category."""
        q = cls._normalise(question)
        column = cls._find_column(question, data)

        if column is not None and not pd.api.types.is_numeric_dtype(
            data[column]
        ):
            return column

        hints = [
            ("product", ["product", "products", "item", "items"]),
            ("region", ["region", "location", "area", "territory", "zone"]),
            ("category", ["category", "categories", "type"]),
        ]

        for canonical, words in hints:
            if any(
                re.search(r"\b" + re.escape(word) + r"\b", q)
                for word in words
            ):
                for candidate in data.columns:
                    name = cls._column_name(candidate)
                    if name == canonical or name in words:
                        return candidate

        categorical = list(data.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns)

        if len(categorical) == 1:
            return categorical[0]

        return None

    @classmethod
    def _find_metric_column(cls, question, data, exclude=None):
        """Identify the numeric measure requested in a question."""
        q = cls._normalise(question)
        excluded = set(exclude or [])
        numeric = [
            c for c in data.select_dtypes(include="number").columns
            if c not in excluded
        ]

        # Exact numeric column names have priority.
        for column in sorted(
            numeric, key=lambda item: len(cls._column_name(item)),
            reverse=True,
        ):
            name = cls._column_name(column)
            if name and re.search(r"\b" + re.escape(name) + r"\b", q):
                return column

        # Match common measure aliases against actual numeric columns.
        for canonical in cls.METRIC_PREFERENCES:
            aliases = [canonical] + cls.ALIASES.get(canonical, [])
            if any(
                re.search(
                    r"\b" + re.escape(cls._normalise(alias)) + r"\b", q
                )
                for alias in aliases
            ):
                for column in numeric:
                    name = cls._column_name(column)
                    accepted = [
                        cls._normalise(alias)
                        for alias in aliases + [canonical]
                    ]
                    if name in accepted:
                        return column

        # "Units sold" is a stronger intent than a generic "sales" word.
        if re.search(r"\b(units sold|quantity sold|items sold|qty)\b", q):
            for column in numeric:
                name = cls._column_name(column)
                if any(word in name for word in ("unit", "quantity", "qty")):
                    return column

        # Use revenue as a default only when the question is about revenue
        # or when no more specific metric was requested.
        if not re.search(
            r"\b(profit|earnings|cost|expense|quantity|units|qty)\b", q
        ):
            for column in numeric:
                if cls._column_name(column) == "revenue":
                    return column

        return None

    @staticmethod
    def _numeric(data, column):
        return pd.to_numeric(data[column], errors="coerce")

    @staticmethod
    def _format_number(value, decimals=2):
        if value is None or pd.isna(value):
            return "N/A"
        try:
            return f"{float(value):,.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_value(value):
        try:
            if pd.isna(value):
                return "(missing)"
        except (TypeError, ValueError):
            pass

        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)

    @classmethod
    def _find_date_column(cls, data):
        """Find a date column by name, then by successful date parsing."""
        for column in data.columns:
            name = cls._column_name(column)
            if any(
                term in name
                for term in ("date", "time", "timestamp", "datetime")
            ):
                return column

        for column in data.columns:
            parsed = pd.to_datetime(data[column], errors="coerce")
            if len(parsed) and parsed.notna().mean() >= 0.80:
                return column

        return None

    @classmethod
    def _overview(cls, data):
        missing = data.isna().sum()
        blank_counts = {}
        for column in data.select_dtypes(
            include=["object", "string"]
        ).columns:
            blank_counts[column] = int(
                data[column].astype("string").str.strip().eq("").sum()
            )

        missing_total = int(missing.sum()) + sum(blank_counts.values())
        duplicates = int(data.duplicated().sum())
        numeric_columns = list(data.select_dtypes(include="number").columns)
        categorical_columns = list(data.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns)

        details = [
            {"Metric": "Total rows", "Value": f"{len(data):,}"},
            {"Metric": "Total columns", "Value": f"{len(data.columns):,}"},
            {"Metric": "Numeric columns", "Value": len(numeric_columns)},
            {"Metric": "Categorical columns", "Value": len(categorical_columns)},
            {"Metric": "Missing or blank cells", "Value": f"{missing_total:,}"},
            {"Metric": "Exact duplicate rows", "Value": f"{duplicates:,}"},
        ]

        sections = [
            f"Dataset overview: {len(data):,} rows and "
            f"{len(data.columns):,} columns.",
            f"Data types: {len(numeric_columns)} numeric and "
            f"{len(categorical_columns)} categorical columns.",
            f"Data quality: {missing_total:,} missing or blank cells and "
            f"{duplicates:,} exact duplicate rows.",
        ]

        for column in numeric_columns:
            values = pd.to_numeric(data[column], errors="coerce").dropna()
            if values.empty:
                continue

            stats = [
                ("total", values.sum()),
                ("average", values.mean()),
                ("minimum", values.min()),
                ("maximum", values.max()),
            ]
            sections.append(
                f"{column}: " + ", ".join(
                    f"{label} {cls._format_number(value)}"
                    for label, value in stats
                ) + "."
            )
            for label, value in stats:
                details.append({
                    "Metric": f"{column} {label}",
                    "Value": cls._format_number(value),
                })

        metric = cls._find_metric_column("revenue", data)
        if metric is None and numeric_columns:
            metric = numeric_columns[0]

        if metric is not None:
            for hint, label in [
                ("product", "Top product"),
                ("category", "Top category"),
                ("region", "Top region"),
            ]:
                dimension = None
                for column in data.columns:
                    name = cls._column_name(column)
                    if hint == "product" and name in {
                        "product", "product name", "item", "products"
                    }:
                        dimension = column
                    elif hint == "category" and name in {
                        "category", "product category", "type"
                    }:
                        dimension = column
                    elif hint == "region" and name in {
                        "region", "location", "area", "territory", "zone"
                    }:
                        dimension = column
                    if dimension is not None:
                        break

                if dimension is None:
                    continue

                temp = data[[dimension, metric]].copy()
                temp[metric] = pd.to_numeric(temp[metric], errors="coerce")
                grouped = temp.groupby(
                    dimension, dropna=False
                )[metric].sum(min_count=1).dropna()

                if grouped.empty:
                    continue

                top_name = grouped.idxmax()
                top_value = grouped.max()
                value = (
                    f"{cls._format_value(top_name)} "
                    f"({cls._format_number(top_value)})"
                )
                sections.append(f"{label} by {metric}: {value}.")
                details.append({"Metric": label, "Value": value})

        date_column = cls._find_date_column(data)
        if date_column is not None:
            dates = pd.to_datetime(
                data[date_column], errors="coerce"
            ).dropna()
            if not dates.empty:
                start = dates.min().strftime("%Y-%m-%d")
                end = dates.max().strftime("%Y-%m-%d")
                sections.append(f"Date range: {start} to {end}.")
                details.append({
                    "Metric": "Date range",
                    "Value": f"{start} to {end}",
                })

        if missing_total:
            affected = []
            for column in data.columns:
                count = int(data[column].isna().sum())
                if column in blank_counts:
                    count += blank_counts[column]
                if count:
                    affected.append(f"{column}: {count}")
            sections.append("Missing/blank values by column: " + ", ".join(
                affected
            ) + ".")

        sections.append(
            "Calculated locally from the active dataset. "
            "SQL is a preview only and is never executed."
        )
        return "\n\n".join(sections), details

    @classmethod
    def _missing_values(cls, data):
        rows = []
        for column in data.columns:
            count = int(data[column].isna().sum())
            if data[column].dtype == object or pd.api.types.is_string_dtype(
                data[column]
            ):
                count += int(
                    data[column].astype("string").str.strip().eq("").sum()
                )
            if count:
                rows.append({"Metric": str(column), "Value": f"{count:,}"})

        if not rows:
            return (
                "No missing or blank values were found in the active dataset.",
                [{"Metric": "Missing/blank cells", "Value": "0"}],
            )

        total = sum(int(item["Value"].replace(",", "")) for item in rows)
        breakdown = ", ".join(
            f"{item['Metric']}: {item['Value']}" for item in rows
        )
        return f"Found {total:,} missing or blank cells. {breakdown}.", rows

    @classmethod
    def _duplicate_rows(cls, data):
        count = int(data.duplicated().sum())
        return (
            f"The dataset contains {count:,} exact duplicate rows.",
            [
                {"Metric": "Duplicate rows", "Value": f"{count:,}"},
                {
                    "Metric": "Non-duplicate rows",
                    "Value": f"{len(data) - count:,}",
                },
            ],
        )

    @classmethod
    def _column_list(cls, data):
        names = ", ".join(str(column) for column in data.columns)
        return f"Available columns: {names}.", [
            {"Metric": "Column count", "Value": len(data.columns)},
            {"Metric": "Column names", "Value": names},
        ]

    @classmethod
    def _row_count(cls, data):
        return f"Your dataset contains {len(data):,} rows.", [
            {"Metric": "Dataset rows", "Value": f"{len(data):,}"},
            {"Metric": "Dataset columns", "Value": f"{len(data.columns):,}"},
        ]

    @classmethod
    def _correlation(cls, data):
        numeric = data.select_dtypes(include="number")
        if numeric.shape[1] < 2:
            return "Correlation needs at least two numeric columns.", []

        matrix = numeric.corr()
        pairs = []
        for i, first in enumerate(matrix.columns):
            for second in matrix.columns[i + 1:]:
                value = matrix.loc[first, second]
                if pd.notna(value):
                    pairs.append((
                        abs(float(value)), str(first), str(second), float(value)
                    ))

        pairs.sort(reverse=True)
        if not pairs:
            return "Not enough valid numeric values for correlation.", []

        details = [
            {
                "Metric": f"{first} ↔ {second}",
                "Value": f"{value:+.3f}",
            }
            for _, first, second, value in pairs[:10]
        ]
        strength, first, second, value = pairs[0]
        label = (
            "strong" if strength >= 0.7
            else "moderate" if strength >= 0.4
            else "weak"
        )
        return (
            f"The strongest numeric relationship is between {first} and "
            f"{second}: {value:+.3f} ({label} linear correlation). "
            "Correlation indicates association, not causation."
        ), details

    @classmethod
    def _ranked_values(cls, question, data):
        """Rank a dimension using the requested numeric metric."""
        q = cls._normalise(question)
        dimension = cls._find_dimension(question, data)

        if dimension is None:
            return None

        metric = cls._find_metric_column(
            question, data, exclude=[dimension]
        )

        if metric is None:
            numeric = list(data.select_dtypes(include="number").columns)
            for preferred in cls.METRIC_PREFERENCES:
                for candidate in numeric:
                    if cls._column_name(candidate) == preferred:
                        metric = candidate
                        break
                if metric is not None:
                    break

        ascending = bool(re.search(
            r"\b(bottom|lowest|least|worst|smallest|fewest)\b", q
        ))

        if metric is not None:
            temp = data[[dimension, metric]].copy()
            temp[metric] = pd.to_numeric(temp[metric], errors="coerce")
            grouped = temp.groupby(
                dimension, dropna=False
            )[metric].sum(min_count=1).dropna()
            grouped = grouped.sort_values(ascending=ascending).head(10)

            if grouped.empty:
                return f"No usable values to rank {dimension} by {metric}.", []

            details = [
                {
                    "Metric": cls._format_value(key),
                    "Value": cls._format_number(value),
                }
                for key, value in grouped.items()
            ]
            summary = ", ".join(
                f"{cls._format_value(key)} ({cls._format_number(value)})"
                for key, value in list(grouped.items())[:5]
            )
            rank_label = "Lowest" if ascending else "Highest"
            return (
                f"{rank_label} {dimension} by total {metric}: {summary}. "
                "Values are aggregated across the active dataset."
            ), details

        counts = data[dimension].value_counts(dropna=False).head(10)
        details = [
            {"Metric": cls._format_value(key), "Value": f"{int(value):,}"}
            for key, value in counts.items()
        ]
        summary = ", ".join(
            f"{cls._format_value(key)} ({int(value):,} records)"
            for key, value in list(counts.items())[:5]
        )
        return f"Most frequent values in {dimension}: {summary}.", details

    @classmethod
    def _trend(cls, question, data):
        q = cls._normalise(question)
        date_column = cls._find_date_column(data)

        if date_column is None:
            return "I couldn't identify a date column for trend analysis.", []

        metric = cls._find_metric_column(question, data)
        if metric is None:
            numeric = list(data.select_dtypes(include="number").columns)
            metric = numeric[0] if numeric else None

        if metric is None:
            return "Trend analysis requires a numeric measure.", []

        temp = pd.DataFrame({
            "_date": pd.to_datetime(data[date_column], errors="coerce"),
            "_value": pd.to_numeric(data[metric], errors="coerce"),
        }).dropna()

        if temp.empty:
            return "No valid date and numeric values were found.", []

        if re.search(r"\b(yearly|per year|by year|annual)\b", q):
            temp["_period"] = temp["_date"].dt.to_period("Y").astype(str)
            label = "year"
        elif re.search(r"\b(weekly|per week|by week)\b", q):
            temp["_period"] = temp["_date"].dt.to_period("W").astype(str)
            label = "week"
        elif re.search(r"\b(daily|per day|by day)\b", q):
            temp["_period"] = temp["_date"].dt.strftime("%Y-%m-%d")
            label = "day"
        elif re.search(r"\b(quarterly|per quarter|by quarter)\b", q):
            temp["_period"] = temp["_date"].dt.to_period("Q").astype(str)
            label = "quarter"
        else:
            temp["_period"] = temp["_date"].dt.to_period("M").astype(str)
            label = "month"

        grouped = temp.groupby("_period")["_value"].sum().sort_index()
        details = [
            {"Metric": str(period), "Value": cls._format_number(value)}
            for period, value in grouped.tail(12).items()
        ]

        first_period, first_value = grouped.index[0], grouped.iloc[0]
        last_period, last_value = grouped.index[-1], grouped.iloc[-1]

        if len(grouped) > 1 and first_value != 0:
            change = (
                (last_value - first_value) / abs(first_value)
            ) * 100
            change_text = f"{change:+.2f}%"
        elif len(grouped) > 1:
            change_text = "N/A (starting value is zero)"
        else:
            change_text = "N/A (only one period)"

        direction = (
            "increased" if last_value > first_value
            else "decreased" if last_value < first_value
            else "remained unchanged"
        )
        return (
            f"{metric} {direction} from {first_period} "
            f"({cls._format_number(first_value)}) to {last_period} "
            f"({cls._format_number(last_value)}). Change between the first "
            f"and last {label}: {change_text}. Showing the latest "
            f"{min(12, len(grouped))} periods."
        ), details

    @classmethod
    def _compare_categories(cls, question, data):
        dimension = cls._find_dimension(question, data)
        if dimension is None:
            return None

        metric = cls._find_metric_column(
            question, data, exclude=[dimension]
        )
        if metric is None:
            numeric = list(data.select_dtypes(include="number").columns)
            metric = numeric[0] if len(numeric) == 1 else None

        if metric is None:
            return (
                "I identified a category but couldn't identify a numeric "
                "measure. Try 'Compare regions by revenue'."
            ), []

        temp = data[[dimension, metric]].copy()
        temp[metric] = pd.to_numeric(temp[metric], errors="coerce")
        grouped = temp.groupby(
            dimension, dropna=False
        )[metric].sum(min_count=1).dropna().sort_values(ascending=False)

        if grouped.empty:
            return f"No usable values were found for {metric}.", []

        details = [
            {"Metric": cls._format_value(key), "Value": cls._format_number(value)}
            for key, value in grouped.head(10).items()
        ]
        highest_key, highest_value = grouped.index[0], grouped.iloc[0]
        lowest_key, lowest_value = grouped.index[-1], grouped.iloc[-1]

        return (
            f"Comparing total {metric} by {dimension}: highest is "
            f"{cls._format_value(highest_key)} "
            f"({cls._format_number(highest_value)}); lowest is "
            f"{cls._format_value(lowest_key)} "
            f"({cls._format_number(lowest_value)})."
        ), details

    @classmethod
    def _analyse(cls, question, data):
        q = cls._normalise(question)

        # Dataset overview / summary.
        if re.search(
            r"\b(summary|summarize|summarise|overview|describe)\b", q
        ) or (
            re.search(r"\b(complete|full|entire|overall)\b", q)
            and re.search(r"\b(dataset|data|table|summary|overview)\b", q)
        ):
            return cls._overview(data)

        if re.search(
            r"\b(column names|list columns|show columns|schema|fields)\b", q
        ):
            return cls._column_list(data)

        if (
            re.search(r"\b(rows|records|entries|observations)\b", q)
            and re.search(r"\b(count|many|number|how|total)\b", q)
        ) or q in {"row count", "record count", "number of rows"}:
            return cls._row_count(data)

        if re.search(
            r"\b(missing|null|empty|blank|incomplete|na values)\b", q
        ):
            return cls._missing_values(data)

        if re.search(
            r"\b(duplicate|duplicates|repeated rows|duplicate records)\b", q
        ):
            return cls._duplicate_rows(data)

        if re.search(
            r"\b(correlation|correlate|correlations|numeric relationship|"
            r"relationship between numeric)\b", q
        ):
            return cls._correlation(data)

        if re.search(
            r"\b(trend|trends|over time|time series|monthly|weekly|daily|"
            r"yearly|quarterly|annual|growth|year over year)\b", q
        ):
            return cls._trend(question, data)

        if re.search(r"\b(compare|comparison|versus|vs)\b", q):
            result = cls._compare_categories(question, data)
            if result is not None:
                return result

        if re.search(
            r"\b(top|highest|lowest|bottom|best|worst|most|least|"
            r"largest|smallest|fewest|best selling|popular)\b", q
        ):
            result = cls._ranked_values(question, data)
            if result is not None:
                return result

        column = cls._find_column(question, data)
        if column is None:
            return (
                "I couldn't confidently identify what to analyse. "
                f"Available columns: {', '.join(str(c) for c in data.columns)}. "
                "Try asking for a dataset summary, average revenue, top "
                "products, highest-revenue region, monthly trends, missing "
                "values, duplicates, or correlations."
            ), [
                {"Metric": "Rows", "Value": f"{len(data):,}"},
                {"Metric": "Columns", "Value": f"{len(data.columns):,}"},
            ]

        series = data[column]
        numeric = cls._numeric(data, column)
        valid = numeric.dropna()
        name = str(column)

        if pd.api.types.is_numeric_dtype(series) or not valid.empty:
            if re.search(r"\b(avg|average|mean)\b", q):
                value, label = valid.mean(), f"Average {name}"
            elif re.search(r"\b(total|sum|overall total)\b", q):
                value, label = valid.sum(), f"Total {name}"
            elif re.search(r"\bmedian\b", q):
                value, label = valid.median(), f"Median {name}"
            elif re.search(r"\b(max|maximum|highest|largest|peak)\b", q):
                value, label = valid.max(), f"Highest {name}"
            elif re.search(r"\b(min|minimum|lowest|smallest)\b", q):
                value, label = valid.min(), f"Lowest {name}"
            elif re.search(r"\b(count|how many|number of values)\b", q):
                return (
                    f"There are {len(valid):,} valid numeric values in {name}."
                ), [
                    {"Metric": "Valid values", "Value": f"{len(valid):,}"},
                    {
                        "Metric": "Missing/non-numeric",
                        "Value": f"{len(series) - len(valid):,}",
                    },
                ]
            else:
                stats = [
                    ("Minimum", valid.min()),
                    ("Maximum", valid.max()),
                    ("Average", valid.mean()),
                ]
                return (
                    f"{name}: " + ", ".join(
                        f"{label.lower()} {cls._format_number(value)}"
                        for label, value in stats
                    ) + "."
                ), [
                    {"Metric": label, "Value": cls._format_number(value)}
                    for label, value in stats
                ]

            formatted = cls._format_number(value)
            return f"{label} is {formatted}.", [
                {"Metric": label, "Value": formatted},
                {"Metric": "Valid values", "Value": f"{len(valid):,}"},
                {
                    "Metric": "Missing/non-numeric",
                    "Value": f"{len(series) - len(valid):,}",
                },
            ]

        if re.search(r"\b(unique|distinct|different)\b", q):
            count = int(series.nunique(dropna=True))
            return f"{name} has {count:,} unique non-empty values.", [
                {"Metric": "Unique values", "Value": f"{count:,}"},
                {
                    "Metric": "Non-empty values",
                    "Value": f"{int(series.notna().sum()):,}",
                },
            ]

        if re.search(r"\b(count|how many|number)\b", q):
            return (
                f"There are {int(series.notna().sum()):,} non-empty values "
                f"in {name}, with {int(series.nunique(dropna=True)):,} unique values."
            ), [
                {
                    "Metric": "Non-empty values",
                    "Value": f"{int(series.notna().sum()):,}",
                },
                {
                    "Metric": "Unique values",
                    "Value": f"{int(series.nunique(dropna=True)):,}",
                },
            ]

        counts = series.value_counts(dropna=False).head(10)
        details = [
            {"Metric": cls._format_value(key), "Value": f"{int(value):,}"}
            for key, value in counts.items()
        ]
        summary = ", ".join(
            f"{cls._format_value(key)} ({int(value):,})"
            for key, value in list(counts.items())[:5]
        )
        return f"Most common values in {name}: {summary}.", details

    @classmethod
    def _generate_sql(cls, question, data):
        """Generate illustrative SQL only; never execute it."""
        q = cls._normalise(question)

        if data is None or data.empty:
            return "-- Load a non-empty dataset to generate SQL."

        if re.search(
            r"\b(summary|summarize|summarise|overview|describe)\b", q
        ):
            return (
                "SELECT COUNT(*) AS total_rows FROM dataset;\n"
                "-- Other summary statistics are calculated locally with Pandas.\n"
                "-- Preview only; not executed."
            )

        if re.search(r"\b(missing|null|empty|blank|incomplete)\b", q):
            return (
                "-- Missing/blank-value analysis is calculated locally with Pandas.\n"
                "-- SQL syntax for blank strings varies by database."
            )

        if re.search(r"\b(duplicate|duplicates|repeated rows)\b", q):
            return (
                "-- Duplicate-row analysis is calculated locally with Pandas.\n"
                "-- Exact SQL depends on the database and table schema."
            )

        if re.search(
            r"\b(correlation|correlate|correlations|numeric relationship)\b", q
        ):
            return (
                "-- Correlation is calculated locally with Pandas.\n"
                "-- Correlation functions vary by database."
            )

        if (
            re.search(r"\b(rows|records|entries|observations)\b", q)
            and re.search(r"\b(count|many|number|how|total)\b", q)
        ) or q in {"row count", "record count", "number of rows"}:
            return "SELECT COUNT(*) AS row_count FROM dataset;"

        if re.search(r"\b(column names|list columns|show columns|schema)\b", q):
            return "-- Inspect the dataset schema using database metadata."

        if re.search(
            r"\b(trend|trends|over time|monthly|weekly|daily|yearly|"
            r"quarterly|annual|growth|time series)\b", q
        ):
            date_column = cls._find_date_column(data)
            metric = cls._find_metric_column(question, data)

            if metric is None:
                numeric = list(data.select_dtypes(include="number").columns)
                metric = numeric[0] if numeric else None

            if date_column is None or metric is None:
                return "-- Trend analysis needs a date column and numeric measure."

            date_sql = "`" + str(date_column).replace("`", "``") + "`"
            metric_sql = "`" + str(metric).replace("`", "``") + "`"

            if re.search(r"\b(yearly|per year|by year|annual)\b", q):
                period = f"YEAR({date_sql})"
            elif re.search(r"\b(weekly|per week|by week)\b", q):
                period = f"YEARWEEK({date_sql})"
            elif re.search(r"\b(daily|per day|by day)\b", q):
                period = f"DATE({date_sql})"
            elif re.search(r"\b(quarterly|per quarter|by quarter)\b", q):
                period = f"CONCAT(YEAR({date_sql}), '-Q', QUARTER({date_sql}))"
            else:
                period = f"DATE_FORMAT({date_sql}, '%Y-%m')"

            return (
                f"SELECT {period} AS period, SUM({metric_sql}) AS total_value\n"
                "FROM dataset\n"
                "GROUP BY period\n"
                "ORDER BY period;\n"
                "-- Preview only; not executed."
            )

        if re.search(r"\b(compare|comparison|versus|vs)\b", q) or re.search(
            r"\b(top|highest|lowest|bottom|best|worst|most|least|largest|smallest)\b",
            q,
        ):
            dimension = cls._find_dimension(question, data)
            metric = cls._find_metric_column(
                question, data, exclude=[dimension] if dimension is not None else []
            )

            if dimension is not None:
                dim_sql = "`" + str(dimension).replace("`", "``") + "`"
                if metric is not None:
                    metric_sql = "`" + str(metric).replace("`", "``") + "`"
                    order = (
                        "ASC" if re.search(
                            r"\b(bottom|lowest|least|worst|smallest|fewest)\b", q
                        ) else "DESC"
                    )
                    return (
                        f"SELECT {dim_sql}, SUM({metric_sql}) AS total_value\n"
                        "FROM dataset\n"
                        f"GROUP BY {dim_sql}\n"
                        f"ORDER BY total_value {order}\n"
                        "LIMIT 10;\n"
                        "-- Preview only; not executed."
                    )
                return (
                    f"SELECT {dim_sql}, COUNT(*) AS record_count\n"
                    "FROM dataset\n"
                    f"GROUP BY {dim_sql}\n"
                    "ORDER BY record_count DESC\n"
                    "LIMIT 10;\n"
                    "-- Preview only; not executed."
                )

        column = cls._find_column(question, data)
        if column is None:
            return (
                "SELECT * FROM dataset LIMIT 20;\n"
                "-- Generic preview only; not executed."
            )

        safe = "`" + str(column).replace("`", "``") + "`"
        if re.search(r"\b(avg|average|mean)\b", q):
            return f"SELECT AVG({safe}) AS average_value FROM dataset;"
        if re.search(r"\b(total|sum|overall total)\b", q):
            return f"SELECT SUM({safe}) AS total_value FROM dataset;"
        if re.search(r"\b(median)\b", q):
            return "-- Median is calculated locally with Pandas."
        if re.search(r"\b(max|maximum|highest|largest|peak)\b", q):
            return f"SELECT MAX({safe}) AS highest_value FROM dataset;"
        if re.search(r"\b(min|minimum|lowest|smallest)\b", q):
            return f"SELECT MIN({safe}) AS lowest_value FROM dataset;"
        if re.search(r"\b(count|how many|number of values)\b", q):
            return f"SELECT COUNT({safe}) AS non_null_count FROM dataset;"

        return (
            "SELECT * FROM dataset LIMIT 20;\n"
            "-- Preview only; not executed."
        )