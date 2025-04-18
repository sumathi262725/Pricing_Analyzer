import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
from io import BytesIO
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load your API key securely
SERPAPI_KEY = os.getenv("SERPAPI_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# --- UI ---
st.set_page_config(page_title="🛍️ Price Comparison App", layout="wide")
st.title("🛍️ Product Price Comparison")
st.write(
    "Upload a product list (CSV or TXT), and compare prices from online shopping sites in US 🇺🇸 and India 🇮🇳."
)

# File uploader
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

# Function to extract base site name (e.g., "eBay" from "eBay - houstoncellphones")
def get_base_site_name(site):
    # Use regex to extract the base site name (before the '-')
    match = re.match(r"([a-zA-Z0-9]+)", site)
    if match:
        return match.group(1)
    return site

# SerpAPI call with fallback for India
def get_prices(product_name, country_code):
    gl_map = {"US": "us", "IN": "in"}
    location_map = {"US": "United States", "IN": "India"}

    gl_value = gl_map.get(country_code.upper(), "us")
    location_value = location_map.get(country_code.upper(), "United States")

    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": gl_value,
        "location": location_value
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    shopping_results = results.get("shopping_results", [])

    # Fallback for India
    if not shopping_results and country_code.upper() == "IN":
        params["gl"] = "us"
        params["location"] = "United States"
        results = GoogleSearch(params).get_dict()
        shopping_results = results.get("shopping_results", [])

    if not shopping_results:
        st.warning(f"No shopping results found for {product_name} in {country_code}")

    seen_sites = set()
    items = []

    for item in shopping_results:
        site = item.get("source")
        price_str = item.get("price")
        currency_symbol = item.get("currency")

        if site and price_str and currency_symbol:
            base_site_name = get_base_site_name(site)  # Get base site name (e.g., "eBay")
            if base_site_name not in seen_sites:
                # Clean and convert price
                price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
                try:
                    price = float(price_cleaned)
                    # Add currency symbol to the price
                    price_with_currency = f"{currency_symbol}{price}"
                    items.append((base_site_name, price_with_currency))
                    seen_sites.add(base_site_name)
                except ValueError:
                    continue

    return items

# Function to fetch prices concurrently
def fetch_prices_concurrently(products, regions):
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_product = {}
        for product in products:
            for region in regions:
                future = executor.submit(get_prices, product, region)
                future_to_product[future] = (product, region)

        for future in as_completed(future_to_product):
            product, region = future_to_product[future]
            price_data = future.result()

            if price_data:
                # Find the lowest price for this product
                lowest_price = min(p[1] for p in price_data)
                lowest_price_site = [site for site, price in price_data if price == lowest_price][0]

                # Add each site and its price as a separate row
                for site, price in price_data:
                    results.append({
                        "Product": product if site == price_data[0][0] else "",  # Show product name only on first site
                        "Region": region,
                        "Site & Price": f"{site}({price})",
                        "Lowest Price & Site": f"{lowest_price_site}({lowest_price})" if site == lowest_price_site else ""
                    })
            else:
                results.append({
                    "Product": product,
                    "Region": region,
                    "Site & Price": "No results found",
                    "Lowest Price & Site": None
                })
    return results

# Main app logic
if uploaded_file:
    products = parse_file(uploaded_file)

    # Set regions to US and India by default
    selected_regions = ["US", "IN"]

    if products:
        with st.spinner("🔍 Searching for product prices..."):
            results = fetch_prices_concurrently(products, selected_regions)

        # Final Results DataFrame
        if results:
            df = pd.DataFrame(results)

            st.success("✅ Price comparison complete!")

            # Neatly formatted table in the Streamlit UI
            st.dataframe(df.style.set_table_styles(
                [{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
                 {'selector': 'tbody td', 'props': [('font-size', '12px')]}]
            ))

            # CSV Download
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name="price_comparison.csv",
                mime="text/csv",
            )

            # Excel Download
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="PriceComparison")
            st.download_button(
                label="📊 Download Excel",
                data=output.getvalue(),
                file_name="price_comparison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("❌ No results found for any products.")
