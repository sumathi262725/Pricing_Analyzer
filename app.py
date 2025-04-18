import streamlit as st
import pandas as pd
import requests
from serpapi import GoogleSearch
from datetime import datetime
import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Streamlit config
st.set_page_config(page_title="Price Tracker", layout="wide")

# SerpAPI Key (use either env var or paste directly)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc")

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY", "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")

# LangChain setup
chat_model = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=openai.api_key
)
conversation = ConversationChain(llm=chat_model)

# Price search function
def get_prices(product_name):
    search_params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(search_params)
    results = search.get_dict()

    prices = []
    sites = []

    for result in results.get("shopping_results", []):
        if "price" in result:
            price_str = result["price"].replace("$", "").replace(",", "")
            try:
                price = float(price_str)
                link = result.get("link", "")
                site = link.split("/")[2] if link else "unknown"
                prices.append(price)
                sites.append(site)
            except ValueError:
                continue

    return prices, sites

# Save price history
def save_to_csv(product_name, prices, sites):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "product_name": product_name,
        "timestamp": now,
        "prices": [",".join(map(str, prices))],
        "sites": [",".join(sites)],
    }
    df = pd.DataFrame(data)
    file_path = "price_history.csv"

    try:
        history_df = pd.read_csv(file_path)
        history_df = pd.concat([history_df, df], ignore_index=True)
    except FileNotFoundError:
        history_df = df

    history_df.to_csv(file_path, index=False)

# Plotting price trends
def plot_price_trends():
    try:
        df = pd.read_csv("price_history.csv")
        if df.empty:
            st.write("No price history available.")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['prices_list'] = df['prices'].apply(lambda x: [float(p) for p in x.split(",") if p.strip().replace('.', '', 1).isdigit()])
        df_exploded = df.explode('prices_list')
        df_exploded['prices_list'] = df_exploded['prices_list'].astype(float)

        fig, ax = plt.subplots(figsize=(10, 6))
        df_exploded.groupby('timestamp')['prices_list'].mean().plot(ax=ax)
        ax.set_title("Average Price Trends Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Average Price")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error in plotting price trends: {e}")

# Chatbot response
def get_chatbot_response(query):
    response = conversation.predict(input=query)
    return response

# Main UI
def main():
    st.title("AI-Driven Price Tracker")

    uploaded_file = st.file_uploader("Upload a CSV with product names", type="csv")

    if uploaded_file is not None:
        product_df = pd.read_csv(uploaded_file)
        if "product_name" in product_df.columns:
            for product in product_df["product_name"]:
                prices, sites = get_prices(product)
                if prices:
                    save_to_csv(product, prices, sites)
                    st.write(f"Product: {product}")
                    st.write("Prices:", prices)
                    st.write("Sites:", sites)
                    st.write("Lowest Price:", min(prices))
                    st.write("------------")
                else:
                    st.write(f"No prices found for {product}.")
        else:
            st.error("CSV must contain a column named 'product_name'")

    st.subheader("Ask about a product's prices:")
    user_input = st.text_input("Ask here...")

    if user_input:
        prices, sites = get_prices(user_input)
        if prices:
            st.write(f"Prices for {user_input}:", prices)
            st.write("Available on sites:", sites)
            st.write(f"Lowest Price: {min(prices)}")
        else:
            st.write("No prices found for this product.")

        chat_response = get_chatbot_response(user_input)
        st.write("Chatbot Response:", chat_response)

    st.subheader("Price Trends Over Time")
    plot_price_trends()

    st.subheader("Export Data")
    export_option = st.selectbox("Choose export format", ["CSV", "Excel", "PDF"])
    if st.button("Export Data"):
        try:
            df = pd.read_csv("price_history.csv")
            if export_option == "CSV":
                st.download_button("Download CSV", df.to_csv(index=False), file_name="price_history_export.csv")
            elif export_option == "Excel":
                df.to_excel("price_history_export.xlsx", index=False)
                st.download_button("Download Excel", data=open("price_history_export.xlsx", "rb").read(), file_name="price_history_export.xlsx")
            elif export_option == "PDF":
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Price History", ln=True, align='C')
                pdf.ln(10)
                for index, row in df.iterrows():
                    pdf.multi_cell(0, 10, txt=f"Product: {row['product_name']} | Date: {row['timestamp']} | Prices: {row['prices']} | Sites: {row['sites']}")
                pdf.output("price_history_export.pdf")
                st.download_button("Download PDF", data=open("price_history_export.pdf", "rb").read(), file_name="price_history_export.pdf")
        except Exception as e:
            st.error(f"Error exporting data: {e}")

if __name__ == "__main__":
    main()
