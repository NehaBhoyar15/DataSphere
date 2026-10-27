
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="DataSphere | AI Analytics",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- THEME ----------------
st.markdown("""
<style>
:root {
    --lavender: #F1EAFD;
    --purple: #6849B7;
    --navy: #302447;
    --text: #514364;
    --border: #E3D9F7;
}
.stApp {
    background: linear-gradient(135deg, #FBF9FF, #F5F0FF);
    color: var(--text);
}
[data-testid="stSidebar"] {
    background: linear-gradient(145deg, #FBF9FF, #F1EAFD);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}
.brand {
    color: #403354;
    font-size: 29px;
    font-weight: 800;
    letter-spacing: -1px;
}
.subtitle {
    color: #9182AC;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
}
.section-label {
    color: #9182AC;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin: 18px 0 8px;
}
.hero {
    padding: 26px 30px;
    border-radius: 22px;
    background: linear-gradient(120deg, #E9DFFF, #FFFFFF);
    border: 1px solid #D8CAFF;
    margin-bottom: 24px;
}
.hero h1 {
    color: #30205F;
    font-size: 32px;
    margin: 0;
}
.hero p {
    color: #665B87;
    font-size: 15px;
    margin: 8px 0 0;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #E4DCF7;
    box-shadow: 0 3px 12px #4830780A;
}
div[data-testid="stMetricLabel"] {
    color: #796A96;
}
div[data-testid="stMetricValue"] {
    color: #302447;
}
.stButton > button {
    border-radius: 10px;
    border: 1px solid #DCCEF7;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #E4DCF7;
    border-radius: 12px;
}
hr {
    border-color: #E4DAF5;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
PAGES = [
    ("▦", "Dashboard"),
    ("▤", "Data"),
    ("⌁", "Charts"),
    ("◇", "ML"),
    ("◎", "Clustering"),
    ("◌", "NLP"),
    ("✧", "AI Assistant"),
    ("◷", "Forecasting"),
    ("⚙", "Settings"),
]

with st.sidebar:
    st.markdown('<div class="brand">◈ DataSphere</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="subtitle">YOUR AI COMPANION</div>',
                unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="section-label">WORKSPACE</div>',
                unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    for icon, name in PAGES:
        if st.button(
            f"{icon}    {name}",
            key=f"nav_{name}",
            use_container_width=True,
            type="primary" if st.session_state.page == name else "secondary",
        ):
            st.session_state.page = name
            st.rerun()

    st.divider()
    st.info("●  WORKSPACE READY")
    st.caption("Your data. Your insights.")

page = st.session_state.page

# ---------------- DATA ----------------
if "data" not in st.session_state:
    dates = pd.date_range(end=pd.Timestamp.today(), periods=100)
    rng = np.random.default_rng(42)
    st.session_state.data = pd.DataFrame({
        "Date": dates,
        "Product": rng.choice(
            ["Laptop", "Mobile", "Tablet", "Headphones"], 100
        ),
        "Region": rng.choice(
            ["North", "South", "East", "West"], 100
        ),
        "Units Sold": rng.integers(1, 20, 100),
        "Revenue": rng.integers(1000, 25000, 100),
    })

df = st.session_state.data

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <h1>DataSphere</h1>
    <p>Transforming data into intelligence powered by AI</p>
</div>
""", unsafe_allow_html=True)

# ---------------- PAGE CONTENT ----------------
if page == "Dashboard":
    st.subheader("Executive Overview")
    st.caption("Your data at a glance.")

    uploaded = st.file_uploader(
        "Upload dataset (CSV or Excel)",
        type=["csv", "xlsx"],
        key="dashboard_upload",
    )
    if uploaded:
        try:
            df = (pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv")
                  else pd.read_excel(uploaded))
            st.session_state.data = df
        except Exception as exc:
            st.error(f"Unable to load dataset: {exc}")

    df = st.session_state.data
    revenue_col = next(
        (c for c in df.columns if str(c).lower() in ["revenue", "sales"]),
        None,
    )
    units_col = next(
        (c for c in df.columns if str(c).lower() in
         ["units sold", "quantity", "units"]),
        None,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"{df[revenue_col].sum():,.0f}"
              if revenue_col else "—")
    c2.metric("Units Sold", f"{df[units_col].sum():,.0f}"
              if units_col else "—")
    c3.metric("Columns", len(df.columns))
    c4.metric("Total Records", len(df))

    left, right = st.columns(2)
    with left:
        st.subheader("Dataset Preview")
        st.dataframe(df.head(8), use_container_width=True)
    with right:
        st.subheader("Smart Insights")
        st.write(f"Your dataset contains **{len(df):,} records**.")
        st.write(f"Available columns: **{len(df.columns)}**.")
        if revenue_col:
            st.write(f"Total revenue: **{df[revenue_col].sum():,.2f}**.")
            if not df.empty:
                st.write(f"Highest revenue: **{df[revenue_col].max():,.2f}**.")

    if revenue_col:
        st.subheader("Revenue Trend")
        if "Date" in df.columns:
            chart_df = df.copy()
            chart_df["Date"] = pd.to_datetime(
                chart_df["Date"], errors="coerce"
            )
            chart_df = chart_df.dropna(subset=["Date"])
            if not chart_df.empty:
                st.line_chart(
                    chart_df.groupby("Date")[revenue_col].sum()
                )
        else:
            st.bar_chart(df.groupby(df.columns[0])[revenue_col].sum())

