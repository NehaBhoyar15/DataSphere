
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="DataSphere | AI Analytics",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #faf8ff, #f0ebff);
    color: #242044;
}
[data-testid="stSidebar"] {
    background: #eee8ff;
    border-right: 1px solid #ded3ff;
}
.hero {
    padding: 28px;
    border-radius: 22px;
    background: linear-gradient(120deg, #e6ddff, #ffffff);
    border: 1px solid #d8caff;
    margin-bottom: 22px;
}
.hero h1 { color: #30205f; margin-bottom: 5px; }
.hero p { color: #665b87; font-size: 16px; }
div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #e4dcf7;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("# 🔮 DataSphere")
st.sidebar.caption("YOUR AI COMPANION")
page = st.sidebar.radio(
    "NAVIGATION",
    ["Dashboard", "Data Explorer", "AI Assistant"],
)
st.sidebar.divider()
st.sidebar.success("● Ready to analyse")

st.markdown("""
<div class="hero">
    <h1>DataSphere</h1>
    <p>Transforming data into intelligence powered by AI</p>
</div>
""", unsafe_allow_html=True)

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

if page == "Dashboard":
    st.subheader("Executive Overview")
    st.caption("Explore your data and discover useful patterns.")

    uploaded = st.file_uploader(
        "Upload your dataset (CSV or Excel)",
        type=["csv", "xlsx"],
    )
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.session_state.data = df
            st.success("Dataset loaded successfully.")
        except Exception as exc:
            st.error(f"Could not load file: {exc}")

    c1, c2, c3, c4 = st.columns(4)
    numeric = df.select_dtypes(include="number")
    revenue_col = next(
        (c for c in df.columns if c.lower() in ["revenue", "sales"]),
        None,
    )
    units_col = next(
        (c for c in df.columns if c.lower() in
         ["units sold", "quantity", "units"]),
        None,
    )

    with c1:
        total = df[revenue_col].sum() if revenue_col else 0
        st.metric("Total Revenue", f"{total:,.0f}")
    with c2:
        units = df[units_col].sum() if units_col else len(df)
        st.metric("Units / Records", f"{units:,.0f}")
    with c3:
        st.metric("Columns", len(df.columns))
    with c4:
        st.metric("Total Records", len(df))

    st.subheader("Dataset Preview")
    st.dataframe(df.head(10), use_container_width=True)

    if revenue_col:
        st.subheader("Revenue Distribution")
        st.bar_chart(df.groupby(
            df.columns[0], dropna=False
        )[revenue_col].sum().head(20))

elif page == "Data Explorer":
    st.subheader("Data Explorer")
    uploaded = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx"],
        key="data_upload",
    )
    if uploaded:
        try:
            df = (
                pd.read_csv(uploaded)
                if uploaded.name.endswith(".csv")
                else pd.read_excel(uploaded)
            )
            st.session_state.data = df
        except Exception as exc:
            st.error(f"Could not load file: {exc}")

    df = st.session_state.data
    search = st.text_input("Search across dataset")
    if search:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        df = df[mask]

    st.write(f"Showing {len(df)} records")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="datasphere_data.csv",
        mime="text/csv",
    )

elif page == "AI Assistant":
    st.subheader("How can I assist you today?")
    st.write("Ask a question about your uploaded dataset.")

    question = st.text_input(
        "Your question",
        placeholder="Example: Show total revenue by product",
    )
    if st.button("Analyse", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            st.info(
                "Starter version: dataset loaded, but natural-language "
                "AI analysis is not connected yet."
            )
            st.write("Dataset shape:", df.shape)
            st.write("Available columns:", ", ".join(map(str, df.columns)))
            st.dataframe(df.head(10), use_container_width=True)

st.divider()
st.caption("DataSphere • AI-powered data exploration")
