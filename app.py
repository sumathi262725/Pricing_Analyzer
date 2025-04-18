import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# CONFIG
st.set_page_config(page_title="AI Price Tracker", layout="wide")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")

# Fetch product prices using ZenRows + Google Shopping
def get_prices(product_name):
    url = "https://api.zenrows.com/v1/"
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": f"https://www.google.com/search?tbm=shop&q={product_name}",
        "js_render": "true"
    }

    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    prices, sites = [], []

    for item in soup.select("div.sh-dgr__content"):
        price_tag = item.select_one("span.T14wmb")
        site_tag = item.select_one("div.aULzUe.IuHnof")
        if price_tag and site_tag:
            try:
                price = float(price_tag.text.replace("$", "").replace(",", ""))
                prices.append(price)
                sites.append(site_tag.text.strip())
            except:
                continue

    return prices, sites

# Save prices to history
def save_to_csv(product_name, prices, sites):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "product_name": product_name,
        "timestamp": now,
        "prices": [', '.join(map(str, prices))],
        "sites": [', '.join(sites)],
        "lowest_price": [min(prices) if prices else None],
    }
    df = pd.DataFrame(data)
    file_path = "price_history.csv"
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_csv(file_path, index=False)

# Plot trends
def plot_price_trends():
    try:
        df = pd.read_csv("price_history.csv")
        if df.empty:
            st.info("No data to plot.")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['lowest_price'] = pd.to_numeric(df['lowest_price'], errors='coerce')

        fig, ax = plt.subplots(figsize=(10, 6))
        for product in df['product_name'].unique():
            product_df = df[df['product_name'] == product]
            ax.plot(product_df['timestamp'], product_df['lowest_price'], label=product)

        ax.set_title("Price Trends Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Lowest Price")
        ax.legend()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting trends: {e}")

# Export functionality
def export_data(export_option):
    df = pd.read_csv("price_history.csv")
    if export_option == "CSV":
        df.to_csv("export.csv", index=False)
        st.download_button("Download CSV", data=open("export.csv").read(), file_name="price_data.csv")
    elif export_option == "Excel":
        df.to_excel("export.xlsx", index=False)
        st.download_button("Download Excel", data=open("export.xlsx", "rb").read(), file_name="price_data.xlsx")
    elif export_option == "PDF":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Price History", ln=True, align='C')
        pdf.ln(10)
        for _, row in df.iterrows():
            txt = f"{row['timestamp']} | {row['product_name']} | {row['lowest_price']} | {row['sites']}"
            pdf.cell(200, 10, txt=txt, ln=True)
        pdf.output("export.pdf")
        st.download_button("Download PDF", data=open("export.pdf", "rb").read(), file_name="price_data.pdf")

# MAIN APP
def main():
    st.title("🛒 AI Price Tracker")

    uploaded_file = st.file_uploader("Upload CSV of product names", type="csv")
    results_df = pd.DataFrame()

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "product_name" not in df.columns:
            st.error("CSV must contain a 'product_name' column.")
            return

        for product in df["product_name"]:
            prices, sites = get_prices(product)
            if prices:
                save_to_csv(product, prices, sites)
                results_df = pd.concat([results_df, pd.DataFrame([{
                    "Product Name": product,
                    "Prices": ", ".join(f"${p:.2f}" for p in prices),
                    "Sites": ", ".join(sites),
                    "Lowest Price": f"${min(prices):.2f}"
                }])], ignore_index=True)
        st.subheader("📊 Comparison Table")
        st.dataframe(results_df)

    # Text input product price search
    st.subheader("🔍 Check a product's price:")
    user_input = st.text_input("Enter a product name")

    if user_input:
        prices, sites = get_prices(user_input)
        if prices:
            save_to_csv(user_input, prices, sites)
            row = {
                "Product Name": user_input,
                "Prices": ", ".join(f"${p:.2f}" for p in prices),
                "Sites": ", ".join(sites),
                "Lowest Price": f"${min(prices):.2f}"
            }
            st.dataframe(pd.DataFrame([row]))
        else:
            st.warning("No prices found.")

    # Trend
    st.subheader("📈 Price Trends")
    plot_price_trends()

    # Export
    st.subheader("📤 Export Options")
    export_option = st.selectbox("Choose format", ["CSV", "Excel", "PDF"])
    if st.button("Export"):
        export_data(export_option)

if __name__ == "__main__":
    main()
