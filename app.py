import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from serpapi import GoogleSearch

# --- CONFIG ---
st.set_page_config(page_title="🛒 Competitive Pricing Analyzer", layout="wide")

# --- SCRAPING FUNCTION ---
def search_serpapi(product_name, site):
    # Define your API key here (you can also use Streamlit secrets for security)
    api_key = st.secrets["serpapi"]["key"]
    
    params = {
        "q": product_name,
        "api_key": api_key,
        "engine": "google",
        "google_domain": "google.com",
    }
    
    if site == "amazon":
        params["tbm"] = "shop"
        params["tbs"] = "p_ord:pr"
    elif site == "walmart":
        params["tbm"] = "shop"
        params["tbs"] = "p_ord:pr"
    elif site == "target":
        params["tbm"] = "shop"
        params["tbs"] = "p_ord:pr"
    
    search = GoogleSearch(params)
    results = search.get_dict()

    if "shopping_results" in results:
        for result in results["shopping_results"]:
            if result.get("price"):
                return float(result["price"].replace('$', '').replace(',', ''))
    
    return None

# --- APP LOGIC ---
st.title("📊 Competitive Pricing Analyzer")

uploaded_file = st.file_uploader("Upload your product CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.info("Scraping competitor prices...")

    competitor_sites = ["amazon", "walmart", "target"]
    
    # Add columns for each competitor's price
    for site in competitor_sites:
        df[f"{site}_Price"] = df["Product_Name"].apply(lambda name: search_serpapi(name, site))
    
    # Analyzing the lowest price
    df['Lowest_Competitor_Price'] = df[["amazon_Price", "walmart_Price", "target_Price"]].min(axis=1)
    df['Lowest_Price_Site'] = df[["amazon_Price", "walmart_Price", "target_Price"]].idxmin(axis=1)
    
    # Add column for price comparison (whether it's the lowest, above, or middle)
    df['You_Are'] = df.apply(lambda row: "✅ Lowest" if row['Your_Price'] == row['Lowest_Competitor_Price']
                             else ("🔼 Above" if row['Your_Price'] > row['Lowest_Competitor_Price'] else "🟡 Middle"), axis=1)
    
    st.success("✅ Scraping complete.")
    st.dataframe(df)

    # Display the price comparison bar chart
    st.markdown("### 📉 Price Chart")
    st.bar_chart(df.set_index("Product_Name")[['Your_Price', 'amazon_Price', 'walmart_Price', 'target_Price']])

    # Download results button
    st.download_button("📥 Download Results", df.to_csv(index=False), file_name="price_results.csv")

# --- SECRET FILE SETUP ---
# Please make sure you have a secrets.toml file in the project with your SerpAPI key:
# [serpapi]
# key = "YOUR_SERPAPI_KEY"
