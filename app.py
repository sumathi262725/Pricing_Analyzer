import streamlit as st
import pandas as pd
import requests
from serpapi import GoogleSearch
from datetime import datetime
import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
import matplotlib.pyplot as plt
from fpdf import FPDF

# Configuration
st.set_page_config(page_title="Price Tracker", layout="wide")

# API Key (ensure you've set your API key in Streamlit secrets or the appropriate environment variable)
search = SerpAPIWrapper(serpapi_api_key="97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc")  # Your API key for SerpAPI

# OpenAI API Key (make sure this is set in your secrets or environment)
openai.api_key = st.secrets["openai_api_key"]

# LangChain setup for smarter chat
chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key="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")
conversation = ConversationChain(llm=chat_model)

# Define the function to scrape prices from different e-commerce sites using SerpAPI
def get_prices(product_name):
    search_params = {
        "q": product_name,
        "location": "United States",
        "api_key": serpapi_api_key,
        "engine": "google",
        "google_domain": "google.com",
    }

    search = GoogleSearch(search_params)
    results = search.get_dict()

    prices = []
    sites = []

    for result in results.get("organic_results", []):
        if "price" in result:
            price = result["price"]
            link = result["link"]
            site = link.split("/")[2]  # Extract site name from the link
            prices.append(price)
            sites.append(site)

    return prices, sites

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
    
    # User input for chat-style search
    st.subheader("Ask about a product's prices:")
    user_input = st.text_input("Ask here...")
    
    if user_input:
        prices, sites = get_prices(user_input)
        if prices:
            st.write(f"Prices for {user_input}:", prices)
            st.write(f"Available on sites:", sites)
            st.write(f"Lowest Price: {min(prices)}")
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
