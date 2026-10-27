# AI Data Analytics Assistant v1.0

A complete, PyQt5-based Person 3 desktop application for the internship deliverable.
It launches independently with a local demo dataset, so the GUI remains useful even
when Person 1's model backend, Person 2's database, optional libraries, or Claude are
not available.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Exact launch command: `python main.py`

## Test and package

```bash
pytest
pyinstaller analytics_assistant.spec
```

Set `ANTHROPIC_API_KEY` in the environment to indicate that a project Claude
adapter is configured. The application never hardcodes or prints credentials.
Without it, AI Assistant intentionally displays a local demo response rather
than pretending an external API call succeeded.

## Person 3 coverage

- **Desktop foundation:** sidebar navigation, theme, cards, tooltips, splash screen, status bar, responsive file loading, recent files, settings, database connection UI, drag/drop.
- **Data UI:** CSV/Excel open, progress worker, raw `QTableView`, column types, row/column counts, missing values, search/filter, visible-column selector, reset/refresh.
- **Charts/dashboard:** bar, line, pie, scatter, histogram, box plot, date controls, embedded Matplotlib, PNG/SVG/Plotly HTML export, KPI cards, correlation heatmap, quality alert, JSON save/load.
- **ML results UI:** dataset/target/model selectors, test split, stratification, feature selection control, importance chart, metrics, experiment history, predictions, and adapter seam for Person 1.
- **Clustering:** K-Means, DBSCAN, cluster scatter, labels, profile-capable table, elbow curve, silhouette score, Isolation Forest anomaly highlighting, 2D PCA view.
- **NLP:** text selector, keyword extraction, sentiment results and chart, with local analysis that does not require downloading NLTK data.
- **AI assistant:** scrollable chat, local demo response, generated SQL, copy button, result table, clear conversation, environment-variable boundary.
- **Forecasting:** ARIMA, Prophet, Holt-Winters selectors, horizon slider, historical/predicted/confidence-band chart, forecast table, MAE/RMSE/MAPE scorecards, alert banner, graceful fallback.
- **Quality/packaging:** friendly errors, optional dependency handling, PyTest/PyTest-Qt coverage, PyInstaller spec.

The project intentionally does not implement Person 1's backend/model ownership or
Person 2's SQL/database ownership. It exposes UI-facing service adapters and safe
local implementations only where needed to keep the Person 3 demo runnable.