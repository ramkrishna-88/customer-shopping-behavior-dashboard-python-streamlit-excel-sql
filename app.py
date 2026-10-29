import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Customer Shopping Analytics", page_icon="🛍️", layout="wide")

ROOT = Path(__file__).parent
DEFAULT_DATA = ROOT / "data" / "customer_shopping_behavior.csv"
DB_PATH = ROOT / "outputs" / "shopping_behavior.db"

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f5f7fb; padding: 14px 16px; border-radius: 12px; border: 1px solid #e7eaf1;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_default_data():
    return pd.read_csv(DEFAULT_DATA)

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def find_col(df, options):
    for col in options:
        if col in df.columns:
            return col
    return None

st.sidebar.title("🛍️ Shopping Analytics")
st.sidebar.caption("Customer Shopping Behavior Analysis")
uploaded = st.sidebar.file_uploader("Use your own CSV (optional)", type=["csv"])

try:
    data = normalize_columns(pd.read_csv(uploaded)) if uploaded else normalize_columns(load_default_data())
except Exception as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.stop()

if data.empty:
    st.warning("The dataset is empty.")
    st.stop()

# Detect common fields so the app works with the included dataset and similar CSV files.
revenue_col = find_col(data, ["purchase_amount_usd", "revenue", "sales", "total_amount", "amount", "purchase_amount"])
category_col = find_col(data, ["category", "product_category", "item_category"])
customer_col = find_col(data, ["customer_id", "customerid", "user_id", "customer"])
age_col = find_col(data, ["age", "customer_age"])
gender_col = find_col(data, ["gender", "sex"])
season_col = find_col(data, ["season"])
payment_col = find_col(data, ["payment_method", "payment", "payment_type"])
discount_col = find_col(data, ["discount_applied", "discount", "has_discount"])
review_col = find_col(data, ["review_rating", "rating", "review"])
item_col = find_col(data, ["item_purchased", "product", "item", "product_name"])
month_col = find_col(data, ["month", "purchase_month", "date", "purchase_date"])
shipping_col = find_col(data, ["shipping_type", "shipping"])

if revenue_col:
    data[revenue_col] = pd.to_numeric(data[revenue_col], errors="coerce")
if age_col:
    data[age_col] = pd.to_numeric(data[age_col], errors="coerce")
if review_col:
    data[review_col] = pd.to_numeric(data[review_col], errors="coerce")

st.title("Customer Shopping Behavior Dashboard")
st.caption("Explore sales, customer segments, product categories, payment methods, and shopping patterns.")
st.info("This project ships with synthetic demonstration data. Results are illustrative, not real-company findings.")

