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
    st.error("\u274c OPENAI_API_KEY not set. Please set the API key in your environment variables or secrets.")
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(layout="wide")
st.title("\ud83d\udecd\ufe0f Interactive Product Price Comparison (US Only)")

# Tabs
tabs = st.tabs(["\ud83d\udcc5 Upload & Compare", "\ud83d\udcca Charts", "\ud83d\udcac AI Chat"])

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

        with st.spinner("\ud83d\udd0d Searching for prices..."):
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

        st.success("\u2705 Price comparison complete!")
        st.dataframe(df.drop(columns=["URL"]).style.set_properties(subset=["Product", "Lowest Price"], align="center"))

        # Export
        st.subheader("\ud83d\udcc1 Export Results")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("\ud83d\udcc5 Download CSV", data=csv, file_name="price_comparison.csv", mime="text/csv")

        excel_file = BytesIO()
        df.to_excel(excel_file, index=False, engine='xlsxwriter')
        excel_file.seek(0)
        st.download_button("\ud83d\udcc5 Download Excel", data=excel_file, file_name="price_comparison.xlsx")

        st.session_state.df = df

# Tab 2: Charts
with tabs[1]:
    st.subheader("\ud83d\udcca Interactive Price Comparison Charts with Seller Ratings")
    if "df" in st.session_state:
        df = st.session_state.df.copy()

        grouped = df.groupby("Product")
        col1, col2 = st.columns(2)
        toggle = True

        for product, group in grouped:
            group = group.dropna(subset=["Price"])
            if group.empty:
                continue

            group["Seller Rating"] = group["Site"].apply(lambda x: {
                "Amazon": 4.7, "Walmart": 4.3, "Target": 4.1, "Best Buy": 4.4
            }.get(x, 4.0))

            min_price = group["Price"].min()
            group["Color"] = group["Price"].apply(lambda x: "Lowest Price" if x == min_price else "Other")

            group["Hover"] = group.apply(
                lambda row: f"{row['Site']}: ${row['Price']:.2f}<br>Rating: {row['Seller Rating']}/5" +
                            (f"<br>{row['URL']}" if row['URL'] else ""), axis=1)

            fig = px.bar(
                group,
                x="Site",
                y="Price",
                color="Color",
                color_discrete_map={"Lowest Price": "orange", "Other": "steelblue"},
                hover_data={"Hover": True, "Price": False, "Color": False, "URL": False, "Seller Rating": False},
            )

            fig.add_scatter(
                x=group["Site"],
                y=group["Seller Rating"],
                mode='lines+markers',
                name='Seller Rating (0–5)',
                yaxis='y2',
                marker=dict(size=8, color='green'),
                line=dict(dash='dash')
            )

            fig.update_layout(
                title=f"\ud83d\uded2 {product}",
                xaxis=dict(title="Website"),
                yaxis=dict(title="Price (USD)"),
                yaxis2=dict(title="Seller Rating", overlaying='y', side='right', range=[0, 5]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                hovermode="x unified",
                bargap=0.3
            )

            if toggle:
                with col1:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                with col2:
                    st.plotly_chart(fig, use_container_width=True)
            toggle = not toggle

            st.markdown("\ud83d\udd17 **Product Links:**")
            for _, row in group.iterrows():
                if row["URL"]:
                    st.markdown(f"- [{row['Site']}]({row['URL']}) - `${row['Price']:.2f}`, Rating: {row['Seller Rating']}/5")
    else:
        st.info("Upload a product list in the first tab to generate charts.")

# Tab 3: Chat
with tabs[2]:
    st.subheader("\ud83d\udcac Ask the AI Assistant")
    if "df" in st.session_state:
        df = st.session_state.df
        chat_input = st.text_input("Ask a question about the products or prices")
        if chat_input:
            with st.spinner("\ud83e\udde0 Thinking..."):
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
                    st.error("\ud83d\udeab OpenAI API quota exceeded. Please check your usage and billing at platform.openai.com.")
    else:
        st.info("Upload a product list in the first tab to ask questions.")
