import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

# Load your API key securely
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Streamlit UI
st.title("🛍️ Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT), and select regions to compare prices from shopping sites in US 🇺🇸, UK 🇬🇧, and India 🇮🇳.")

uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

# Parse uploaded file
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

# Search product prices using SerpAPI
def get_prices(product_name, country_code):
    gl_map = {
        "US": "us",
        "UK": "uk",
        "IN": "in"
    }
    gl_value = gl_map.get(country_code.upper(), "us")

    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": gl_value
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    items = []
    for item in results.get("shopping_results", []):
        site = item.get("source")
        price_str = item.get("price")
        if site and price_str:
            price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            try:
                price = float(price_cleaned)
                items.append((site, price))
            except:
                continue
    return items

# Main logic
if uploaded_file:
    products = parse_file(uploaded_file)

    # Let user select regions
    selected_regions = st.multiselect(
        "🌍 Select regions to search prices in:",
        options=["US", "UK", "IN"],
        default=["US"]
    )

    if selected_regions:
        results = []

        with st.spinner("🔎 Searching for prices..."):
            for product in products:
                for region in selected_regions:
                    price_data = get_prices(product, region)
                    if price_data:
                        lowest_price = min(p[1] for p in price_data)
                        for site, price in price_data:
                            results.append({
                                "Product": product,
                                "Region": region,
                                "Site": site,
                                "Price": price,
                                "Lowest Price in Region": lowest_price
                            })
                    else:
                        results.append({
                            "Product": product,
                            "Region": region,
                            "Site": "No results found",
                            "Price": None,
                            "Lowest Price in Region": None
                        })

        df = pd.DataFrame(results)
        st.success("✅ Price comparison complete!")
        st.dataframe(df)

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")
