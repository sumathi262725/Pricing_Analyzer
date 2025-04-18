# price_comparison_india.py
import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
import re
from io import BytesIO

SERPAPI_KEY = os.getenv("SERPAPI_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

st.set_page_config(page_title="🇮🇳 India Price Comparison", layout="wide")
st.title("🇮🇳 Product Price Comparison - India")
st.write("Upload a list of products and get their prices from top Indian online stores.")

uploaded_file = st.file_uploader("📄 Upload product list (CSV or TXT)", type=["csv", "txt"])

def parse_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file).iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        return [line.strip() for line in file.read().decode("utf-8").splitlines() if line.strip()]
    return []

def get_base_site_name(site):
    match = re.match(r"([a-zA-Z0-9]+)", site)
    return match.group(1) if match else site

def get_prices_india(product):
    params = {
        "engine": "google_shopping",
        "q": product,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "in",
        "location": "India"
    }
    results = GoogleSearch(params).get_dict()
    shopping_results = results.get("shopping_results", [])
    seen_sites = set()
    items = []

    for item in shopping_results:
        site = item.get("source")
        price_str = item.get("price")
        currency_symbol = item.get("currency")

        if site and price_str and currency_symbol:
            base = get_base_site_name(site)
            if base not in seen_sites:
                price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
                try:
                    price = float(price_cleaned)
                    items.append((base, f"{currency_symbol}{price}"))
                    seen_sites.add(base)
                except ValueError:
                    continue
    return items

if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    for product in products:
        price_data = get_prices_india(product)
        if price_data:
            lowest_price = min(price_data, key=lambda x: float(re.sub(r'[^\d.]', '', x[1])))
            for site, price in price_data:
                results.append({
                    "Product": product if site == price_data[0][0] else "",
                    "Region": "India",
                    "Site & Price": f"{site}({price})",
                    "Lowest Price & Site": f"{lowest_price[0]}({lowest_price[1]})" if site == lowest_price[0] else ""
                })
        else:
            results.append({
                "Product": product,
                "Region": "India",
                "Site & Price": "No results found",
                "Lowest Price & Site": ""
            })

    df = pd.DataFrame(results)
    st.dataframe(df)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", data=csv, file_name="price_comparison_india.csv", mime="text/csv")
