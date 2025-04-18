import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
from google_search_results import GoogleSearch
import os

# Load your API key securely (via env or hardcoded)
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

st.title("🛍️ Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT), and we'll find prices from shopping sites.")

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
def get_prices(product_name, country_code):
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": country_code  # Country-specific code like "us", "uk", "in"
    }
    
    # Using GoogleSearch class from serpapi
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
            except ValueError:
                continue
    return items

# Main logic
if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    # Country code selection for different regions
    country_code = st.selectbox(
        "🌍 Select Country for Search",
        options=["us", "uk", "in"],  # US, UK, India
        index=0,  # Default to 'us'
        format_func=lambda x: {"us": "United States", "uk": "United Kingdom", "in": "India"}[x]
    )

    with st.spinner("🔎 Searching for prices..."):
        for product in products:
            price_data = get_prices(product, country_code)
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

    # Display results in a DataFrame
    df = pd.DataFrame(results)
    st.success("✅ Price comparison complete!")
    st.dataframe(df)

    # Export options
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
    st.download_button("📥 Download Results as Excel", data=excel_buffer.getvalue(), file_name="price_comparison.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.warning("Please upload a product list CSV or TXT to begin.")
