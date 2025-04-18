import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
from io import BytesIO

# Load your API key securely
SERPAPI_KEY = os.getenv("SERPAPI_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# --- UI ---
st.set_page_config(page_title="🛍️ Price Comparison App", layout="wide")
st.title("🛍️ Product Price Comparison")
st.write(
    "Upload a product list (CSV or TXT), choose regions, and compare prices from online shopping sites in US 🇺🇸, UK 🇬🇧, and India 🇮🇳."
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

# SerpAPI call with fallback for India
def get_prices(product_name, country_code):
    gl_map = {"US": "us", "UK": "uk", "IN": "in"}
    location_map = {"US": "United States", "UK": "United Kingdom", "IN": "India"}

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
        st.info(f"🔁 No results in India for '{product_name}'. Trying US fallback.")
        params["gl"] = "us"
        params["location"] = "United States"
        results = GoogleSearch(params).get_dict()
        shopping_results = results.get("shopping_results", [])

    seen_sites = set()
    items = []

    for item in shopping_results:
        site = item.get("source")
        price_str = item.get("price")

        if site and price_str and site not in seen_sites:
            price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            try:
                price = float(price_cleaned)
                items.append((site, price))
                seen_sites.add(site)
            except ValueError:
                continue

    return items

# Main app logic
if uploaded_file:
    products = parse_file(uploaded_file)

    selected_regions = st.multiselect(
        "🌍 Select one or more regions:", ["US", "UK", "IN"]
    )

    if not selected_regions:
        st.warning("⚠️ Please select at least one region to proceed.")
    elif products:
        results = []
        seen_entries = set()  # To avoid duplicates across products/regions/sites
        product_prices = {}  # Store lowest price for each product
        product_sites = {}  # Store sites for each product

        with st.spinner("🔍 Searching for product prices..."):
            for product in products:
                for region in selected_regions:
                    price_data = get_prices(product, region)
                    if price_data:
                        lowest_price = min(p[1] for p in price_data)
                        if product not in product_prices or lowest_price < product_prices[product]:
                            product_prices[product] = lowest_price

                        if product not in product_sites:
                            product_sites[product] = []

                        for site, price in price_data:
                            key = (product.lower(), region, site.lower())
                            if key not in seen_entries:
                                results.append({
                                    "Product": product,
                                    "Region": region,
                                    "Site": site,
                                    "Price": price,
                                    "Lowest Price in Region": lowest_price
                                })
                                seen_entries.add(key)
                                product_sites[product].append({"Site": site, "Price": price})

                    else:
                        results.append({
                            "Product": product,
                            "Region": region,
                            "Site": "No results found",
                            "Price": None,
                            "Lowest Price in Region": None
                        })

        # Aggregated results: Single product name, lowest price, and sites
        final_results = []
        for product, lowest_price in product_prices.items():
            sites_info = ", ".join([f"{entry['Site']} ({entry['Price']})" for entry in product_sites[product]])
            final_results.append({
                "Product": product,
                "Lowest Price": lowest_price,
                "Sites": sites_info
            })

        if final_results:
            df = pd.DataFrame(final_results)
            st.success("✅ Price comparison complete!")
            st.dataframe(df)

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
