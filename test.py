import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection

# Function to initialize the database
def init_db(conn: Connection):
    conn.execute('''CREATE TABLE IF NOT EXISTS sales
                    (Date TEXT, Product TEXT, Quantity INTEGER, Amount REAL, Payment_Mode TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS inventory
                    (Product TEXT PRIMARY KEY, Quantity INTEGER)''')
    conn.commit()

# Function to load data from the database
def load_data(conn: Connection):
    sales_df = pd.read_sql('SELECT * FROM sales', conn)
    inventory_df = pd.read_sql('SELECT * FROM inventory', conn)
    return sales_df, inventory_df

# Function to record sales
def record_sales(date, products, quantities, amounts, payment_mode, conn: Connection):
    sales_df, inventory_df = load_data(conn)
    
    # Split products, quantities, and amounts by commas
    products_list = [p.strip() for p in products.split(',')]
    quantities_list = [int(q.strip()) for q in quantities.split(',')]
    amounts_list = [float(a.strip()) for a in amounts.split(',')]

    for product, quantity, amount in zip(products_list, quantities_list, amounts_list):
        if product and quantity and amount and payment_mode:
            # Check if product exists in inventory
            if product in inventory_df['Product'].values:
                # Add the sales data to the database
                conn.execute('INSERT INTO sales (Date, Product, Quantity, Amount, Payment_Mode) VALUES (?, ?, ?, ?, ?)',
                             (date, product, quantity, amount, payment_mode))
                # Subtract sold quantity from inventory
                conn.execute('UPDATE inventory SET Quantity = Quantity - ? WHERE Product = ?', (quantity, product))
            else:
                st.error(f"Product '{product}' not found in inventory.")
    conn.commit()

    # Load the updated data
    sales_df, inventory_df = load_data(conn)
    return sales_df, inventory_df

# Main Streamlit app
def main():
    st.title("Sales Recording App")

    # Initialize database connection
    conn = sqlite3.connect('sales_data.db')
    init_db(conn)

    # Input fields
    with st.form("record_sales_form"):
        sales_date = st.date_input("Date")
        products = st.text_input("Products (comma separated)")
        sales_quantity = st.text_input("Quantities (comma separated)")
        sales_amount = st.text_input("Amounts (comma separated)")
        payment_mode = st.selectbox("Payment Mode", ["Cash", "Credit Card", "Debit Card"])
        submit_button = st.form_submit_button("Record Sales")

    # Record sales if the form is submitted
    if submit_button:
        if sales_date and products and sales_quantity and sales_amount and payment_mode:
            sales_df, inventory_df = record_sales(sales_date, products, sales_quantity, sales_amount, payment_mode, conn)
            st.success("Sales recorded successfully!")
        else:
            st.error("Please fill all the fields.")

    # Display the sales and inventory data
    sales_df, inventory_df = load_data(conn)
    st.subheader("Sales Data")
    st.write(sales_df)

    st.subheader("Inventory Data")
    st.write(inventory_df)

    # Input fields for adding products to the inventory
    with st.form("add_inventory_form"):
        new_product = st.text_input("Product Name")
        new_quantity = st.number_input("Quantity", min_value=0, step=1)
        add_button = st.form_submit_button("Add to Inventory")

    # Add new product to the inventory if the form is submitted
    if add_button:
        if new_product and new_quantity:
            if new_product in inventory_df['Product'].values:
                conn.execute('UPDATE inventory SET Quantity = Quantity + ? WHERE Product = ?', (new_quantity, new_product))
            else:
                conn.execute('INSERT INTO inventory (Product, Quantity) VALUES (?, ?)', (new_product, new_quantity))
            conn.commit()
            st.success("Product added to inventory!")
        else:
            st.error("Please fill all the fields.")

    # Load the updated inventory data
    inventory_df = pd.read_sql('SELECT * FROM inventory', conn)
    st.subheader("Updated Inventory Data")
    st.write(inventory_df)

if __name__ == "__main__":
    main()
