import math


def fmt_number(value):
    try:
        value = float(value)
        if math.isfinite(value):
            return f"{value:,.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        pass
    return "—"


def friendly_error(exc):
    return str(exc).strip() or "The operation could not be completed."


def numeric_columns(frame):
    return list(frame.select_dtypes(include="number").columns) if frame is not None else []


def text_columns(frame):
    if frame is None:
        return []
    return list(frame.select_dtypes(include=["object", "string", "category"]).columns)