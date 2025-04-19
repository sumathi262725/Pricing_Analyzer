import streamlit as st
import pandas as pd
import os
from serpapi import GoogleSearch
import plotly.graph_objects as go
import openai
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Client Setup
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY not set.")
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Layout
st.set_page_config(layout="wide")
st.title("🛍️ Product Price Comparison App (US)")

# Tabs
tabs = st.tabs(["📥 Upload & Compare", "📊 Charts", "💬 AI Chat"])

# Tab 1: Upload & Compare
with tabs[0]:
    st.subheader("Step 1: Upload Your Product List")
    uploaded_file = st.file_uploader("Upload CSV or TXT", type=["csv", "txt"])

    @st.cache_data
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
            link = item.get("link")
            rating = item.get("rating", 0)
            if site and price_str:
                price_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
                try:
                    price = float(price_cleaned)
                    items.append((site, price, link, rating))
                except:
                    continue
        return items

    if uploaded_file:
        products = parse_file(uploaded_file)
        results = []

        with st.spinner("🔍 Searching for prices..."):
            for product in products:
                price_data = get_prices(product)
                if price_data:
                    lowest_price = min(p[1] for p in price_data)
                    for site, price, link, rating in price_data:
                        results.append({
                            "Product": product,
                            "Site": site,
                            "Price": price,
                            "URL": link,
                            "Rating": rating,
                            "Lowest Price": f"${lowest_price:.2f}" if price == lowest_price else ""
                        })
                else:
                    results.append({
                        "Product": product,
                        "Site": "No results",
                        "Price": None,
                        "URL": None,
                        "Rating": None,
                        "Lowest Price": None
                    })

        df = pd.DataFrame(results)
        st.session_state.df = df

        st.success("✅ Price comparison complete!")
        st.dataframe(df.drop(columns=["URL"]))

        # Export options
        st.subheader("📁 Export Results")

        csv = df.to_csv(index=False, encoding="utf-8", errors="ignore").encode("utf-8")
        st.download_button("📥 Download CSV", csv, "price_comparison.csv", mime="text/csv")

        excel_file = BytesIO()
        df_clean = df.copy()
        df_clean = df_clean.applymap(lambda x: str(x).encode("utf-8", "ignore").decode("utf-8") if isinstance(x, str) else x)
        df_clean.to_excel(excel_file, index=False, engine='xlsxwriter')
        excel_file.seek(0)
        st.download_button("📥 Download Excel", excel_file, "price_comparison.xlsx")

# Tab 2: Charts
with tabs[1]:
    st.subheader("📊 Side-by-Side Price Charts")
    if "df" in st.session_state:
        df = st.session_state.df
        for product in df["Product"].unique():
            prod_df = df[df["Product"] == product].dropna(subset=["Price"])

            if not prod_df.empty:
                fig = go.Figure()
                for idx, row in prod_df.iterrows():
                    fig.add_trace(go.Bar(
                        x=[row["Site"]],
                        y=[row["Price"]],
                        name=row["Site"],
                        marker_color="orange" if row["Price"] == prod_df["Price"].min() else "steelblue",
                        hovertemplate=f"<b>{row['Site']}</b><br>Price: ${row['Price']:.2f}<br><a href='{row['URL']}' target='_blank'>Visit</a><extra></extra>"
                    ))

                fig.update_layout(
                    title_text=f"Prices for {product}",
                    barmode='group',
                    xaxis_title="Site",
                    yaxis_title="Price (USD)",
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload a file first to see charts.")

# Tab 3: Chat
with tabs[2]:
    st.subheader("💬 Ask the AI Assistant")
    if "df" in st.session_state:
        df = st.session_state.df
        chat_input = st.text_input("Ask about the products or pricing:")
        if chat_input:
            with st.spinner("🤖 Thinking..."):
                try:
                    context = df.drop(columns=["URL"]).to_string(index=False)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert pricing analyst."},
                            {"role": "user", "content": f"Product data:\n{context}\n\nQuestion: {chat_input}"}
                        ]
                    )
                    st.markdown("**AI Response:**")
                    st.write(response.choices[0].message.content)
                except openai.RateLimitError:
                    st.error("🚫 OpenAI API quota exceeded.")
    else:
        st.info("Upload product data first to ask questions.")
