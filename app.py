import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
import io
import matplotlib.pyplot as plt

# Load API Key
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Streamlit UI
st.title("🛍️ US Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT) to compare prices from shopping sites in the United States 🇺🇸.")

uploaded_file = st.file_uploader("📄 Upload product list (CSV or TXT)", type=["csv", "txt"])

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

    with st.spinner("🔎 Searching for US prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                # Get site offering lowest price
                site, price = min(price_data, key=lambda x: x[1])
                formatted = f"${price:.2f} ({site})"
                results.append({
                    "Product & Lowest Price": f"{product}",
                    "Lowest Price": formatted
                })
            else:
                results.append({
                    "Product & Lowest Price": f"{product}",
                    "Lowest Price": "No results found"
                })

    df = pd.DataFrame(results)

    st.success("✅ US price comparison complete!")

    # 🖼️ Stylish display
    def highlight_price(val):
        if val != "No results found":
            return 'font-weight: bold; color: green; text-align: center;'
        return 'color: red; text-align: center;'

    styled_df = df.style.set_properties(**{
        'Product & Lowest Price': 'text-align: center; font-weight: bold'
    }).applymap(highlight_price, subset=['Lowest Price'])

    st.dataframe(styled_df, use_container_width=True)

    # 📊 Chart
    st.subheader("📊 Price Chart")
    for product_row in results:
        product = product_row["Product & Lowest Price"]
        price_info = product_row["Lowest Price"]
        if price_info != "No results found":
            price_val = float(price_info.split(" ")[0].replace("$", ""))
            site = price_info.split("(")[-1].rstrip(")")
            fig, ax = plt.subplots()
            ax.barh([site], [price_val], color="skyblue")
            ax.set_xlabel("Price (USD)")
            ax.set_title(f"{product} - Lowest Price")
            st.pyplot(fig)

    # 📥 Export to CSV / Excel
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results (CSV)", data=csv, file_name="us_price_comparison.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
    st.download_button("📊 Download Results (Excel)", data=excel_buffer, file_name="us_price_comparison.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
