import streamlit as st
import pandas as pd
import requests
from serpapi import GoogleSearchResults
from datetime import datetime
import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Configuration
st.set_page_config(page_title="Price Tracker", layout="wide")

# Set your API keys (make sure they're in Streamlit secrets or environment variables)
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # Ensure this is set in your environment
openai.api_key = st.secrets["openai_api_key"]

# LangChain setup for smarter chat
chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=openai.api_key)
conversation = ConversationChain(llm=chat_model)

# Define search function using SerpAPI to scrape product prices
def search_product_prices(product_name):
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": SERPAPI_KEY,
    }

    search = GoogleSearchResults(params)
    results = search.get_dict()

    prices = []
    if "shopping_results" in results:
        for item in results["shopping_results"]:
            prices.append({
                "title": item.get("title"),
                "price": item.get("price"),
                "source": item.get("source"),
                "link": item.get("link"),
            })
    return prices

# Function to save prices to a CSV file (for price history tracking)
def save_to_csv(product_name, prices, sites):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "product_name": product_name,
        "timestamp": now,
        "prices": prices,
        "sites": sites,
    }
    df = pd.DataFrame([data])
    file_path = "price_history.csv"

    try:
        history_df = pd.read_csv(file_path)
        history_df = pd.concat([history_df, df], ignore_index=True)
    except FileNotFoundError:
        history_df = df

    history_df.to_csv(file_path, index=False)

# Visualization function for price trend over time
def plot_price_trends():
    try:
        df = pd.read_csv("price_history.csv")
        if df.empty:
            st.write("No price history available.")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.groupby('timestamp')['prices'].apply(lambda x: x.str.split(',').explode().astype(float)).plot(ax=ax)
        ax.set_title("Price Trends Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error in plotting price trends: {e}")

# Chatbot for product-specific questions
def get_chatbot_response(query):
    response = conversation.predict(input=query)
    return response

# Main application UI
def main():
    st.title("AI-Driven Price Tracker")

    # Upload product list (optional, this will allow batch processing)
    uploaded_file = st.file_uploader("Upload a CSV with product names", type="csv")
    
    if uploaded_file is not None:
        product_df = pd.read_csv(uploaded_file)
        if "product_name" in product_df.columns:
            for product in product_df["product_name"]:
                df_prices = get_prices(product)
                if not df_prices.empty:
                    save_to_csv(product, df_prices["Price"].tolist(), df_prices["Site"].tolist())
                    st.write(f"Product: {product}")
                    st.write("Prices Table:")
                    st.dataframe(df_prices)
                    st.write("Lowest Price:", df_prices["Price"].min())
                    st.write("------------")
                else:
                    st.write(f"No prices found for {product}.")
        else:
            st.error("CSV must contain a column named 'product_name'")
    
    # User input for chat-style search
    st.subheader("Ask about a product's prices:")
    user_input = st.text_input("Ask here...")
    
    if user_input:
        df_prices = get_prices(user_input)
        if not df_prices.empty:
            st.subheader(f"Prices for '{user_input}'")
            st.dataframe(df_prices)

            st.write(f"Lowest Price: {df_prices['Price'].min()}")

            # Save for trend tracking
            save_to_csv(user_input, df_prices["Price"].tolist(), df_prices["Site"].tolist())
        else:
            st.write("No prices found for this product.")

        # Chatbot-style interaction
        chat_response = get_chatbot_response(user_input)
        st.write("Chatbot Response:", chat_response)

    # Price trend visualization
    st.subheader("Price Trends Over Time")
    plot_price_trends()

    # Export options
    st.subheader("Export Data")
    export_option = st.selectbox("Choose export format", ["CSV", "Excel", "PDF"])
    if st.button("Export Data"):
        try:
            df = pd.read_csv("price_history.csv")
            if export_option == "CSV":
                df.to_csv("price_history_export.csv", index=False)
                st.download_button("Download CSV", data=open("price_history_export.csv", "r").read(), file_name="price_history_export.csv")
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
                    pdf.cell(200, 10, txt=f"Product: {row['product_name']} | Date: {row['timestamp']} | Prices: {row['prices']} | Sites: {row['sites']}", ln=True)

                pdf.output("price_history_export.pdf")
                st.download_button("Download PDF", data=open("price_history_export.pdf", "rb").read(), file_name="price_history_export.pdf")
        except Exception as e:
            st.error(f"Error exporting data: {e}")

if __name__ == "__main__":
    main()
