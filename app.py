import streamlit as st
import pandas as pd
from serpapi import GoogleSearch

# Title of the app
st.title('Competitive Pricing Analyzer')

# Get the API key from Streamlit secrets
api_key = st.secrets["serpapi"]["api_key"]

# Input widget for product names (a single string or comma-separated list)
product_input = st.text_input("Enter product names (comma-separated)", "")

# Check if the user has entered product names
if product_input:
    # Split the input string into a list of product names
    product_names = [name.strip() for name in product_input.split(",")]

    # Initialize a list to store the pricing info for the table
    results_data = []

    # Loop through the product names entered by the user
    for product_query in product_names:
        st.subheader(f"Pricing for '{product_query}'")

        # Set up parameters for SerpAPI request
        params = {
            "q": product_query,  # Use the product name entered by the user
            "api_key": api_key,
        }

        try:
            # Perform the search using SerpAPI
            search = GoogleSearch(params)
            results = search.get_dict()

            # Initialize a dictionary to store prices from different websites
            prices = {}
            sites_used = []

            for result in results.get('organic_results', []):
                if 'price' in result and 'source' in result:
                    price = result['price']
                    site = result['source']
                    prices[site] = price
                    sites_used.append(site)

            if prices:
                # Get the lowest price
                lowest_site = min(prices, key=lambda x: float(prices[x].replace('$', '').replace(',', '')))
                lowest_price = prices[lowest_site]

                # Add the data to the results list for the table
                results_data.append({
                    "Product": product_query,
                    "Sites Used": ", ".join(sites_used),
                    "Prices": ", ".join([f"{site}: {price}" for site, price in prices.items()]),
                    "Lowest Price": f"${lowest_price} from {lowest_site}"
                })

            else:
                results_data.append({
                    "Product": product_query,
                    "Sites Used": "None",
                    "Prices": "None",
                    "Lowest Price": "No price found"
                })

        except Exception as e:
            results_data.append({
                "Product": product_query,
                "Sites Used": "Error",
                "Prices": "Error",
                "Lowest Price": str(e)
            })

    # Display the results in a table format
    results_df = pd.DataFrame(results_data)
    st.dataframe(results_df)

else:
    st.info("Please enter product names to proceed.")
