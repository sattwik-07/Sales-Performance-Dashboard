"""
Generate a realistic multi-year retail sales transaction dataset.

Sales Performance Dashboard — by Sattwik

Why generated instead of downloaded:
The reference dataset (Tableau/Power BI "Sample Superstore") could not be
retrieved in full through available tools. Rather than use a truncated
fragment, this script generates a statistically faithful equivalent at
full scale: same schema, same category economics (notably, that heavy
discounting on Furniture/Tables and Binders/Machines erases profit -
the single most famous insight in the real Superstore dataset), real-
world seasonality (Nov/Dec retail spike), and genuine messiness (nulls,
duplicates, a few bad rows) so the cleaning step is not cosmetic.

Schema matches the standard Superstore columns so this slots into the
exact Project 1 brief: Sales Performance Dashboard.
"""

import numpy as np
import pandas as pd
from datetime import timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

REGION_STATE_CITY = {
    "East": [("New York", "New York City"), ("New York", "Buffalo"),
             ("Pennsylvania", "Philadelphia"), ("Pennsylvania", "Pittsburgh"),
             ("Massachusetts", "Boston"), ("New Jersey", "Newark"),
             ("Virginia", "Richmond"), ("Ohio", "Columbus")],
    "West": [("California", "Los Angeles"), ("California", "San Francisco"),
             ("California", "San Diego"), ("Washington", "Seattle"),
             ("Oregon", "Portland"), ("Arizona", "Phoenix"),
             ("Colorado", "Denver"), ("Nevada", "Las Vegas")],
    "Central": [("Illinois", "Chicago"), ("Texas", "Houston"),
                ("Texas", "Dallas"), ("Texas", "Austin"),
                ("Michigan", "Detroit"), ("Minnesota", "Minneapolis"),
                ("Wisconsin", "Milwaukee"), ("Missouri", "St. Louis")],
    "South": [("Florida", "Miami"), ("Florida", "Orlando"),
              ("Georgia", "Atlanta"), ("North Carolina", "Charlotte"),
              ("Tennessee", "Nashville"), ("Louisiana", "New Orleans"),
              ("Kentucky", "Louisville"), ("Alabama", "Birmingham")],
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_WEIGHTS = [0.52, 0.30, 0.18]

SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
SHIP_MODE_WEIGHTS = [0.60, 0.19, 0.16, 0.05]
SHIP_LEAD_DAYS = {"Standard Class": (4, 7), "Second Class": (2, 4),
                   "First Class": (1, 3), "Same Day": (0, 0)}

# category -> sub-category -> (product names, unit price range, base margin)
CATALOG = {
    "Furniture": {
        "Bookcases": (
            ["Bush Birmingham 5-Shelf Bookcase", "Sauder Heritage Hill Bookcase",
             "O'Sullivan Living Dimensions Bookcase", "Hon 3-Shelf Metal Bookcase",
             "Atlantic Mobile 4-Shelf Bookcase"], (90, 950), 0.10),
        "Chairs": (
            ["Hon Mesh Task Chair", "Global High-Back Leather Tilter",
             "Novimex Executive Leather Armchair", "Office Star Contemporary Swivel Chair",
             "SAFCO Arco Folding Chair", "Steelcase Series 1 Task Chair"], (80, 1100), 0.09),
        "Furnishings": (
            ["Howard Miller Wall Clock", "Eldon Expressions Desk Accessory Set",
             "Luxo Swing-Arm Desk Lamp", "Tenex Chair Mat for Carpet",
             "DAX Metal Desktop Frame"], (8, 400), 0.18),
        "Tables": (
            ["Bretford Rectangular Conference Table", "Chromcraft Bull-Nose Conference Table",
             "Bevis Round Bullnose Table Top", "Hon Racetrack Conference Table",
             "KI Adjustable-Height Table"], (150, 4200), 0.06),
    },
    "Office Supplies": {
        "Appliances": (
            ["Honeywell HEPA Air Cleaner", "Belkin 8-Outlet Surge Protector",
             "Eureka Cordless Stick Vac", "Hamilton Beach Mini Fridge"], (15, 850), 0.16),
        "Art": (
            ["Sanford Colored Pencil Set", "Boston Electric Pencil Sharpener",
             "Newell Highlighter Pack", "Crayola Washable Markers"], (2, 120), 0.30),
        "Binders": (
            ["Avery Durable View Binder", "GBC ProClick Binding System",
             "Wilson Jones Hanging Binder", "Cardinal Slant-D Ring Binder",
             "Ibico Plastic Comb Binding Machine"], (3, 900), 0.20),
        "Envelopes": (
            ["Staple Security-Tint Envelopes", "Tyvek Peel & Seal Envelopes",
             "Globe-Weis Interoffice Envelopes"], (4, 90), 0.28),
        "Fasteners": (
            ["Advantus Push Pins", "OIC Binder Clip Pack", "Staples Rubber Band Pack"],
            (1, 35), 0.32),
        "Labels": (
            ["Avery Shipping Labels", "Avery File Folder Labels",
             "Self-Adhesive Address Labels"], (2, 60), 0.30),
        "Paper": (
            ["Xerox Multipurpose Copy Paper", "Universal Premium Laser Paper",
             "Ampad Wirebound Steno Book"], (3, 160), 0.24),
        "Storage": (
            ["Iris Project Storage Case", "Fellowes Stor/Drawer Steel Plus",
             "Safco Industrial Wire Shelving", "Tennsco Storage Locker",
             "Eldon File Cart"], (10, 1200), 0.14),
        "Supplies": (
            ["Fiskars Softgrip Scissors", "Acme Letter Opener", "Martin-Yale Electric Opener"],
            (2, 120), 0.22),
    },
    "Technology": {
        "Accessories": (
            ["Logitech MX Master Wireless Mouse", "Logitech Wireless Keyboard",
             "SanDisk USB Flash Drive 64GB", "NETGEAR Dual-Band WiFi Router",
             "Anker Portable Charger", "Razer Gaming Headset"], (10, 480), 0.22),
        "Copiers": (
            ["Canon ImageClass Digital Copier", "Hewlett Packard LaserJet Copier",
             "Sharp Digital Copier"], (350, 5200), 0.18),
        "Machines": (
            ["Lexmark Monochrome Laser Printer", "Zebra Direct Thermal Printer",
             "Cisco IP Phone System", "Brother Multifunction Printer"], (180, 8500), 0.14),
        "Phones": (
            ["Cisco Unified IP Phone", "AT&T Cordless Phone System",
             "Apple iPhone Case & Charger Bundle", "Samsung Galaxy Accessory Kit",
             "Plantronics Wireless Headset", "Jabra Speakerphone"], (15, 1450), 0.20),
    },
}

CATEGORY_OF = {sub: cat for cat, subs in CATALOG.items() for sub in subs}

# Discount levels and their relative likelihood.
# Big-ticket equipment (Machines/Copiers/Tables) rarely gets steeply
# discounted in practice (negotiated/enterprise pricing); everyday supplies
# get discounted more freely. Two separate distributions capture this.
DISCOUNT_LEVELS = [0.0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
DISCOUNT_WEIGHTS = [0.40, 0.16, 0.12, 0.13, 0.09, 0.05, 0.03, 0.01, 0.005, 0.005]
DISCOUNT_WEIGHTS_BIGTICKET = [0.55, 0.20, 0.12, 0.08, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0]
BIGTICKET_SUBCATS = {"Machines", "Copiers", "Tables"}

# Per sub-category sensitivity of margin to discount depth (how fast profit
# erodes as discount grows). Tables/Bookcases/Binders are the classic
# "discount kills profit" categories; everyday consumables barely move.
DISCOUNT_SENSITIVITY = {
    "Tables": 0.95, "Bookcases": 0.70, "Binders": 0.55, "Machines": 0.55,
    "Chairs": 0.40, "Copiers": 0.40, "Storage": 0.35, "Appliances": 0.35,
}
DEFAULT_SENSITIVITY = 0.22

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2025-12-31")
N_ORDERS = 2300

# Monthly seasonality weight (retail-style: holiday peak, summer lull)
MONTH_WEIGHTS = {1: 0.7, 2: 0.7, 3: 0.85, 4: 0.9, 5: 0.95, 6: 0.9,
                 7: 0.85, 8: 0.9, 9: 1.0, 10: 1.05, 11: 1.45, 12: 1.6}

# Mild year-over-year growth, with a soft dip in 2024 Q2 (a deliberate,
# realistic wrinkle so the trend analysis has something to explain)
YEAR_GROWTH = {2023: 1.00, 2024: 1.08, 2025: 1.18}


def random_date():
    days_span = (END_DATE - START_DATE).days
    # sample a candidate date, weighted by month seasonality via rejection sampling
    while True:
        offset = rng.integers(0, days_span + 1)
        d = START_DATE + timedelta(days=int(offset))
        w = MONTH_WEIGHTS[d.month]
        if d.year == 2024 and d.month in (4, 5, 6):
            w *= 0.8  # the deliberate soft patch
        if rng.random() < w / 1.6:
            return d


def gen_customer_pool(n=420):
    first = ["James", "Mary", "Robert", "Patricia", "John", "Linda", "Michael", "Barbara",
             "William", "Elizabeth", "David", "Jennifer", "Richard", "Maria", "Joseph",
             "Susan", "Thomas", "Margaret", "Charles", "Dorothy", "Daniel", "Lisa",
             "Matthew", "Nancy", "Anthony", "Karen", "Mark", "Betty", "Paul", "Helen",
             "Steven", "Sandra", "Andrew", "Donna", "Kenneth", "Carol", "Joshua", "Ruth",
             "Kevin", "Sharon", "Brian", "Michelle", "George", "Laura", "Edward", "Emily",
             "Ronald", "Kimberly", "Timothy", "Deborah"]
    last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
            "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"]
    names = set()
    while len(names) < n:
        names.add(f"{rng.choice(first)} {rng.choice(last)}")
    customers = []
    for nm in names:
        region = rng.choice(list(REGION_STATE_CITY.keys()))
        state, city = REGION_STATE_CITY[region][rng.integers(0, len(REGION_STATE_CITY[region]))]
        segment = rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
        cust_id = "".join([w[0] for w in nm.split()]).upper() + f"-{rng.integers(10000,99999)}"
        customers.append({"Customer ID": cust_id, "Customer Name": nm, "Segment": segment,
                           "Region": region, "State": state, "City": city})
    return pd.DataFrame(customers)


def build_dataset():
    customers = gen_customer_pool()
    rows = []
    order_counter = 0

    for _ in range(N_ORDERS):
        order_counter += 1
        cust = customers.iloc[rng.integers(0, len(customers))]
        order_date = random_date()
        ship_mode = rng.choice(SHIP_MODES, p=SHIP_MODE_WEIGHTS)
        lo, hi = SHIP_LEAD_DAYS[ship_mode]
        ship_date = order_date + timedelta(days=int(rng.integers(lo, hi + 1)))
        prefix = rng.choice(["CA", "US"])
        order_id = f"{prefix}-{order_date.year}-{100000 + order_counter}"

        n_items = rng.choice([1, 2, 3, 4, 5], p=[0.42, 0.28, 0.16, 0.09, 0.05])
        chosen_subcats = rng.choice(list(CATEGORY_OF.keys()), size=n_items, replace=True)

        for sub in chosen_subcats:
            cat = CATEGORY_OF[sub]
            products, price_range, base_margin = CATALOG[cat][sub]
            product_name = rng.choice(products)
            product_id = f"{cat[:3].upper()}-{sub[:2].upper()}-{rng.integers(1000,9999)}"
            unit_price = float(rng.uniform(*price_range))
            quantity = int(rng.integers(1, 10))
            weights = DISCOUNT_WEIGHTS_BIGTICKET if sub in BIGTICKET_SUBCATS else DISCOUNT_WEIGHTS
            discount = float(rng.choice(DISCOUNT_LEVELS, p=weights))

            year_factor = YEAR_GROWTH[order_date.year]
            sales = unit_price * quantity * year_factor

            # Profit model: margin shrinks with discount depth, at a rate
            # set per sub-category (see DISCOUNT_SENSITIVITY above).
            sensitivity = DISCOUNT_SENSITIVITY.get(sub, DEFAULT_SENSITIVITY)
            discount_penalty = discount * sensitivity
            margin = base_margin - discount_penalty + rng.normal(0, 0.025)
            profit = sales * margin

            rows.append({
                "Row ID": len(rows) + 1,
                "Order ID": order_id,
                "Order Date": order_date.strftime("%Y-%m-%d"),
                "Ship Date": ship_date.strftime("%Y-%m-%d"),
                "Ship Mode": ship_mode,
                "Customer ID": cust["Customer ID"],
                "Customer Name": cust["Customer Name"],
                "Segment": cust["Segment"],
                "Country": "United States",
                "City": cust["City"],
                "State": cust["State"],
                "Postal Code": int(rng.integers(10000, 99999)),
                "Region": cust["Region"],
                "Product ID": product_id,
                "Category": cat,
                "Sub-Category": sub,
                "Product Name": product_name,
                "Sales": round(sales, 2),
                "Quantity": quantity,
                "Discount": discount,
                "Profit": round(profit, 4),
            })

    df = pd.DataFrame(rows)

    # -----------------------------------------------------------------
    # Inject realistic data-quality issues for the cleaning step
    # -----------------------------------------------------------------
    n = len(df)

    # 1. Exact duplicate rows (a common real-world export glitch)
    dup_idx = rng.choice(n, size=22, replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)

    # 2. Missing values in non-key fields
    null_idx_postal = rng.choice(len(df), size=18, replace=False)
    df.loc[null_idx_postal, "Postal Code"] = np.nan

    null_idx_customer = rng.choice(len(df), size=9, replace=False)
    df.loc[null_idx_customer, "Customer Name"] = None

    null_idx_ship = rng.choice(len(df), size=7, replace=False)
    df.loc[null_idx_ship, "Ship Mode"] = None

    # 3. A few invalid rows (zero quantity / blank sales) that should be dropped
    bad_idx = rng.choice(len(df), size=5, replace=False)
    df.loc[bad_idx, "Quantity"] = 0
    df.loc[bad_idx, "Sales"] = np.nan

    df = df.sample(frac=1, random_state=7).reset_index(drop=True)
    df["Row ID"] = range(1, len(df) + 1)
    return df


if __name__ == "__main__":
    df = build_dataset()
    out_path = "/home/claude/superstore_project/data/raw_sales_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    print(df.head(3).to_string())
    print("\nNulls per column:\n", df.isna().sum())
    print("\nExact duplicate rows:", df.duplicated().sum())
