"""
Step 2: Clean the raw sales export and run the core analysis for the
Sales Performance Dashboard project.

Sales Performance Dashboard — by Sattwik

Pipeline:
  1. Load raw data
  2. Clean: drop exact duplicates, handle nulls, drop invalid rows
  3. Engineer date parts (year, month, quarter)
  4. Compute: monthly/quarterly/yearly trends, top & bottom products,
     region x category breakdowns, KPIs (revenue, profit, margin, growth)
  5. Export a cleaned CSV (ready for Excel/Power BI/Tableau) and a single
     JSON bundle that powers the interactive HTML dashboard.
"""

import json
import numpy as np
import pandas as pd

RAW_PATH = "/home/claude/superstore_project/data/raw_sales_data.csv"
CLEAN_CSV_PATH = "/home/claude/superstore_project/data/cleaned_sales_data.csv"
DASHBOARD_JSON_PATH = "/home/claude/superstore_project/data/dashboard_data.json"
CLEANING_LOG_PATH = "/home/claude/superstore_project/data/cleaning_log.txt"

log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
df = pd.read_csv(RAW_PATH)
log(f"Loaded raw data: {df.shape[0]} rows, {df.shape[1]} columns")

# ---------------------------------------------------------------------------
# 2. Clean
# ---------------------------------------------------------------------------
key_cols = [c for c in df.columns if c != "Row ID"]
n_before = len(df)
df = df.drop_duplicates(subset=key_cols).copy()
log(f"Removed exact duplicate rows: {n_before - len(df)}")

n_before = len(df)
df = df[~(df["Sales"].isna() | (df["Quantity"] <= 0))].copy()
log(f"Removed invalid rows (blank Sales or zero/negative Quantity): {n_before - len(df)}")

# Missing Ship Mode -> impute with the column mode (most common shipping method)
n_missing_ship = df["Ship Mode"].isna().sum()
df["Ship Mode"] = df["Ship Mode"].fillna(df["Ship Mode"].mode()[0])
log(f"Filled missing Ship Mode with mode value: {n_missing_ship} rows")

# Missing Customer Name -> label explicitly rather than drop (order is still valid)
n_missing_cust = df["Customer Name"].isna().sum()
df["Customer Name"] = df["Customer Name"].fillna("Unknown Customer")
log(f"Filled missing Customer Name: {n_missing_cust} rows")

# Missing Postal Code -> not used in any analysis below; leave as null but flagged
n_missing_postal = df["Postal Code"].isna().sum()
log(f"Missing Postal Code left as null (not used in analysis): {n_missing_postal} rows")

df["Row ID"] = range(1, len(df) + 1)
log(f"Final cleaned row count: {len(df)}")

# ---------------------------------------------------------------------------
# 3. Date engineering
# ---------------------------------------------------------------------------
df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Year"] = df["Order Date"].dt.year
df["Month"] = df["Order Date"].dt.month
df["MonthLabel"] = df["Order Date"].dt.strftime("%Y-%m")
df["Quarter"] = df["Order Date"].dt.quarter
df["QuarterLabel"] = df["Year"].astype(str) + "-Q" + df["Quarter"].astype(str)

df.to_csv(CLEAN_CSV_PATH, index=False)
log(f"\nSaved cleaned dataset to {CLEAN_CSV_PATH}")

# ---------------------------------------------------------------------------
# 4. KPIs
# ---------------------------------------------------------------------------
total_revenue = df["Sales"].sum()
total_profit = df["Profit"].sum()
total_orders = df["Order ID"].nunique()
total_units = df["Quantity"].sum()
margin_pct = total_profit / total_revenue * 100
avg_order_value = total_revenue / total_orders

yearly = df.groupby("Year")["Sales"].sum().sort_index()
years_sorted = yearly.index.tolist()
yoy_growth = {}
for i in range(1, len(years_sorted)):
    prev_y, cur_y = years_sorted[i - 1], years_sorted[i]
    yoy_growth[f"{prev_y}->{cur_y}"] = round((yearly[cur_y] - yearly[prev_y]) / yearly[prev_y] * 100, 2)

