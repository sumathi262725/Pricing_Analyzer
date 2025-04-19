import streamlit as st 
import pandas as pd
from serpapi import GoogleSearch
import os
import io
import matplotlib.pyplot as plt
from fpdf import FPDF

# Load your API key securely
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY") or "97b3eb326b26893076b6054759bd07126a3615ef525828bc4dcb7bf84265d3bc"

# Streamlit UI
st.title("🛍️ US Product Price Comparison")
st.write("Upload a list of product names (CSV or TXT) to compare prices from shopping sites in the United States 🇺🇸.")

uploaded_file = st.file_uploader("📄 Upload product list (CSV or TXT)", type=["csv", "txt"])

# Parse uploaded file
def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

# Search product prices using SerpAPI
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

# PDF Export helper
def generate_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    col_width = pdf.w / 4.5
    row_height = 8

    pdf.set_fill_color(220, 220, 220)
    for header in dataframe.columns:
        pdf.cell(col_width, row_height, header, border=1, ln=0, align='C', fill=True)
    pdf.ln(row_height)

    for i, row in dataframe.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    return pdf_output.getvalue()

# Main logic
if uploaded_file:
    products = parse_file(uploaded_file)
    results = []

    with st.spinner("🔎 Searching for US prices..."):
        for product in products:
            price_data = get_prices(product)
            if price_data:
                lowest_price = min(p[1] for p in price_data)
                for site, price in price_data:
                    results.append({
                        "Product": product,
                        "Site": site,
                        "Price (USD)": price,
                        "Lowest Price (USD)": lowest_price
                    })
            else:
                results.append({
                    "Product": product,
                    "Site": "No results found",
                    "Price (USD)": None,
                    "Lowest Price (USD)": None
                })

    df = pd.DataFrame(results)
    st.success("✅ US price comparison complete!")
    st.dataframe(df)

    # 📊 Price Chart
    st.subheader("📊 Price Chart (per Product)")
    for product in df["Product"].unique():
        product_data = df[df["Product"] == product].dropna(subset=["Price (USD)"])
        if not product_data.empty:
            fig, ax = plt.subplots()
            ax.barh(product_data["Site"], product_data["Price (USD)"], color="skyblue")
            ax.set_xlabel("Price (USD)")
            ax.set_title(f"{product} - Prices by Site")
            st.pyplot(fig)

    # 📥 Download options
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results (CSV)", data=csv, file_name="us_price_comparison.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
    st.download_button("📊 Download Results (Excel)", data=excel_buffer, file_name="us_price_comparison.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    pdf_data = generate_pdf(df)
    st.download_button("📝 Download Results (PDF)", data=pdf_data, file_name="us_price_comparison.pdf", mime="application/pdf")
