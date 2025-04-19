import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from serpapi import GoogleSearch
import os
import openai

# Load API Keys
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
openai.api_key = OPENAI_API_KEY

# App Title
st.title("🛍️ US Product Price Comparison")
st.write("Upload a product list (CSV or TXT) to compare US prices and visualize them with charts.")

uploaded_file = st.file_uploader("📄 Upload product list", type=["csv", "txt"])

# Parse File
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        return [line.strip() for line in file.read().decode("utf-8").splitlines() if line.strip()]
    return []

# Get Prices from SerpAPI
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

# Plot Chart
def plot_prices(product_name, price_data):
    if not price_data:
        st.warning(f"No prices found for {product_name}")
        return

    sites = [site for site, _ in price_data]
    prices = [price for _, price in price_data]

    min_index = prices.index(min(prices))
    colors = ['#4CAF50' if i != min_index else 'red' for i in range(len(prices))]

    fig, ax = plt.subplots()
    bars = ax.bar(sites, prices, color=colors)
    ax.set_title(f"{product_name} - Price Comparison")
    ax.set_ylabel("Price (USD)")
    ax.set_xlabel("Retailer")
    for bar, price in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"${price:.2f}", 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    st.pyplot(fig)

# Main Logic
if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔍 Searching for prices..."):
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

    def highlight_lowest(val):
        if isinstance(val, str) and val.startswith("$"):
            return "color: red; font-weight: bold; text-align: center"
        return ""

    styled_df = df.style \
        .applymap(lambda v: "font-weight: bold; text-align: center" if v != "" else "color: transparent", subset=["Product"]) \
        .applymap(highlight_lowest, subset=["Lowest Price in Region"])

    st.dataframe(styled_df, use_container_width=True)

    for product in products:
        product_data = df[df["Product"] == product]
        if product_data.empty:
            product_data = df[df["Product"] == ""]
        plot_prices(product, [(row["Site"], row["Price"]) for _, row in product_data.iterrows() if row["Price"]])

    # CSV Download
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

# Chatbot Interface
st.markdown("---")
st.subheader("💬 Ask me anything about product prices")

user_input = st.text_input("Type your question:")

if user_input:
    with st.spinner("Thinking..."):
        prompt = f"You are an assistant helping with product price comparison. The user asked:\n\n{user_input}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        st.write(response.choices[0].message.content.strip())
