"""
Customer Shopping Behavior Analysis
Run: python analysis.py
Input: data/customer_shopping_behavior.csv
Outputs: outputs/*.csv and outputs/*.png
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "customer_shopping_behavior.csv"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
df["Purchase_Date"] = pd.to_datetime(df["Purchase_Date"], errors="coerce")
df["Purchase_Amount_USD"] = pd.to_numeric(df["Purchase_Amount_USD"], errors="coerce")
df["Review_Rating"] = pd.to_numeric(df["Review_Rating"], errors="coerce")
df = df.drop_duplicates(subset=["Purchase_ID"]).dropna(
    subset=["Purchase_ID", "Customer_ID", "Category", "Purchase_Amount_USD"]
)

# KPI summary
kpis = pd.DataFrame({
    "Metric": ["Total Orders", "Unique Customers", "Total Revenue (USD)",
               "Average Order Value (USD)", "Average Review Rating"],
    "Value": [len(df), df["Customer_ID"].nunique(),
              round(df["Purchase_Amount_USD"].sum(), 2),
              round(df["Purchase_Amount_USD"].mean(), 2),
              round(df["Review_Rating"].mean(), 2)]
})
kpis.to_csv(OUT / "kpi_summary.csv", index=False)

category_summary = (df.groupby("Category", as_index=False)
    .agg(Orders=("Purchase_ID", "count"),
         Revenue_USD=("Purchase_Amount_USD", "sum"),
         Average_Order_Value=("Purchase_Amount_USD", "mean"),
         Average_Rating=("Review_Rating", "mean"))
    .sort_values("Revenue_USD", ascending=False))
category_summary.to_csv(OUT / "category_summary.csv", index=False)

monthly = (df.assign(Month=df["Purchase_Date"].dt.to_period("M").astype(str))
    .groupby("Month", as_index=False)
    .agg(Orders=("Purchase_ID", "count"), Revenue_USD=("Purchase_Amount_USD", "sum"))
    .sort_values("Month"))
monthly.to_csv(OUT / "monthly_trends.csv", index=False)

payment = (df.groupby("Payment_Method", as_index=False)
    .agg(Orders=("Purchase_ID", "count"), Revenue_USD=("Purchase_Amount_USD", "sum"))
    .sort_values("Orders", ascending=False))
payment.to_csv(OUT / "payment_method_summary.csv", index=False)

discount = (df.groupby("Discount_Applied", as_index=False)
    .agg(Orders=("Purchase_ID", "count"), Avg_Order_Value=("Purchase_Amount_USD", "mean"),
         Average_Rating=("Review_Rating", "mean")))
discount.to_csv(OUT / "discount_analysis.csv", index=False)

# Load a clean copy into SQLite for SQL analysis
db_path = OUT / "shopping_behavior.db"
with sqlite3.connect(db_path) as conn:
    df.to_sql("shopping_behavior", conn, if_exists="replace", index=False)

# Charts (matplotlib defaults)
plt.figure(figsize=(8, 5))
plt.bar(category_summary["Category"], category_summary["Revenue_USD"])
plt.title("Revenue by Product Category")
plt.xlabel("Category")
plt.ylabel("Revenue (USD)")
plt.tight_layout()
plt.savefig(OUT / "revenue_by_category.png", dpi=150)
plt.close()

plt.figure(figsize=(10, 5))
plt.plot(monthly["Month"], monthly["Revenue_USD"], marker="o")
plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue (USD)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUT / "monthly_revenue_trend.png", dpi=150)
plt.close()

print("Analysis complete. Check the outputs folder.")
print(kpis.to_string(index=False))
