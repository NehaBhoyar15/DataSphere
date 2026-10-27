"""Chart rendering and export helpers shared by the dashboard and chart
studio pages. All methods are static: callers pass in the Matplotlib axes
from their own ``ChartWidget`` instance."""
import pandas as pd


class ChartService:
    TYPES = ("Bar", "Line", "Pie", "Scatter", "Histogram", "Box Plot")

    @staticmethod
    def render(ax, frame, chart_type, x=None, y=None, color=None, title=None):
        ax.clear()
        chart_type = (chart_type or "").strip().lower()

        if frame is None or frame.empty or not x or x not in frame.columns:
            ax.text(0.5, 0.5, "Choose fields to explore the local dataset.",
                     ha="center", va="center", color="#94a3b8")
            ax.set_axis_off()
            return ax

        try:
            if chart_type == "histogram":
                data = pd.to_numeric(frame[x], errors="coerce").dropna()
                ax.hist(data, bins=min(30, max(5, int(len(data) ** 0.5))), color="#60a5fa")
                ax.set_xlabel(x)
            elif chart_type == "pie":
                if y and y in frame.columns:
                    grouped = frame.groupby(x)[y].sum()
                else:
                    grouped = frame[x].value_counts()
                grouped = grouped.head(8)
                ax.pie(grouped.values, labels=[str(v) for v in grouped.index], autopct="%1.0f%%")
            elif chart_type == "box plot" or chart_type == "boxplot":
                if y and y in frame.columns:
                    groups = [g.dropna().to_numpy() for _, g in frame.groupby(x)[y]]
                    labels = [str(k) for k in frame.groupby(x)[y].groups.keys()]
                    ax.boxplot(groups, labels=labels)
                    ax.set_ylabel(y)
                else:
                    values = pd.to_numeric(frame[x], errors="coerce").dropna()
                    ax.boxplot(values)
                ax.set_xlabel(x)
            elif chart_type == "scatter":
                xs = pd.to_numeric(frame[x], errors="coerce")
                ys = pd.to_numeric(frame[y], errors="coerce") if y and y in frame.columns else xs
                if color and color in frame.columns:
                    codes = frame[color].astype("category").cat.codes
                    ax.scatter(xs, ys, c=codes, cmap="viridis", s=30)
                else:
                    ax.scatter(xs, ys, color="#60a5fa", s=30)
                ax.set_xlabel(x); ax.set_ylabel(y or "")
            elif chart_type == "line":
                plot_frame = frame
                x_vals = pd.to_datetime(plot_frame[x], errors="coerce")
                if x_vals.notna().sum() == 0:
                    x_vals = plot_frame[x]
                if y and y in plot_frame.columns:
                    if color and color in plot_frame.columns:
                        for key, group in plot_frame.groupby(color):
                            gx = pd.to_datetime(group[x], errors="coerce")
                            gx = gx if gx.notna().sum() else group[x]
                            ax.plot(gx, group[y], label=str(key))
                        ax.legend()
                    else:
                        ax.plot(x_vals, plot_frame[y], color="#60a5fa")
                ax.set_xlabel(x); ax.set_ylabel(y or "")
                ax.figure.autofmt_xdate()
            else:  # bar (default)
                if y and y in frame.columns:
                    grouped = frame.groupby(x)[y].mean().head(30)
                else:
                    grouped = frame[x].value_counts().head(30)
                ax.bar([str(v) for v in grouped.index], grouped.values, color="#60a5fa")
                ax.set_xlabel(x); ax.set_ylabel(y or "count")
                ax.tick_params(axis="x", rotation=45)
        except Exception as exc:
            ax.clear()
            ax.text(0.5, 0.5, f"Could not render chart: {exc}", ha="center", va="center",
                     color="#f87171", wrap=True)
            ax.set_axis_off()
            return ax

        if title:
            ax.set_title(title)
        return ax

    @staticmethod
    def export_png(figure, path):
        figure.savefig(path, format="png", dpi=150, bbox_inches="tight")
        return True

    @staticmethod
    def export_svg(figure, path):
        figure.savefig(path, format="svg", bbox_inches="tight")
        return True

    @staticmethod
    def export_html(frame, chart_type, x, y, title, path):
        try:
            import plotly.express as px
        except ImportError:
            return False

        chart_type = (chart_type or "").strip().lower()
        try:
            if chart_type == "histogram":
                fig = px.histogram(frame, x=x, title=title)
            elif chart_type == "pie":
                fig = px.pie(frame, names=x, values=y if y in frame.columns else None, title=title)
            elif chart_type in ("box plot", "boxplot"):
                fig = px.box(frame, x=x, y=y if y in frame.columns else None, title=title)
            elif chart_type == "scatter":
                fig = px.scatter(frame, x=x, y=y, title=title)
            elif chart_type == "line":
                fig = px.line(frame, x=x, y=y, title=title)
            else:
                fig = px.bar(frame, x=x, y=y if y in frame.columns else None, title=title)
        except Exception:
            return False

        fig.write_html(path)
        return True
