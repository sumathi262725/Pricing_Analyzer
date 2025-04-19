import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from serpapi import GoogleSearch
import openai
import os

# Load API keys from environment
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="🛒 Price Comparison App", layout="wide")
st.title("🛍️ Product Price Comparison - US Only")
st.write("Upload a list of product names (CSV or TXT), and compare prices from shopping sites in the US 🇺🇸.")

uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

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

def handle_chat(prompt, df):
    # Dummy logic for now
    if "cheapest" in prompt.lower():
        cheapest = df[df["Price"] == df["Price"].min()]
        return f"📌 The lowest price overall is ${cheapest.iloc[0]['Price']} for {cheapest.iloc[0]['Product']} on {cheapest.iloc[0]['Site']}."
    return "🤖 I'm still learning! Try asking about the cheapest product or site."

if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔎 Searching for prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                lowest_price = min(p[1] for p in price_data)
                for site, price in price_data:
                    results.append({
                        "Product": product,
                        "Site": site,
                        "Price": price,
                        "Lowest Price in Product": lowest_price
                    })
            else:
                results.append({
                    "Product": product,
                    "Site": "No results found",
                    "Price": None,
                    "Lowest Price in Product": None
                })

    df = pd.DataFrame(results)

    # Format output
    st.success("✅ Price comparison complete!")

    formatted_data = []
    for product in df["Product"].unique():
        product_rows = df[df["Product"] == product]
        min_price = product_rows["Price"].min()
        formatted_product = product
        for i, row in product_rows.iterrows():
            formatted_price = f"${row['Price']} ({row['Site']})" if row['Price'] else "N/A"
            formatted_data.append({
                "Product": formatted_product,
                "Site": row['Site'],
                "Price": formatted_price,
                "Lowest Price": f"**🟩 ${min_price} ({row['Site']})**" if row['Price'] == min_price else ""
            })
            formatted_product = ""  # For merging effect

    formatted_df = pd.DataFrame(formatted_data)
    st.dataframe(formatted_df, use_container_width=True)

    # Charts per product
    st.markdown("---")
    st.subheader("📊 Price Charts")
    for product in df["Product"].unique():
        product_data = df[df["Product"] == product].dropna(subset=["Price"])
        if not product_data.empty:
            fig, ax = plt.subplots()
            bars = ax.bar(product_data["Site"], product_data["Price"], color="skyblue")
            min_price_idx = product_data["Price"].idxmin()
            for i, bar in enumerate(bars):
                if product_data.index[i] == min_price_idx:
                    bar.set_color("green")
                    bar.set_edgecolor("black")
                    bar.set_linewidth(2)
            ax.set_title(f"Prices for: {product}")
            ax.set_ylabel("Price ($)")
            ax.set_xlabel("Site")
            st.pyplot(fig)

    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

# Chatbot
st.markdown("---")
st.markdown("### 🤖 Chat with PriceBot")
if prompt := st.chat_input("Ask about product prices, cheapest options, or sites..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if uploaded_file:
            response = handle_chat(prompt, df)
        else:
            response = "⚠️ Please upload a product list to start."
        st.markdown(response)
