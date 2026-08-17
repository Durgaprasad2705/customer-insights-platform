"""
Customer Insights Platform – Synthetic Electronics Retail Dataset Generator.
Produces realistic transaction data for demo / testing purposes.
"""

from __future__ import annotations

import datetime
import random

import numpy as np
import pandas as pd

from config import ELECTRONICS_CATEGORIES, ELECTRONICS_BRANDS, ELECTRONICS_REGIONS

_PRODUCT_CATALOG: dict[str, list[tuple[str, float, str]]] = {
    "Laptops & Computers": [
        ("MacBook Pro 16\"", 2499.00, "Apple"),
        ("Dell XPS 15", 1899.00, "Dell"),
        ("HP Spectre x360", 1499.00, "HP"),
        ("Lenovo ThinkPad X1 Carbon", 1699.00, "Lenovo"),
        ("Asus ROG Strix G16", 1999.00, "Asus"),
    ],
    "Smartphones & Accessories": [
        ("iPhone 15 Pro Max", 1199.00, "Apple"),
        ("Galaxy S24 Ultra", 1299.00, "Samsung"),
        ("Google Pixel 8 Pro", 999.00, "Google"),
        ("Sony Xperia 1 VI", 1199.00, "Sony"),
        ("MagSafe Wireless Charger", 39.00, "Apple"),
    ],
    "Televisions & Home Theater": [
        ("LG C3 65\" OLED 4K TV", 1799.00, "LG"),
        ("Samsung Neo QLED 75\"", 2299.00, "Samsung"),
        ("Sony BRAVIA XR 65\"", 1999.00, "Sony"),
        ("Sonos Arc Soundbar", 899.00, "Bose"),
    ],
    "Headphones & Audio": [
        ("Sony WH-1000XM5", 399.00, "Sony"),
        ("Bose QuietComfort Ultra", 429.00, "Bose"),
        ("AirPods Pro 2nd Gen", 249.00, "Apple"),
        ("Logitech G PRO X Headset", 149.00, "Logitech"),
    ],
    "Smartwatches & Wearables": [
        ("Apple Watch Ultra 2", 799.00, "Apple"),
        ("Galaxy Watch 6 Classic", 399.00, "Samsung"),
        ("Garmin Fenix 7X Pro", 899.00, "Sony"),
    ],
    "Cameras & Photography": [
        ("Sony Alpha a7 IV", 2499.00, "Sony"),
        ("Canon EOS R6 Mark II", 2299.00, "Sony"),
        ("DJI Mini 4 Pro Drone", 759.00, "Google"),
    ],
    "Gaming Consoles & Gear": [
        ("PlayStation 5 Console", 499.00, "Sony"),
        ("Xbox Series X", 499.00, "Asus"),
        ("Logitech G502 X Plus Mouse", 79.00, "Logitech"),
    ],
    "Smart Home Devices": [
        ("Google Nest Hub Max", 229.00, "Google"),
        ("Ring Video Doorbell Pro 2", 199.00, "Google"),
        ("Philips Hue Starter Kit", 179.00, "Logitech"),
    ],
}


def generate_electronics_dataset(num_records: int = 1_250) -> pd.DataFrame:
    """
    Generate a realistic synthetic electronics retail transaction dataset rapidly using vectorized operations.

    Returns a DataFrame with canonical column names ready for the platform.
    """
    np.random.seed(42)
    random.seed(42)

    num_customers = 350
    start_date    = datetime.date.today() - datetime.timedelta(days=365)

    # Customer pool
    cust_ids     = [f"CUST-{1000 + i}" for i in range(num_customers)]
    cust_names   = [f"Customer {i + 1}" for i in range(num_customers)]
    cust_ages    = np.random.randint(18, 68, size=num_customers)
    cust_genders = np.random.choice(
        ["Male", "Female", "Non-Binary"], size=num_customers, p=[0.52, 0.45, 0.03]
    )
    cust_regions = np.random.choice(
        ELECTRONICS_REGIONS, size=num_customers, p=[0.35, 0.25, 0.20, 0.10, 0.10]
    )

    # Pre-flatten catalog items
    catalog_items = []
    for cat, items in _PRODUCT_CATALOG.items():
        for prod_name, unit_price, brand in items:
            catalog_items.append((cat, prod_name, unit_price, brand))

    num_catalog = len(catalog_items)
    selected_catalog_idxs = np.random.randint(0, num_catalog, size=num_records)
    selected_cust_idxs = np.random.randint(0, num_customers, size=num_records)

    quantities = np.random.choice([1, 2, 3, 4], size=num_records, p=[0.75, 0.18, 0.05, 0.02])
    ratings = np.random.choice([5, 4, 3, 2, 1], size=num_records, p=[0.55, 0.25, 0.10, 0.06, 0.04])
    payment_choices = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "EMI Financing"]
    payments = np.random.choice(payment_choices, size=num_records)

    random_days = np.random.randint(1, 366, size=num_records)
    profit_multipliers = np.random.uniform(0.18, 0.42, size=num_records)

    categories = [catalog_items[i][0] for i in selected_catalog_idxs]
    prod_names = [catalog_items[i][1] for i in selected_catalog_idxs]
    unit_prices = np.array([catalog_items[i][2] for i in selected_catalog_idxs], dtype=float)
    brands = [catalog_items[i][3] for i in selected_catalog_idxs]

    total_amounts = np.round(unit_prices * quantities, 2)
    profit_margins = np.round(total_amounts * profit_multipliers, 2)

    purchase_dates = [(start_date + datetime.timedelta(days=int(d))).strftime("%Y-%m-%d") for d in random_days]
    txn_ids = [f"TXN-{10000 + i}" for i in range(num_records)]

    df = pd.DataFrame({
        "TransactionID":  txn_ids,
        "CustomerID":     [cust_ids[i] for i in selected_cust_idxs],
        "CustomerName":   [cust_names[i] for i in selected_cust_idxs],
        "CustomerAge":    cust_ages[selected_cust_idxs],
        "Gender":         cust_genders[selected_cust_idxs],
        "Region":         cust_regions[selected_cust_idxs],
        "PurchaseDate":   purchase_dates,
        "Category":       categories,
        "ProductName":    prod_names,
        "Brand":          brands,
        "UnitPrice":      unit_prices,
        "Quantity":       quantities,
        "TotalAmount":    total_amounts,
        "ProfitMargin":   profit_margins,
        "PaymentMethod":  payments,
        "CustomerRating": ratings,
    })

    # Compute RFM & churn per customer rapidly
    date_dt = pd.to_datetime(df["PurchaseDate"])
    max_date = date_dt.max()

    rfm = (
        df.assign(DateObj=date_dt).groupby("CustomerID")
        .agg(
            RecencyDays      = ("DateObj", lambda d: (max_date - d.max()).days),
            PurchaseFrequency= ("TransactionID", "count"),
            MonetaryValue    = ("TotalAmount",   "sum"),
        )
        .reset_index()
    )
    rfm["ChurnStatus"] = (rfm["RecencyDays"] > 120).astype(int)

    return df.merge(rfm, on="CustomerID", how="left")
