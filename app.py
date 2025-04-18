import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Setup Chrome WebDriver
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

# Flipkart scraper
def scrape_flipkart(driver, product_name):
    driver.get(f"https://www.flipkart.com/search?q={product_name}")
    time.sleep(2)
    try:
        items = driver.find_elements(By.CLASS_NAME, "_1AtVbE")[:5]
        for item in items:
            try:
                name = item.find_element(By.CLASS_NAME, "_4rR01T").text
                price = item.find_element(By.CLASS_NAME, "_30jeq3").text
                return f"Flipkart({price})"
            except:
                continue
    except:
        pass
    return "Flipkart(Not Found)"

# Amazon India scraper
def scrape_amazon(driver, product_name):
    driver.get(f"https://www.amazon.in/s?k={product_name}")
    time.sleep(2)
    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".s-main-slot .s-result-item")[:5]
        for item in items:
            try:
                name = item.find_element(By.TAG_NAME, "h2").text
                price = item.find_element(By.CLASS_NAME, "a-price-whole").text
                currency = "₹"
                return f"Amazon India({currency}{price})"
            except:
                continue
    except:
        pass
    return "Amazon India(Not Found)"

# Croma scraper
def scrape_croma(driver, product_name):
    driver.get(f"https://www.croma.com/searchB?q={product_name}")
    time.sleep(2)
    try:
        items = driver.find_elements(By.CLASS_NAME, "product-item")[:5]
        for item in items:
            try:
                name = item.find_element(By.CLASS_NAME, "product-title").text
                price = item.find_element(By.CLASS_NAME, "new-price").text
                return f"Croma({price})"
            except:
                continue
    except:
        pass
    return "Croma(Not Found)"

# Reliance Digital scraper
def scrape_reliance_digital(driver, product_name):
    driver.get(f"https://www.reliancedigital.in/search?q={product_name}:relevance")
    time.sleep(2)
    try:
        items = driver.find_elements(By.CLASS_NAME, "sp__product")[:5]
        for item in items:
            try:
                price = item.find_element(By.CLASS_NAME, "TextWeb__Text-sc-1cyx778-0.giKaCJ.offer-price").text
                return f"Reliance Digital({price})"
            except:
                continue
    except:
        pass
    return "Reliance Digital(Not Found)"

# Tata CLiQ scraper
def scrape_tatacliq(driver, product_name):
    driver.get(f"https://www.tatacliq.com/search/?searchCategory=all&text={product_name}")
    time.sleep(2)
    try:
        items = driver.find_elements(By.CLASS_NAME, "ProductModule__Content-sc-1fg9z9i-2")[:5]
        for item in items:
            try:
                price = item.find_element(By.CLASS_NAME, "ProductDescription__PriceContainer-sc-1v7ly3i-6").text
                return f"Tata CLiQ({price})"
            except:
                continue
    except:
        pass
    return "Tata CLiQ(Not Found)"

# Streamlit UI
st.set_page_config(page_title="🇮🇳 India Price Comparison", layout="wide")
st.title("🇮🇳 India Product Price Comparison")

uploaded_file = st.file_uploader("📄 Upload product list (CSV or TXT)", type=["csv", "txt"])

def parse_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.iloc[:, 0].dropna().tolist()
    elif file.name.endswith(".txt"):
        content = file.read().decode("utf-8").splitlines()
        return [line.strip() for line in content if line.strip()]
    return []

if uploaded_file:
    product_list = parse_file(uploaded_file)

    if st.button("🔍 Search Prices"):
        driver = create_driver()
        results = []

        for product in product_list:
            prices = [
                scrape_flipkart(driver, product),
                scrape_amazon(driver, product),
                scrape_croma(driver, product),
                scrape_reliance_digital(driver, product),
                scrape_tatacliq(driver, product)
            ]

            numeric_prices = [(p, float(''.join(filter(str.isdigit, p)))) for p in prices if any(c.isdigit() for c in p)]
            lowest = min(numeric_prices, key=lambda x: x[1])[0] if numeric_prices else "N/A"

            for p in prices:
                results.append({
                    "Product": product,
                    "Region": "IN",
                    "Site & Price": p,
                    "Lowest Price & Site": lowest if p == lowest else ""
                })

        driver.quit()

        df = pd.DataFrame(results)
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button("\ud83d\udcc5 Download CSV", data=csv, file_name="india_price_comparison.csv", mime="text/csv")
