import telebot
import mysql.connector

# Telegram bot token
TOKEN = '5613753671:AAEb164Mq7QIKQR-uKuzFyai9-Fxyj4-HbI'
store_owner_id = 'Vaastav_p'

# MySQL database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Rsridevi1#'
DB_NAME = 'new_schema'

# Initialize the Telegram bot
bot = telebot.TeleBot(TOKEN)

# Connect to the MySQL database
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()

# Command handler for /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the General Store bot!")
    bot.reply_to(message, "Please enter your name:")
    bot.register_next_step_handler(message, get_name)

# Function to handle getting the customer's name
def get_name(message):
    name = message.text
    # Save the customer's name in a variable or database

    bot.reply_to(message, "Please enter your phone number:")
    bot.register_next_step_handler(message, get_phone_number)

# Function to handle getting the customer's phone number
def get_phone_number(message):
    phone_number = message.text
    # Save the customer's phone number in a variable or database

    bot.reply_to(message, "Thank you for providing your information.")
    bot.reply_to(message, "To place an order, use the /order command.")

# Command handler for /order
@bot.message_handler(commands=['order'])
def order(message):
    # Fetch inventory items from the database
    cursor.execute("SELECT * FROM inventory")
    inventory_items = cursor.fetchall()

    # Display inventory items to the user
    response = "Available items:\n"
    for item in inventory_items:
        response += f"ID: {item[0]}\nbrand: {item[5]}\nName: {item[1]}\nPrice: {item[2]}\nQuantity: {item[3]}\nremaining: {item[4]}\n\n"

    bot.reply_to(message, response)
    bot.reply_to(message, "Please enter the item ID and quantity (e.g., 1 2) for your order:")

# Handler for user's item selection
@bot.message_handler(func=lambda message: True)
def handle_order_item(message):
    if message.text.startswith('/'):
        confirm(message)
    try:
        # Extract the item ID and quantity from the user's message
        item_id, quantity = message.text.split()
        item_id = int(item_id)
        quantity = int(quantity)

        # Retrieve the item details from the database
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if item:
            item_name = item[5]+item[1]
            remaining_quantity = item[4]

            # Check if the selected quantity is available
            if quantity <= remaining_quantity:
                # Update the user's order dictionary with the selected item and quantity
                user_order[item_name] = quantity

                # Decrease the remaining quantity in the database
                updated_remaining_quantity = remaining_quantity - quantity
                cursor.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (updated_remaining_quantity, item_id))
                db.commit()

                bot.reply_to(message, f"Item '{item_name}' added to your order.")
            else:
                bot.reply_to(message, "Insufficient quantity available for the selected item.")
        else:
            bot.reply_to(message, "Invalid item ID.")

    except ValueError:
        bot.reply_to(message, "Invalid input format. Please enter the item ID")
# Command handler for /confirm
@bot.message_handler(commands=['confirm'])
def confirm(message):
    # Calculate total cost based on selected items
    total_cost = 0
    selected_items = []  # Declare and initialize the selected_items variable
    for item_name, quantity in user_order.items():
     cursor.execute("SELECT price FROM inventory WHERE name = %s", (item_name,))
     price = int(cursor.fetchone()[0])  # Convert the price to an integer
     item_cost = price * quantity
     total_cost += item_cost
     selected_items.append(f"{item_name} (Qty: {quantity})")
    # Send the total cost and selected items to the customer for confirmation
    response = f"Total Cost: {total_cost}\nSelected Items:\n"
    response += "\n".join(selected_items)
    response += "\n\nTo place the order, use the /place_order command."
    bot.reply_to(message, response)

    # Ask the store owner for approval
    bot.send_message(store_owner_id, f"New order received:\n{response}\nPlease approve or deny the order.")

# Command handler for /place_order
def place_order(message):
    # Generate a unique order ID
    order_id = generate_order_id()

    # Get the customer's name and phone number from the database
    cursor.execute("SELECT name, phone_number FROM customer")
    customer_info = cursor.fetchone()
    customer_name = customer_info[0]
    customer_phone_number = customer_info[1]

    # Calculate total cost based on selected items
    total_cost = 0
    selected_items = []  # Declare and initialize the selected_items variable
    for item_name, quantity in user_order.items():
        cursor.execute("SELECT price FROM inventory WHERE name = %s", (item_name,))
        price = cursor.fetchone()[0]
        item_cost = price * quantity
        total_cost += item_cost
        selected_items.append(f"{item_name} (Qty: {quantity})")

    # Update the customer's inventory with the order details
    for item_name, quantity in user_order.items():
        cursor.execute("INSERT INTO customer_inventory (order_id, name, phone_number, item_name, quantity) VALUES (%s, %s, %s, %s, %s)",
                       (order_id, customer_name, customer_phone_number, item_name, quantity))
        db.commit()

    # Send the order details to the store owner
    order_details = f"New Order Received!\nOrder ID: {order_id}\nCustomer Name: {customer_name}\nPhone Number: {customer_phone_number}\n"
    order_details += "Selected Items:\n" + "\n".join(selected_items)
    bot.send_message(store_owner_id, order_details)

    bot.reply_to(message, "Your order has been placed. We will get back to you soon.")
# Function to generate a unique order ID
def generate_order_id():
    # Implement your logic to generate a unique order ID
    return "ORDER123"  # Replace with your logic
user_order={}
# Connect to the Telegram API and start listening for messages
bot.polling()
