import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

# Set your SerpAPI key securely (you can also set this in Streamlit Secrets)
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Upload section
st.title("🛍️ Product Price Comparison Tool")
uploaded_file = st.file_uploader("Upload a file with product names (CSV or TXT)", type=["csv", "txt"])

# Helper to parse uploaded file
def parse_uploaded_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        return [line.strip() for line in file.readlines()]
    return []

# Helper to extract prices from search results
def extract_prices(product_name):
    search = GoogleSearch({
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "engine": "google_shopping",
        "hl": "en",
        "gl": "us"
    })

    results = search.get_dict()
    product_data = []

    for item in results.get("shopping_results", []):
        site = item.get("source")
        price_str = item.get("price")
        if price_str and site:
            try:
                price = float(price_str.replace("$", "").replace(",", "").strip())
                product_data.append((site, price))
            except:
                continue

    return product_data

# Display results
if uploaded_file:
    product_list = parse_uploaded_file(uploaded_file)
    final_data = []

    with st.spinner("🔍 Searching for prices..."):
        for product in product_list:
            data = extract_prices(product)
            if data:
                lowest_price = min(price for _, price in data)
                for site, price in data:
                    final_data.append({
                        "Product": product,
                        "Site": site,
                        "Price ($)": price,
                        "Lowest Price ($)": lowest_price
                    })
            else:
                final_data.append({
                    "Product": product,
                    "Site": "No results",
                    "Price ($)": None,
                    "Lowest Price ($)": None
                })

    df = pd.DataFrame(final_data)
    st.success("✅ Done!")
    st.dataframe(df)

    # Download as CSV
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")