elif page == "Data":
    st.subheader("Data Explorer")
    uploaded = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx"],
        key="data_page_upload",
    )
    if uploaded:
        try:
            df = (pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv")
                  else pd.read_excel(uploaded))
            st.session_state.data = df
        except Exception as exc:
            st.error(f"Unable to load dataset: {exc}")

    df = st.session_state.data
    search = st.text_input("Search across your dataset")
    if search:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        df = df[mask]

    st.caption(f"{len(df):,} records shown")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        "datasphere_data.csv",
        "text/csv",
    )

elif page == "Charts":
    st.subheader("Charts & Visualization")
    st.caption("Explore numeric columns in your dataset.")
    numeric = df.select_dtypes(include="number").columns.tolist()
    if numeric:
        metric = st.selectbox("Select metric", numeric)
        if len(df.columns) > 0:
            group = st.selectbox("Group by", df.columns.tolist())
            st.bar_chart(df.groupby(group, dropna=False)[metric].sum())
            st.line_chart(df.groupby(group, dropna=False)[metric].sum())
    else:
        st.info("Upload a dataset containing numeric columns to create charts.")

elif page == "ML":
    st.subheader("Machine Learning")
    st.info("ML workspace")
    st.write("Preview your data and select a target column to prepare a model.")
    st.dataframe(df.head(10), use_container_width=True)
    target = st.selectbox("Target column", df.columns.tolist())
    if st.button("Prepare ML Dataset"):
        st.session_state.ml_target = target
        st.success(f"Target selected: {target}. Model training needs to be connected.")

elif page == "Clustering":
    st.subheader("Clustering")
    numeric = df.select_dtypes(include="number").columns.tolist()
    if len(numeric) >= 2:
        x_col = st.selectbox("X feature", numeric, index=0)
        y_col = st.selectbox("Y feature", numeric, index=1)
        st.scatter_chart(df, x=x_col, y=y_col)
        st.caption("Interactive feature preview. Clustering model is not connected yet.")
    else:
        st.info("Upload at least two numeric columns to explore clustering.")

elif page == "NLP":
    st.subheader("Natural Language Processing")
    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    if text_cols:
        col = st.selectbox("Text column", text_cols)
        st.dataframe(df[[col]].head(20), use_container_width=True)
        st.caption("Text preview ready. NLP training and sentiment analysis need to be connected.")
    else:
        st.info("Upload a dataset with a text column to begin NLP analysis.")

elif page == "AI Assistant":
    st.subheader("How can I assist you today?")
    st.caption("Ask questions about the current dataset.")
    question = st.text_input(
        "Your question",
        placeholder="Example: Show total revenue by product",
    )
    if st.button("Analyse", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            st.info("Natural-language AI analysis is not connected yet.")
            st.write("Dataset shape:", df.shape)
            st.write("Available columns:", ", ".join(map(str, df.columns)))
            st.dataframe(df.head(10), use_container_width=True)

elif page == "Forecasting":
    st.subheader("Forecasting")
    numeric = df.select_dtypes(include="number").columns.tolist()
    if numeric:
        metric = st.selectbox("Metric to forecast", numeric)
        horizon = st.slider("Forecast horizon (periods)", 1, 30, 7)
        st.line_chart(df[metric].reset_index(drop=True))
        st.caption(
            f"Selected {metric} for a {horizon}-period forecast. "
            "Forecast model is not connected yet."
        )
    else:
        st.info("Upload numeric data to prepare forecasting.")

elif page == "Settings":
    st.subheader("Settings")
    st.write("DataSphere web workspace")
    st.write(f"Rows: {len(df):,}")
    st.write(f"Columns: {len(df.columns)}")
    st.write("Theme: Lavender / White / Navy")
    st.write("Current session data is stored in memory.")
    if st.button("Reset demo dataset"):
        del st.session_state.data
        st.rerun()

st.divider()
st.caption("DataSphere • Transforming data into intelligence powered by AI")