# Sidebar filters
st.sidebar.subheader("Filters")
filtered = data.copy()
if category_col:
    options = sorted(filtered[category_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Product category", options, default=options)
    if chosen:
        filtered = filtered[filtered[category_col].astype(str).isin(chosen)]
if gender_col:
    options = sorted(filtered[gender_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Gender", options, default=options)
    if chosen:
        filtered = filtered[filtered[gender_col].astype(str).isin(chosen)]
if season_col:
    options = sorted(filtered[season_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Season", options, default=options)
    if chosen:
        filtered = filtered[filtered[season_col].astype(str).isin(chosen)]
if payment_col:
    options = sorted(filtered[payment_col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect("Payment method", options, default=options)
    if chosen:
        filtered = filtered[filtered[payment_col].astype(str).isin(chosen)]

# KPI cards
orders = len(filtered)
revenue = filtered[revenue_col].sum() if revenue_col else None
avg_order = filtered[revenue_col].mean() if revenue_col else None
customers = filtered[customer_col].nunique() if customer_col else None
rating = filtered[review_col].mean() if review_col else None

cols = st.columns(4)
cols[0].metric("Orders / Records", f"{orders:,}")
cols[1].metric("Total Revenue", f"${revenue:,.2f}" if revenue is not None else "N/A")
cols[2].metric("Average Order Value", f"${avg_order:,.2f}" if avg_order is not None else "N/A")
cols[3].metric("Unique Customers", f"{customers:,}" if customers is not None else "N/A")

overview, customers_tab, products_tab, data_tab, sql_tab = st.tabs([
    "📊 Overview", "👥 Customer Insights", "🛒 Product Insights", "📄 Data Explorer", "🧮 SQL Insights"
])

with overview:
    left, right = st.columns(2)
    with left:
        if category_col and revenue_col:
            summary = filtered.groupby(category_col, dropna=False)[revenue_col].sum().reset_index().sort_values(revenue_col, ascending=False)
            fig = px.bar(summary, x=category_col, y=revenue_col, title="Revenue by Category", text_auto=".2s")
            fig.update_layout(xaxis_title="", yaxis_title="Revenue")
            st.plotly_chart(fig, use_container_width=True)
        elif category_col:
            summary = filtered[category_col].value_counts().rename_axis(category_col).reset_index(name="orders")
            st.plotly_chart(px.bar(summary, x=category_col, y="orders", title="Orders by Category"), use_container_width=True)
        else:
            st.write("No category column found in this dataset.")
    with right:
        if payment_col:
            summary = filtered[payment_col].astype(str).value_counts().rename_axis("payment_method").reset_index(name="orders")
            st.plotly_chart(px.pie(summary, names="payment_method", values="orders", title="Payment Method Share", hole=.4), use_container_width=True)
        elif gender_col:
            summary = filtered[gender_col].astype(str).value_counts().rename_axis("gender").reset_index(name="customers")
            st.plotly_chart(px.pie(summary, names="gender", values="customers", title="Gender Distribution", hole=.4), use_container_width=True)
        else:
            st.write("No payment or gender column found.")
    if month_col and revenue_col:
        trend_data = filtered.copy()
        if "date" in month_col or "date" in str(trend_data[month_col].dtype).lower():
            parsed = pd.to_datetime(trend_data[month_col], errors="coerce")
            if parsed.notna().any():
                trend_data["_month"] = parsed.dt.to_period("M").astype(str)
            else:
                trend_data["_month"] = trend_data[month_col].astype(str)
        else:
            trend_data["_month"] = trend_data[month_col].astype(str)
        trend = trend_data.groupby("_month", dropna=False)[revenue_col].sum().reset_index()
        st.plotly_chart(px.line(trend, x="_month", y=revenue_col, markers=True, title="Revenue Trend"), use_container_width=True)
    if rating is not None:
        st.metric("Average Review Rating", f"{rating:.2f} / 5")

with customers_tab:
    c1, c2 = st.columns(2)
    with c1:
        if age_col:
            st.plotly_chart(px.histogram(filtered, x=age_col, nbins=15, title="Customer Age Distribution"), use_container_width=True)
        else:
            st.info("No age column found.")
    with c2:
        if gender_col and revenue_col:
            g = filtered.groupby(gender_col)[revenue_col].agg(["sum", "mean", "count"]).reset_index()
            g.columns = [gender_col, "total_revenue", "average_order_value", "orders"]
            st.plotly_chart(px.bar(g, x=gender_col, y="total_revenue", title="Revenue by Gender", text_auto=".2s"), use_container_width=True)
        elif gender_col:
            st.plotly_chart(px.histogram(filtered, x=gender_col, title="Customers by Gender"), use_container_width=True)
        else:
            st.info("No gender column found.")
    if discount_col and revenue_col:
        d = filtered.groupby(discount_col, dropna=False)[revenue_col].agg(["sum", "mean", "count"]).reset_index()
        d.columns = ["discount_applied", "total_revenue", "average_order_value", "orders"]
        st.subheader("Discount vs. Spending")
        st.dataframe(d, use_container_width=True, hide_index=True)

with products_tab:
    if item_col:
        item_counts = filtered[item_col].astype(str).value_counts().head(15).rename_axis("item").reset_index(name="orders")
        st.plotly_chart(px.bar(item_counts.sort_values("orders"), x="orders", y="item", orientation="h", title="Top 15 Purchased Items"), use_container_width=True)
    if category_col and revenue_col:
        cat = filtered.groupby(category_col)[revenue_col].agg(["sum", "mean", "count"]).reset_index()
        cat.columns = ["category", "total_revenue", "average_purchase", "orders"]
        st.subheader("Category Performance")
        st.dataframe(cat.sort_values("total_revenue", ascending=False), use_container_width=True, hide_index=True)
    if season_col and revenue_col:
        seas = filtered.groupby(season_col)[revenue_col].sum().reset_index()
        st.plotly_chart(px.bar(seas, x=season_col, y=revenue_col, title="Revenue by Season"), use_container_width=True)

with data_tab:
    st.subheader("Filtered Dataset")
    st.write(f"Showing {len(filtered):,} of {len(data):,} rows.")
    st.dataframe(filtered, use_container_width=True, height=420)
    st.download_button("⬇️ Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "filtered_shopping_data.csv", "text/csv")
    st.download_button("⬇️ Download filtered Excel", filtered.to_csv(index=False).encode("utf-8"), "filtered_shopping_data.csv", "text/csv", help="Downloads CSV, which opens in Excel.")

with sql_tab:
    st.subheader("SQL-style analysis")
    st.caption("These results are calculated from the currently filtered dataset. They mirror common SQL GROUP BY analyses.")
    query_choice = st.selectbox("Choose an analysis", [
        "Revenue by category", "Orders by payment method", "Revenue by season",
        "Average spend by gender", "Top purchased items", "Raw filtered rows"
    ])
    if query_choice == "Revenue by category" and category_col and revenue_col:
        result = filtered.groupby(category_col)[revenue_col].agg(["sum", "mean", "count"]).reset_index()
        result.columns = [category_col, "total_revenue", "average_order_value", "orders"]
    elif query_choice == "Orders by payment method" and payment_col:
        result = filtered[payment_col].value_counts().rename_axis(payment_col).reset_index(name="orders")
    elif query_choice == "Revenue by season" and season_col and revenue_col:
        result = filtered.groupby(season_col)[revenue_col].agg(["sum", "count"]).reset_index()
        result.columns = [season_col, "total_revenue", "orders"]
    elif query_choice == "Average spend by gender" and gender_col and revenue_col:
        result = filtered.groupby(gender_col)[revenue_col].agg(["mean", "sum", "count"]).reset_index()
        result.columns = [gender_col, "average_spend", "total_revenue", "orders"]
    elif query_choice == "Top purchased items" and item_col:
        result = filtered[item_col].value_counts().head(15).rename_axis(item_col).reset_index(name="orders")
    else:
        result = filtered.head(500)
        if query_choice != "Raw filtered rows":
            st.warning("The required columns for this analysis were not found, so raw rows are shown.")
    st.dataframe(result, use_container_width=True, hide_index=True)
    st.download_button("Download analysis result CSV", result.to_csv(index=False).encode("utf-8"), "sql_insight_result.csv", "text/csv")

with st.expander("How this dashboard works"):
    st.markdown("""
    - **Python / Pandas:** loads, cleans column names, filters, and calculates KPIs.
    - **Charts:** Plotly charts update when you change sidebar filters.
    - **SQL concepts:** the SQL Insights tab presents common grouping and aggregation analyses.
    - **Excel:** use the Data Explorer download to export filtered results and open them in Excel.
    """)
