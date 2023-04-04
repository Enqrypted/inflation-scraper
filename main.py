# -*- coding: utf-8 -*-
import requests, re
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pandas as pd
import time
import matplotlib.pyplot as plt
from io import BytesIO
from flask import Flask, send_file

app = Flask(__name__)

def plot_prices(df):
    # Plot the data
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(ax=ax)

    # Customize the plot
    ax.set_title('Product Prices Over Time')
    ax.set_ylabel('Price')
    ax.set_xlabel('Date')

    # Save the plot to a buffer
    buffer = BytesIO()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    # Close the plot to avoid memory leaks
    plt.close()

    return buffer

def scrape_prices():
    json_file = 'price_data.json'
    excel_file = 'price_data.xlsx'

    products = {
        'Bread': 'https://www.theconvenienceshop.com/product/golden-harvest-new-brown-squares/',
        'Milk': 'https://www.theconvenienceshop.com/product/benna-milk-2-5-fat-1000ml/',
        'Eggs': 'https://www.theconvenienceshop.com/product/eggsx6/',
        'Bleach': 'https://www.theconvenienceshop.com/product/ace-wc-bleach-gel-700ml/',
        '7-UP': 'https://www.theconvenienceshop.com/product/7up-1-5l/'
    }

    # Read existing data or create an empty dictionary
    try:
        with open(json_file, 'r') as file:
            price_data = json.load(file)
    except FileNotFoundError:
        price_data = {}

    current_date = datetime.now().strftime('%d/%m/%Y')

    for product_type, url in products.items():
        # Fetch and parse the HTML content
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            price_element = soup.find('span', class_='woocommerce-Price-amount')

            if price_element:
                price = float(re.sub("€", "", price_element.get_text()))
                print(f'The price of {product_type} is: €{price}')

                # Create a list for the current date if it doesn't exist
                if current_date not in price_data:
                    price_data[current_date] = []

                # Create a new entry with the product type and price
                entry = {
                    'product': product_type,
                    'price': price
                }

                # Append the new entry to the list for the current date
                price_data[current_date].append(entry)

            else:
                print(f'Price element not found for {product_type}.')
        else:
            print(f'Error fetching the URL for {product_type}: {response.status_code}')

    # Save the updated data to the JSON file
    with open(json_file, 'w') as file:
        json.dump(price_data, file)

    # Convert JSON to DataFrame and save as Excel
    dfs = []
    for date, data in price_data.items():
        df = pd.DataFrame(data)
        df['date'] = date
        df.set_index(['date', 'product'], inplace=True)
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=False)
    pivot_df = merged_df.pivot_table(values='price', index='date', columns='product', aggfunc='first')
    pivot_df.to_excel(excel_file)

    # Plot the updated price data
    plot_prices(pivot_df)

# Set the number of days to run the script
num_days = 28
interval = 24*60*60  # Interval is 24 hours (in seconds)

# Run the script every day for the specified number of days

@app.route('/malta-inflation')
def serve_plot():

    # Read the Excel file into a pandas DataFrame
    excel_file = 'price_data.xlsx'
    df = pd.read_excel(excel_file)

    # Plot the data and save it to a buffer
    buffer = plot_prices(df)

    # Serve the buffer as a PNG image
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=8001)

start_time = time.time()
for _ in range(num_days):
    scrape_prices()
    time.sleep(interval - ((time.time() - start_time) % interval))


