import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
import matplotlib.pyplot as plt

# Load API Key
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# UI Title
st.title("🛍️ Product Price Comparison (US Only)")
st.write("Upload a list of product names (CSV or TXT) to compare prices from US shopping sites 🇺🇸.")

uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

# File Parser
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

# SerpAPI Search
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

# Chart Renderer
def plot_prices(product_name, price_data):
    if not price_data:
        st.warning(f"No prices found for {product_name}")
        return
    sites = [s for s, _ in price_data]
    prices = [p for _, p in price_data]

    fig, ax = plt.subplots()
    bars = ax.bar(sites, prices, color="#4CAF50")
    ax.set_title(f"{product_name} - Price Comparison")
    ax.set_ylabel("Price (USD)")
    ax.set_xlabel("Retailer")
    for bar, price in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"${price:.2f}", 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    st.pyplot(fig)

# Main Execution
if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔎 Searching for prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                sorted_data = sorted(price_data, key=lambda x: x[1])
                lowest_site, lowest_price = sorted_data[0]
                for idx, (site, price) in enumerate(sorted_data):
                    results.append({
                        "Product": product if idx == 0 else "",
                        "Region": "US",
                        "Site": site,
                        "Price": price,
                        "Lowest Price in Region": f"${lowest_price:.2f} ({lowest_site})" if idx == 0 else ""
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

    # Styling
    def highlight_lowest(val):
        if isinstance(val, str) and val.startswith("$"):
            return "color: green; font-weight: bold; text-align: center"
        elif "No results" in str(val):
            return "color: red; text-align: center"
        return ""

    styled_df = df.style \
        .applymap(lambda v: "font-weight: bold; text-align: center" if v != "" else "color: transparent", subset=["Product"]) \
        .applymap(highlight_lowest, subset=["Lowest Price in Region"])

    st.dataframe(styled_df, use_container_width=True)

    # Show bar charts
    for product in products:
        data = df[df["Product"] == product]
        if data.empty:
            data = df[df["Product"] == ""].iloc[0:len(df[df["Product"] == ""])]
        plot_prices(product, [(row["Site"], row["Price"]) for _, row in df[df["Product"] == product].iterrows() if row["Price"]])

    # CSV Download
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")
