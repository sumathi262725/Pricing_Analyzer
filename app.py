
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="🛍️ Product Price Comparison", layout="wide")
st.title("📦 Competitive Price Search via SerpAPI")

# --- SerpAPI Helpers ---
def search_serpapi(product_name, site):
    api_key = st.secrets["serpapi"]["key"]
    engines = {
        "Amazon": "amazon",
        "Walmart": "walmart",
        "Google": "google_shopping"
    }
    
    params = {
        "api_key": api_key,
        "engine": engines[site],
        "type": "search",
        "search_term": product_name
    }

    if site == "Amazon":
        params["amazon_domain"] = "amazon.com"
    elif site == "Walmart":
        params["walmart_domain"] = "walmart.com"
    
    try:
        res = requests.get("https://serpapi.com/search", params=params)
        data = res.json()
        results = data.get("shopping_results") or data.get("organic_results", [])
        if results:
            price = results[0].get("price", "N/A")
            title = results[0].get("title", "")
            return price
        else:
            return "N/A"
    except:
        return "Error"

# --- File Upload ---
uploaded_file = st.file_uploader("Upload CSV with 'Product_Name' column", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if 'Product_Name' not in df.columns:
        st.error("CSV must contain a column named 'Product_Name'")
    else:
        st.info("Fetching prices, please wait...")
        for site in ["Amazon", "Walmart", "Google"]:
            df[f"{site}_Price"] = df["Product_Name"].apply(lambda name: search_serpapi(name, site))

        st.success("✅ Price search completed!")
        st.dataframe(df)

        st.download_button("📥 Download Results", df.to_csv(index=False), "price_results.csv")
