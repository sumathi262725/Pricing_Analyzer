import streamlit as st
from serpapi import GoogleSearch

# Title of the app
st.title('Competitive Pricing Analyzer')

# Get the API key from Streamlit secrets
api_key = st.secrets["serpapi"]["api_key"]

# Input for product search query
product_query = st.text_input("Enter product name for price analysis:")

# Check if the user entered a query
if product_query:
    # Set up parameters for SerpAPI request
    params = {
        "q": product_query,  # Use the input product name
        "api_key": api_key,
    }

    try:
        # Perform the search using SerpAPI
        search = GoogleSearch(params)
        results = search.get_dict()

        # Display the raw results for debugging
        # st.write(results)

        # Extract price information and display
        st.subheader(f"Pricing for '{product_query}'")
        for result in results.get('organic_results', []):
            if 'price' in result:
                st.write(f"Website: {result.get('source', 'Unknown')} - Price: {result['price']}")
            else:
                st.write(f"Website: {result.get('source', 'Unknown')} - Price not available")

    except Exception as e:
        st.error(f"Error occurred while fetching data: {e}")

