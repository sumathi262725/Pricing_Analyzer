import streamlit as st
import pandas as pd
import os
from serpapi import GoogleSearch
import plotly.express as px
import openai
from io import BytesIO
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY not set. Please set the API key in your environment variables or secrets.")
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(layout="wide")
st.title("🛍️ Interactive Product Price Comparison (US Only)")

# Tabs
tabs = st.tabs(["📥 Upload & Compare", "📊 Charts", "💬 AI Chat"])

# Tab 1: Upload & Compare
with tabs[0]:
    st.subheader("Step 1: Upload Your Product List")
    uploaded_file = st.file_uploader("Upload a CSV or TXT file with product names", type=["csv", "txt"])

    @st.cache_data
    def parse_file(file):
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
            return df.iloc[:, 0].dropna().tolist()
        elif file.name.endswith(".txt"):
            content = file.read().decode("utf-8").splitlines()
            return [line.strip() for line in content if line.strip()]
        return []

    def normalize_name(name):
        return name.lower().strip()

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
                    items.append((site, price, link))
                except:
                    continue
        return items

    if uploaded_file:
        products = parse_file(uploaded_file)
        results = []

        with st.spinner("🔍 Searching for prices..."):
            for product in products:
                normalized = normalize_name(product)
                price_data = get_prices(normalized)
                if price_data:
                    lowest_price = min([p[1] for p in price_data])
                    lowest_price_site = [site for site, price, _ in price_data if price == lowest_price][0]
                    for i, (site, price, link) in enumerate(price_data):
                        product_name = f"{product}" if i == 0 else ""
                        lowest_price_value = f"${lowest_price:.2f} ({lowest_price_site})" if i == 0 else ""
                        results.append({
                            "Product": product_name,
                            "Site": site,
                            "Price": price,
                            "URL": link,
                            "Lowest Price": lowest_price_value,
                        })
                else:
                    results.append({
                        "Product": product,
                        "Site": "No results found",
                        "Price": None,
                        "URL": None,
                        "Lowest Price": None,
                    })

        df = pd.DataFrame(results)

        st.success("✅ Price comparison complete!")
        st.dataframe(df.drop(columns=["URL"]).style.set_properties(subset=["Product", "Lowest Price"], align="center"))

        # Export
        st.subheader("📁 Export Results")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

        excel_file = BytesIO()
        df.to_excel(excel_file, index=False, engine='xlsxwriter')
        excel_file.seek(0)
        st.download_button("📥 Download Excel", data=excel_file, file_name="price_comparison.xlsx")

        st.session_state.df = df

# Tab 2: Charts
with tabs[1]:
    st.subheader("📊 Interactive Price Comparison Charts")
    if "df" in st.session_state:
        df = st.session_state.df.copy()

        for product in df["Product"].unique():
            prod_df = df[df["Product"] == product].dropna(subset=["Price"])

            if not prod_df.empty:
                # Determine color column for highlighting lowest price
                min_price = prod_df["Price"].min()
                prod_df["Highlight"] = prod_df["Price"].apply(lambda p: "Lowest" if p == min_price else "Other")

                # Format hover text (without HTML links, since Plotly disables them in tooltips)
                prod_df["Hover"] = prod_df.apply(
                    lambda row: f"{row['Site']}: ${row['Price']:.2f}"
                    + (f"\nURL: {row['URL']}" if row['URL'] else ""),
                    axis=1
                )

                fig = px.bar(
                    prod_df,
                    x="Site",
                    y="Price",
                    color="Highlight",
                    color_discrete_map={"Lowest": "orange", "Other": "blue"},
                    title=f"Prices for {product}",
                    hover_data={"Hover": True, "Price": False, "Highlight": False, "URL": False}
                )

                fig.update_traces(marker_line_width=1.5, hovertemplate="%{customdata[0]}")
                st.plotly_chart(fig, use_container_width=True)

                # Show direct links below chart
                st.markdown("🔗 **Product Links:**")
                for _, row in prod_df.iterrows():
                    if row["URL"]:
                        st.markdown(f"- [{row['Site']}]({row['URL']}) - `${row['Price']:.2f}`")
    else:
        st.info("Upload a product list in the first tab to generate charts.")

# Tab 3: Chat
with tabs[2]:
    st.subheader("💬 Ask the AI Assistant")
    if "df" in st.session_state:
        df = st.session_state.df
        chat_input = st.text_input("Ask a question about the products or prices")
        if chat_input:
            with st.spinner("🤖 Thinking..."):
                try:
                    context = df.drop(columns=["URL"]).to_string(index=False)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant for analyzing product prices."},
                            {"role": "user", "content": f"Product data:\n{context}\n\nQuestion: {chat_input}"}
                        ]
                    )
                    st.markdown("**AI Response:**")
                    st.write(response.choices[0].message.content)
                except openai.RateLimitError:
                    st.error("🚫 OpenAI API quota exceeded. Please check your usage and billing at platform.openai.com.")
    else:
        st.info("Upload a product list in the first tab to ask questions.")
