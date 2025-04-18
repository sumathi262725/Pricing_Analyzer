import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from collections import defaultdict
from io import BytesIO

# Load environment variables
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# Supported countries for SerpAPI's Google Shopping layout
SUPPORTED_COUNTRIES = {
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "NF": "Norfolk Island",
    "HM": "Heard Island and McDonald Islands",
    "TK": "Tokelau"
}

# Extended country list
ALL_COUNTRIES = {
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "IN": "India",
    "UK": "United Kingdom",
    "DE": "Germany",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "NF": "Norfolk Island",
    "HM": "Heard Island and McDonald Islands",
    "TK": "Tokelau"
}

# Improved fallback search for unsupported regions using Bing
def fallback_bing_search(product):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = f"{product} price"
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    prices = []
    seen_sites = set()
    for li in soup.select("li.b_algo"):
        title = li.find("h2")
        snippet = li.find("p")
        link = li.find("a")
        if title and snippet and link:
            text = snippet.text
            site_name = link.get("href", "").split("/")[2] if "http" in link.get("href", "") else link.get("href", "")
            if site_name in seen_sites:
                continue
            seen_sites.add(site_name)
            for word in text.split():
                if "$" in word or "Rs." in word:
                    price_text = word.replace("Rs.", "").replace("$", "").replace(",", "")
                    try:
                        price = float(price_text)
                        prices.append((site_name, price))
                        break
                    except:
                        continue
    return prices

# Streamlit UI
st.title("\ud83d\udcbc Product Price Comparison App")
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
            "\ud83c\udf0d Select Country for Search",
            options=list(ALL_COUNTRIES.keys()),
            format_func=lambda x: ALL_COUNTRIES[x]
        )

        if country_code not in SUPPORTED_COUNTRIES:
            st.warning(
                f"\u26a0\ufe0f The selected country ({ALL_COUNTRIES[country_code]}) may not return results due to limitations in Google Shopping's supported layout via SerpAPI."
            )

        st.info(
            "\u2139\ufe0f Currently, SerpAPI supports Google Shopping results **only in specific countries** due to Google's shopping layout limitations. "
            "Results may not appear for unsupported countries."
        )

        if st.button("\ud83d\udd0d Start Price Comparison"):
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
                    else:
                        fallback_results = fallback_bing_search(product)
                        for site, price in fallback_results:
                            if price < lowest_price:
                                lowest_price = price
                                lowest_site = site
                            sites_prices.append((site, price))

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

                st.markdown("### \ud83d\udcca Comparison Results")
                st.dataframe(output_df, use_container_width=True)

                # Export options
                st.markdown("#### \ud83d\udcc2 Export Results")
                csv = output_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "price_comparison.csv", "text/csv")

                excel_buffer = BytesIO()
                output_df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
                st.download_button("Download Excel", excel_buffer.getvalue(), "price_comparison.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.warning("Please upload a product list CSV to begin.")
