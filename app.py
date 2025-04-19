import streamlit as st
import pandas as pd
import os
from serpapi import GoogleSearch
import plotly.express as px
import openai
from io import BytesIO
import re

# Load API keys
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Streamlit app settings
st.set_page_config(layout="wide")
st.title("🛍️ Interactive Product Price Comparison (US Only)")
st.write("Upload a product list, compare prices, explore charts, and ask AI questions!")

# File uploader
uploaded_file = st.file_uploader("📄 Upload Product List", type=["csv", "txt"])

@st.cache_data
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

def normalize_product_name(name):
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'[^\w\s\-]', '', name)
    return name.title()

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
        link = item.get("link")
        if site and price_str:
            price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            try:
                price = float(price_cleaned)
                link = link if link else "No URL"
                items.append((site, price, link))
            except:
                continue
    return items

if uploaded_file:
    products = [normalize_product_name(p) for p in parse_file(uploaded_file)]
    results = []

    with st.spinner("🔍 Searching for prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                lowest_price = min([p[1] for p in price_data])
                lowest_price_site = [site for site, price, _ in price_data if price == lowest_price][0]
                for i, (site, price, link) in enumerate(price_data):
                    product_name = f"{product}" if i == 0 else ""
                    lowest_price_value = f"${lowest_price:.2f} ({lowest_price_site})" if i == 0 else ""
                    results.append({
                        "Product": product_name,
                        "Site": site,
                        "Price": round(price, 2),
                        "Lowest Price": lowest_price_value,
                        "URL": link
                    })
            else:
                results.append({
                    "Product": product,
                    "Site": "No results found",
                    "Price": None,
                    "Lowest Price": None,
                    "URL": None
                })

    df = pd.DataFrame(results)

    # Tabbed interface
    tab1, tab2, tab3 = st.tabs(["📋 Table", "📊 Charts", "🤖 AI Assistant"])

    with tab1:
        st.success("✅ Price comparison complete!")
        st.dataframe(df.style.set_properties(subset=["Product", "Lowest Price"], align="center"))

        # Export
        st.subheader("📁 Export Results")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

        excel_file = BytesIO()
        df.to_excel(excel_file, index=False, engine='xlsxwriter')
        excel_file.seek(0)
        st.download_button("📥 Download Excel", data=excel_file, file_name="price_comparison.xlsx")

    with tab2:
        st.subheader("📊 Interactive Price Comparison Charts")
        for product in df["Product"].unique():
            prod_df = df[df["Product"] == product].dropna(subset=["Price"])
            if not prod_df.empty:
                colors = ["orange" if price == prod_df["Price"].min() else "blue" for price in prod_df["Price"]]
                prod_df["Hover Info"] = prod_df.apply(
                    lambda row: f'<b>{row["Site"]}</b><br>Price: ${row["Price"]:.2f}<br><a href="{row["URL"]}" target="_blank">View Product</a>',
                    axis=1
                )
                fig = px.bar(
                    prod_df,
                    x="Site",
                    y="Price",
                    color=colors,
                    hover_data={"Hover Info": True},
                    title=f"Prices for {product}",
                    color_discrete_sequence=["blue", "orange"]
                )
                fig.update_traces(marker_line_width=1.5, hovertemplate=prod_df["Hover Info"])
                fig.update_layout(hovermode="closest")
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("💬 Ask the AI Assistant")
        chat_input = st.text_input("Ask a question about the prices or products")
        if chat_input:
            with st.spinner("🤖 Thinking..."):
                context = df.to_string(index=False)
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for analyzing product prices."},
                        {"role": "user", "content": f"Product data:\n{context}\n\nQuestion: {chat_input}"}
                    ]
                )
                st.markdown("**AI Response:**")
                st.write(response.choices[0].message.content)
