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

# Query SerpAPI for shopping prices with country-based filtering
def get_prices(product_name, country_code):
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",  # English language
        "gl": country_code.lower()  # Geolocation by country
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
    
    # Group prices by marketplace (e.g., eBay, Amazon) and get the lowest price per marketplace
    grouped_items = {}
    for site, price in items:
        # We identify the marketplace by checking the site string
        marketplace = site.split()[0]  # First part is typically the marketplace name (e.g., "eBay", "Amazon")
        if marketplace not in grouped_items:
            grouped_items[marketplace] = []
        grouped_items[marketplace].append(price)
    
    # Get lowest price per marketplace
    final_items = []
    for marketplace, prices in grouped_items.items():
        lowest_price = min(prices)
        final_items.append((marketplace, lowest_price))

    return final_items

# Main app logic
if uploaded_file:
    # Step 1: Parse the product list
    products = parse_file(uploaded_file)
    
    # Step 2: Display country selection after the file upload
    country_code = st.selectbox("Select Country for Search", ["US", "UK", "DE", "IN", "CA"], index=0)

    # Step 3: Run the search for prices
    grouped_results = []

    with st.spinner("🔍 Searching for prices..."):
        for product in products:
            price_data = get_prices(product, country_code)
            if price_data:
                sites_prices = [f"{site}: ${price:.2f}" for site, price in price_data]
                lowest_entry = min(price_data, key=lambda x: x[1])
                lowest_site, lowest_price = lowest_entry
                grouped_results.append({
                    "Product": product,
                    "Sites & Prices": "<br>".join(sites_prices),
                    "Lowest Price ($)": f"<b>${lowest_price:.2f}</b> ({lowest_site})",
                    "_sort_price": lowest_price  # for sorting
                })
            else:
                grouped_results.append({
                    "Product": product,
                    "Sites & Prices": "No results found",
                    "Lowest Price ($)": "N/A",
                    "_sort_price": float("inf")  # sort missing values last
                })

    # Create dataframe and sort by lowest price
    df = pd.DataFrame(grouped_results).sort_values(by="_sort_price").drop(columns=["_sort_price"])

    # Display the results with HTML formatting for the lowest price
    st.success("✅ Price comparison complete!")
    st.write("### 🧾 Sorted Results (by Lowest Price)")
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Clean up the export version of the dataframe
    export_df = df.copy()
    export_df["Sites & Prices"] = export_df["Sites & Prices"].str.replace("<br>", " | ", regex=False)
    export_df["Lowest Price ($)"] = export_df["Lowest Price ($)"].str.replace("<b>", "", regex=False).str.replace("</b>", "", regex=False)
    csv = export_df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison_grouped.csv", mime="text/csv")
