import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from serpapi import GoogleSearch
import os

# Load API key from environment
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# Streamlit app title
st.title("🛍️ US Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT). The app fetches prices from US shopping sites.")

# File uploader
uploaded_file = st.file_uploader("📄 Upload product list (CSV/TXT)", type=["csv", "txt"])

# Parse uploaded file
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

# Get prices using SerpAPI
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
            try:
                price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
                price = float(price_cleaned)
                items.append((site, price))
            except:
                continue
    return items

# Format lowest price
def format_price(price, site):
    return f"**:green[${price} ({site})]**"

# Format merged cell-like HTML
def merge_cell(value, align='center', bold=False):
    style = f"text-align:{align};"
    if bold:
        style += " font-weight:bold;"
    return f'<div style="{style}">{value}</div>'

# Handle user queries
def handle_chat(prompt, df):
    prompt = prompt.lower()
    if "cheapest" in prompt or "lowest" in prompt:
        cheapest = df[df["Price"] == df["Price"].min()]
        row = cheapest.iloc[0]
        return f"The cheapest product is **{row['Product']}** for **${row['Price']}** at **{row['Site']}**."
    elif "average" in prompt:
        avg = df["Price"].mean()
        return f"The average price across all products is **${avg:.2f}**."
    elif "sites" in prompt:
        sites = df["Site"].unique()
        return f"Prices were fetched from: {', '.join(sites)}."
    else:
        return "I can help with questions like: 'What's the lowest price?', 'Average price?', 'Which sites?'"

# Main logic
if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔎 Searching for prices in US..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                lowest_price, lowest_site = min(price_data, key=lambda x: x[1])
                for site, price in price_data:
                    results.append({
                        "Product": product,
                        "Site": site,
                        "Price": price,
                        "Lowest Price Display": format_price(lowest_price, lowest_site)
                    })
            else:
                results.append({
                    "Product": product,
                    "Site": "No results",
                    "Price": None,
                    "Lowest Price Display": "-"
                })

    df = pd.DataFrame(results)

    if not df.empty:
        # Format table display
        styled_df = df.copy()
        styled_df["Product"] = styled_df["Product"].apply(lambda x: merge_cell(x, bold=True))
        styled_df["Lowest Price"] = styled_df["Lowest Price Display"].apply(lambda x: merge_cell(x))
        styled_df.drop(columns=["Lowest Price Display"], inplace=True)

        st.success("✅ Price comparison complete!")
        st.markdown("### 📋 Results Table")
        st.write("Below is the price comparison:")

        st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button("📥 Download Results (CSV)", data=csv, file_name="price_comparison.csv", mime="text/csv")

        # Plot bar charts for each product
        st.markdown("### 📊 Price Comparison Charts")
        for product in df["Product"].unique():
            product_df = df[df["Product"].str.contains(product.split()[0], case=False)]

            if product_df.empty:
                continue

            fig, ax = plt.subplots()
            bars = ax.bar(product_df["Site"], product_df["Price"], color="skyblue")
            ax.set_title(product)
            ax.set_ylabel("Price ($)")
            ax.set_xlabel("Sites")

            # Highlight lowest
            min_price = product_df["Price"].min()
            for i, bar in enumerate(bars):
                if product_df.iloc[i]["Price"] == min_price:
                    bar.set_color("green")
                    bar.set_edgecolor("black")
                    bar.set_linewidth(2)

            st.pyplot(fig)

        # Chatbot
        st.markdown("### 💬 Chat with PriceBot")
        if prompt := st.chat_input("Ask anything like 'lowest price?', 'average?', 'which site?'"):
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response = handle_chat(prompt, df)
                st.markdown(response)
