import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

# Load your API key securely (via env or hardcoded)
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

st.title("🛍️ Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT), and we'll find prices from shopping sites.")

# File uploader for CSV or TXT files
uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

# Parse uploaded file
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        return [line.strip() for line in file.readlines()]
    return []

# Search product prices using SerpAPI
def get_prices(product_name, region):
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": region
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

# Main logic
if uploaded_file:
    # Select region for search
    region = st.selectbox(
        "🌍 Select Region for Price Search",
        options=["us", "uk", "in"],
        format_func=lambda x: {"us": "United States", "uk": "United Kingdom", "in": "India"}[x]
    )

    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔎 Searching for prices..."):
        for product in products:
            price_data = get_prices(product, region)
            if price_data:
                lowest_price = min(p[1] for p in price_data)
                for site, price in price_data:
                    results.append({
                        "Product": product,
                        "Site": site,
                        "Price ($)": price,
                        "Lowest Price ($)": lowest_price
                    })
            else:
                results.append({
                    "Product": product,
                    "Site": "No results found",
                    "Price ($)": None,
                    "Lowest Price ($)": None
                })

    df = pd.DataFrame(results)
    st.success("✅ Price comparison complete!")
    st.dataframe(df)

    # Export option
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")
