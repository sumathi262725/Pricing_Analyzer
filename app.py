import streamlit as st
import pandas as pd
import requests
from serpapi import GoogleSearch

# Function to get price data from SerpAPI
def get_price_from_serpapi(product_name):
    api_key = st.secrets["serpapi_api_key"]  # Using Streamlit's secrets management for API key
    search_params = {
        "q": product_name,
        "api_key": api_key,
    }
    
    try:
        # Use SerpAPI to search for product prices across different websites
        search = GoogleSearch(search_params)
        results = search.get_dict()

        if 'organic_results' not in results:
            return None

        product_prices = []
        for result in results['organic_results']:
            if 'price' in result and 'source' in result:
                product_prices.append({
                    'site': result['source'],
                    'price': result['price']
                })

        return product_prices

    except Exception as e:
        st.error(f"Error occurred while fetching prices for {product_name}: {e}")
        return None

# Streamlit UI
st.title("Product Price Scraper")
st.write("Upload a CSV file with a list of product names to get their prices from various websites.")

# File upload for product names CSV
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    # Read the uploaded CSV file
    df = pd.read_csv(uploaded_file)

    # Ensure the CSV has a column for product names
    if "Product" not in df.columns:
        st.error('CSV file must have a column named "Product" with product names.')
    else:
        product_names = df['Product'].tolist()
        price_data = []

        # Fetch prices for each product
        for product in product_names:
            st.write(f"Fetching prices for: {product}")
            product_prices = get_price_from_serpapi(product)
            
            if product_prices:
                for price_info in product_prices:
                    price_data.append({
                        "Product": product,
                        "Site": price_info['site'],
                        "Price": price_info['price'],
                    })
            else:
                st.write(f"No prices found for {product}")
        
        if price_data:
            # Create DataFrame for display
            price_df = pd.DataFrame(price_data)

            # Find the lowest price for each product
            price_df['Price'] = price_df['Price'].replace({'\$': '', ',': ''}, regex=True).astype(float)
            price_df['Lowest Price'] = price_df.groupby('Product')['Price'].transform('min')

            # Display results in table format
            st.write("Prices scraped from various websites:", price_df)

            # Optionally, save to a CSV
            st.download_button("Download prices as CSV", price_df.to_csv(index=False), "prices.csv")
        else:
            st.write("No prices found for the given products.")
