import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

# Load SerpAPI key from environment or use hardcoded fallback
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# App title
st.set_page_config(page_title="Product Price Comparison", layout="centered")
st.title("🛍️ Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT), and we’ll find the best prices across sites.")

# File uploader
uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

# Parse file contents
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        return [line.strip() for line in file.readlines()]
    return []

# Query SerpAPI for shopping prices
def get_prices(product_name):
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "us"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    items = []
    for item in results.get("shopping_results", []):
        site = item.get("source")
        price_str = item.get("price")
        if site and price_str:
            try:
                price = float(price_str.replace("$", "").replace(",", "").strip())
                items.append((site, price))
            except:
                continue
    return items

# Main app logic
if uploaded_file:
    products = parse_file(uploaded_file)
    grouped_results = []

    with st.spinner("🔍 Searching for prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                sites_prices = [f"{site}: ${price:.2f}" for site, price in price_data]
                lowest_price = min(price for _, price in price_data)
                grouped_results.append({
                    "Product": product,
                    "Sites & Prices": "<br>".join(sites_prices),
                    "Lowest Price ($)": lowest_price
                })
            else:
                grouped_results.append({
                    "Product": product,
                    "Sites & Prices": "No results found",
                    "Lowest Price ($)": None
                })

    df = pd.DataFrame(grouped_results)

    # Display with HTML formatting
    st.success("✅ Price comparison complete!")
    st.write("### 🧾 Results")
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Clean export format for CSV
    export_df = df.copy()
    export_df["Sites & Prices"] = export_df["Sites & Prices"].str.replace("<br>", " | ", regex=False)
    csv = export_df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison_grouped.csv", mime="text/csv")
