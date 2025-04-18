import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os

from io import BytesIO

# Load environment variables
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Supported countries for SerpAPI's Google Shopping layout
SUPPORTED_COUNTRIES = {
    "US": "United States",
    "UK": "United Kingdom",
    "IN": "India"
}

# Streamlit UI
st.title("💰 Product Price Comparison App")
st.markdown("Upload a list of product names to compare prices across multiple sites.")

# Upload CSV file
uploaded_file = st.file_uploader("Upload a CSV file with a column named 'product'", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'product' not in df.columns:
        st.error("CSV must contain a 'product' column.")
    else:
        # Select country
        country_code = st.selectbox(
            "🌍 Select Country for Search",
            options=list(SUPPORTED_COUNTRIES.keys()),
            format_func=lambda x: SUPPORTED_COUNTRIES[x]
        )

        st.info(
            "ℹ️ Currently, SerpAPI supports Google Shopping results **only in specific countries**. "
            "Results may not appear for unsupported countries."
        )

        if st.button("🔍 Start Price Comparison"):
            with st.spinner("Searching prices, please wait..."):
                results = []

                for product in df['product']:
                    sites_prices = []
                    lowest_price = float('inf')
                    lowest_site = ""

                    if country_code in SUPPORTED_COUNTRIES:
                        search = GoogleSearch({
                            "q": product,
                            "api_key": SERPAPI_KEY,
                            "engine": "google_shopping",
                            "gl": country_code,
                            "hl": "en"
                        })
                        response = search.get_dict()
                        product_results = response.get("shopping_results", [])

                        for item in product_results:
                            price_str = item.get("price", "").replace("$", "").replace(",", "")
                            source = item.get("source", "")
                            seller = item.get("seller", "")
                            try:
                                price = float(price_str)
                            except:
                                continue

                            site_label = f"{source} - {seller}" if seller else source

                            if price < lowest_price:
                                lowest_price = price
                                lowest_site = site_label

                            sites_prices.append((site_label, price))

                    results.append({
                        "product": product,
                        "sites_prices": sites_prices,
                        "lowest_price": lowest_price,
                        "lowest_site": lowest_site
                    })

                # Prepare display DataFrame
                table_data = []
                for result in results:
                    sites_prices_str = "\n".join([
                        f"**{site}: ${price:.2f}**" if price == result['lowest_price'] else f"{site}: ${price:.2f}"
                        for site, price in result['sites_prices']
                    ])

                    table_data.append({
                        "Product": result['product'],
                        "Sites & Prices": sites_prices_str,
                        "Lowest Price ($)": f"${result['lowest_price']:.2f} ({result['lowest_site']})"
                    })

                output_df = pd.DataFrame(table_data)
                output_df = output_df.sort_values(by="Lowest Price ($)")

                st.markdown("### 📊 Comparison Results")
                st.dataframe(output_df, use_container_width=True)

                # Export options
                st.markdown("#### 📥 Export Results")
                csv = output_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "price_comparison.csv", "text/csv")

                excel_buffer = BytesIO()
                output_df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
                st.download_button("Download Excel", excel_buffer.getvalue(), "price_comparison.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.warning("Please upload a product list CSV to begin.")
