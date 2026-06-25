# Sales Performance Dashboard

A fully interactive, offline-capable sales analytics dashboard built as a personal data project. Bring your own sales CSV, or explore the bundled demo dataset — every chart, KPI, and table recomputes live in the browser as you filter, search, or drill in.

**[Open `sales_performance_dashboard.html`](./sales_performance_dashboard.html) in any browser to use it — no install, no server, no internet connection required.**

## Features

- **Bring your own data.** Upload any CSV with sales transactions (date, region, category, sales, profit, etc.) and the whole dashboard rebuilds around it. Flexible column-name matching (`Revenue`/`Sales`/`Amount` all work), with clear error messages if required columns are missing.
- **Click-to-filter charts.** Click a region bar, a category bar, or a segment of the stacked composition chart to instantly filter the whole dashboard — no separate "apply" step.
- **Searchable, sortable, paginated product table.** Search by product name; click any column header to sort; page through results.
- **Forecasting.** A "Show forecast" toggle projects the next few periods forward using simple linear regression on the visible trend, drawn as a dashed extension of the chart.
- **Revenue goal tracker.** Set a target and watch a live progress bar against the currently filtered revenue. Persists across sessions (localStorage).
- **Export & share.** Export the currently filtered transactions to CSV, print/save the dashboard as a PDF, or copy a link that encodes your exact filter state for someone else to open.
- **Zero dependencies.** Every chart is hand-built in vanilla SVG/CSS/JS — no Chart.js, no D3, no CDN calls. The file works completely offline.

## Files

| File | Purpose |
|---|---|
| `sales_performance_dashboard.html` | The dashboard. Self-contained — open and go. |
| `cleaned_sales_data.csv` | The cleaned demo dataset (also a good reference for the column format the CSV uploader expects). |
| `raw_sales_data.csv` | Demo dataset before cleaning — kept to show what the cleaning step actually removed. |
| `01_generate_dataset.py` | Generates the demo dataset (see below). |
| `02_clean_and_analyze.py` | Cleans the raw data and produces the JSON the dashboard ships with. |
| `cleaning_log.txt` | What the cleaning step removed and why. |

## CSV format

Minimum required columns: **Order Date** and **Sales**. Recognized optional columns (common aliases are auto-detected): `Region`, `Segment`, `Category`, `Sub-Category`, `Product Name`, `Profit`, `Quantity`, `Discount`, `Order ID`, `Customer Name`. Anything missing just falls back to a sensible default rather than failing the import.

## About the demo dataset

It's modeled on the structure and economics of a well-known retail sales dataset (region / category / sub-category / segment, 2023–2025), generated to include realistic seasonality and the same "high revenue, thin margin" discounting pattern that shows up in real retail data — plus genuine messiness (duplicate rows, missing fields) so the cleaning step is real work, not a formality. Swap in your own export any time via the upload button.

## Key findings (demo data)

- $20.48M revenue, $2.06M profit (10.0% margin), 2,300 orders, 2023–2025.
- Furniture is the trap category: ~24% of revenue but only ~5% of profit, driven by Tables and Bookcases barely breaking even once discounts are applied.
- West leads regionally; South trails.
- YoY growth accelerated from +2.5% (2023→2024) to +9.5% (2024→2025).

## Reproducing the demo dataset

```bash
pip install pandas numpy
python 01_generate_dataset.py     # writes raw_sales_data.csv
python 02_clean_and_analyze.py    # writes cleaned_sales_data.csv + the dashboard's JSON data
```

## Author

Built by **Sattwik**.

<!-- Add your links here, e.g.:
- GitHub: https://github.com/your-username
- LinkedIn: https://linkedin.com/in/your-handle
- Portfolio: https://your-site.com
-->
