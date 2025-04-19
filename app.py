import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

# Load your API key securely
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Streamlit UI
st.title("🛍️ Product Price Comparison (US Only)")
st.write("Upload a list of product names (CSV or TXT) to compare prices from US shopping sites 🇺🇸.")

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
    results = []

    with st.spinner("🔎 Searching for prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                lowest_price = min(p[1] for p in price_data)
                lowest_site = [site for site, price in price_data if price == lowest_price][0]
                for site, price in price_data:
                    results.append({
                        "Product": product,
                        "Region": "US",
                        "Site": site,
                        "Price": price,
                        "Lowest Price in Region": f"${lowest_price:.2f} ({lowest_site})"
                    })
            else:
                results.append({
                    "Product": product,
                    "Region": "US",
                    "Site": "No results found",
                    "Price": None,
                    "Lowest Price in Region": "No results"
                })

    df = pd.DataFrame(results)

    st.success("✅ Price comparison complete!")

    # Styling for selected columns
    def style_result(val, col_name):
        if col_name == "Product":
            return "text-align: center; font-weight: bold"
        elif col_name == "Lowest Price in Region":
            if "No results" in val:
                return "text-align: center; color: red"
            return "text-align: center; color: green; font-weight: bold"
        return ""

    styled_df = df.style.applymap(lambda val: style_result(val, "Product"), subset=["Product"]) \
                        .applymap(lambda val: style_result(val, "Lowest Price in Region"), subset=["Lowest Price in Region"])

    st.dataframe(styled_df, use_container_width=True)

    # CSV export
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")
