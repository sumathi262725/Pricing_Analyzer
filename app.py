import streamlit as st
import pandas as pd
import json

st.title("🛍️ India Product Price Tracker")

# Load JSON data
try:
    with open("prices.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
except FileNotFoundError:
    st.error("prices.json not found. Please run the spider first.")
    st.stop()

# Clean and display
if df.empty:
    st.info("No data to display.")
else:
    df["price_num"] = df["price"].str.replace(r"[^\d]", "", regex=True).astype(float)
    result = []

    for product in df["product"].unique():
        sub = df[df["product"] == product]
        min_row = sub.loc[sub["price_num"].idxmin()]
        for i, row in sub.iterrows():
            result.append({
                "Product": product,
                "Region": "IN",
                "Site & Price": f"{row['site']} ({row['price']})",
                "Lowest Price & Site": f"{min_row['site']} ({min_row['price']})" if row.equals(min_row) else ""
            })

    final_df = pd.DataFrame(result)
    st.dataframe(final_df, use_container_width=True)