kpis = {
    "total_revenue": round(total_revenue, 2),
    "total_profit": round(total_profit, 2),
    "profit_margin_pct": round(margin_pct, 2),
    "total_orders": int(total_orders),
    "total_units": int(total_units),
    "avg_order_value": round(avg_order_value, 2),
    "yoy_growth_pct": yoy_growth,
}
log("\n--- KPIs ---")
log(json.dumps(kpis, indent=2))

# ---------------------------------------------------------------------------
# Trends: monthly, quarterly, yearly
# ---------------------------------------------------------------------------
monthly = (df.groupby("MonthLabel")
             .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
             .reset_index().sort_values("MonthLabel"))
quarterly = (df.groupby("QuarterLabel")
               .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
               .reset_index().sort_values("QuarterLabel"))
yearly_df = (df.groupby("Year")
               .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
               .reset_index().sort_values("Year"))

# ---------------------------------------------------------------------------
# Top-selling products & low performers
# ---------------------------------------------------------------------------
product_perf = (df.groupby("Product Name")
                   .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                        Units=("Quantity", "sum"), Orders=("Order ID", "nunique"))
                   .reset_index())

top_products_by_sales = product_perf.sort_values("Sales", ascending=False).head(10)
top_products_by_profit = product_perf.sort_values("Profit", ascending=False).head(10)
low_performers = product_perf.sort_values("Profit", ascending=True).head(10)

# ---------------------------------------------------------------------------
# Region-wise and category-wise comparisons
# ---------------------------------------------------------------------------
region_perf = (df.groupby("Region")
                 .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
                 .reset_index().sort_values("Sales", ascending=False))
category_perf = (df.groupby("Category")
                    .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
                    .reset_index().sort_values("Sales", ascending=False))
subcat_perf = (df.groupby(["Category", "Sub-Category"])
                  .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
                  .reset_index().sort_values("Sales", ascending=False))
region_category = (df.groupby(["Region", "Category"])["Sales"]
                      .sum().reset_index())
segment_perf = (df.groupby("Segment")
                   .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
                   .reset_index().sort_values("Sales", ascending=False))

log("\n--- Region performance ---")
log(region_perf.to_string(index=False))
log("\n--- Category performance ---")
log(category_perf.to_string(index=False))
log("\n--- Sub-category profit (lowest 5 = where discounting hurts most) ---")
log(subcat_perf.sort_values("Profit").head(5).to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Export full record-level data + aggregates as one JSON bundle
#    (the dashboard recomputes filtered aggregates client-side from
#    `records`, and uses the precomputed tables for the unfiltered view)
# ---------------------------------------------------------------------------
records = df[["Order Date", "Year", "Month", "Quarter", "Region",
              "Segment", "Category", "Sub-Category", "Product Name", "Sales",
              "Profit", "Quantity", "Discount", "Order ID", "Customer Name"]].copy()
records["Order Date"] = records["Order Date"].dt.strftime("%Y-%m-%d")

bundle = {
    "kpis": kpis,
    "monthly": monthly.to_dict(orient="records"),
    "quarterly": quarterly.to_dict(orient="records"),
    "yearly": yearly_df.to_dict(orient="records"),
    "top_products_by_sales": top_products_by_sales.to_dict(orient="records"),
    "top_products_by_profit": top_products_by_profit.to_dict(orient="records"),
    "low_performers": low_performers.to_dict(orient="records"),
    "region_perf": region_perf.to_dict(orient="records"),
    "category_perf": category_perf.to_dict(orient="records"),
    "subcat_perf": subcat_perf.to_dict(orient="records"),
    "region_category": region_category.to_dict(orient="records"),
    "segment_perf": segment_perf.to_dict(orient="records"),
    "records": records.to_dict(orient="records"),
}

with open(DASHBOARD_JSON_PATH, "w") as f:
    json.dump(bundle, f)
log(f"\nSaved dashboard data bundle to {DASHBOARD_JSON_PATH} "
    f"({len(records)} records, {round(len(json.dumps(bundle))/1024, 1)} KB)")

with open(CLEANING_LOG_PATH, "w") as f:
    f.write("\n".join(log_lines))
