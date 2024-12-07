import sqlite3
from socket import *
import json


online_users = {}

def client_handler(client_socket):
    username = None
    while True:
        try:
            # Receive and decode the client's message
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            # Parse the message (JSON formatted)
            data = json.loads(message)

            # Dispatch the correct action based on the command
            if data["command"] == "register":
                response = register_user(data)
                if response=="Registration successful":
                    username = data["username"]
                    online_users[username] = None
            elif data["command"] == "login":
                response = login_user(data)
                if response == "Login successful":
                    username = data["username"]
                    online_users[username] = client_socket 
                    #pending_msgs = get_pending_messages(username)
                    #if len(pending_msgs)!=0:
                        #response += "\n\nYou have pending messages:\n" + "\n".join(pending_msgs)
            elif data["command"] == "rate":
                response = rate_product(data)
            elif data["command"] == "add_to_cart":
                response = add_to_cart(data)
            elif data["command"] == "view_cart":
                response = view_cart(data)
            elif data["command"] == "remove_from_cart":
                response = remove_from_cart(data)
            elif data["command"] == "checkout":
                response = checkout(data)
            #elif data["command"] == "add_product":
                #response = add_product(data)
            #elif data["command"] == "view_buyers":
                #response = view_buyers(username)
            elif data["command"] == "view_products":
                response = fetch_products()
            #elif data["command"] == "view_products_by_owner":
                #response = view_products_by_owner(data)
            #elif data["command"] == "check_online_status":
                #response = check_online_status(data)
            #elif data["command"] == "send_message":
                #response = send_message(username, data["owner"], data["message"])
            elif data["command"] == "quit":
                online_users[username]=None
                break

            # Send the response back to the client
            client_socket.send(json.dumps(response).encode('utf-8'))

        except ConnectionResetError:
            print("Client disconnected")
            online_users[username]=None
            break

    client_socket.close()


# Server functionalities
def register_user(data):
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, email, name)
            VALUES (?, ?, ?, ?)
        """, (data["username"], data["password"], data["email"], data["name"]))
        conn.commit()
        conn.close()
        return {"type":0,"error": False, "content": "User registered successfully. Please login."}
    except sqlite3.IntegrityError:
        return {"type":0,"error": True, "content": "Username already exists."}

def login_user(data):
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE username = ? AND password = ?
    """, (data["username"], data["password"]))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"type":0,"error": False, "content": "Login successful"}
    else:
        return {"type":0,"error": True, "content": "Invalid username or password"}
    
def fetch_products():
    """Fetch products from the SQLite database."""
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, name, description, price, owner_username, average_rating, quantity
        FROM products
        WHERE buyer_username IS NULL
    """)
    products = cursor.fetchall()
    conn.close()
    return {"type":0, "error":False, "content":products}

def rate_product(data):
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET average_rating = (average_rating * review_count + ?) / (review_count + 1),
            review_count = review_count + 1
        WHERE product_id = ?
    """, (data["rating"], data["product_id"]))
    conn.commit()

    cursor.execute("SELECT average_rating FROM products WHERE product_id = ?", (data["product_id"],))
    rating = cursor.fetchone()[0]
    conn.close()
    return {"type":0,"error":False,"content":float(rating)}

def add_to_cart(data):
    username = data.get('username')
    product_id = data.get('product_id')

    # Connect to the database
    conn = sqlite3.connect('auboutique.db')
    cursor = conn.cursor()

    # Check if the product already exists in the user's cart
    cursor.execute("""
        SELECT * FROM carts WHERE username = ? AND product_id = ?
    """, (username, product_id))
    result = cursor.fetchone()

    if result:
        # Product is already in the cart, increment the quantity
        cursor.execute("""
            UPDATE carts SET quantity = quantity + 1 WHERE username = ? AND product_id = ?
        """, (username, product_id))
        response = {"type":0, "error": False, "content": "Product quantity updated in cart."}
    else:
        # Add the product to the cart with initial quantity 1
        cursor.execute("""
            INSERT INTO carts (username, product_id, quantity) VALUES (?, ?, ?)
        """, (username, product_id, 1))
        response = {"type":0, "error": False, "content": "Product added to cart."}

    # Commit changes and close connection
    conn.commit()
    conn.close()

    return response

def view_cart(data):
    username = data["username"]
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.product_id, p.name, p.price, c.quantity
        FROM products p
        JOIN carts c ON p.product_id = c.product_id
        WHERE c.username = ?
    """, (username,))
    cart_items = cursor.fetchall()
    conn.close()

    # Format the result as a list of dictionaries
    cart = [{"product_id": item[0], "name": item[1], "price": item[2], "quantity": item[3]} for item in cart_items]

    return {"type": 0, "error": False, "content": cart}

def remove_from_cart(data):
    username = data["username"]
    product_id = data["product_id"]
    
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM carts
        WHERE username = ? AND product_id = ?
    """, (username, product_id))

    conn.commit()
    conn.close()

    return {"type": 0, "error": False, "content": "Product removed from cart"}

def checkout(data):
    username = data["username"]
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    # Process checkout (e.g., reduce product quantity, create order record, etc.)
    cursor.execute("""
        SELECT product_id, quantity FROM carts WHERE username = ?
    """, (username,))
    cart_items = cursor.fetchall()

    for item in cart_items:
        product_id, quantity = item
        cursor.execute("""
            UPDATE products SET quantity = quantity - ? WHERE product_id = ?
        """, (quantity, product_id))

    # Optionally, create an order record, then delete items from the cart
    cursor.execute("""
        DELETE FROM carts WHERE username = ?
    """, (username,))

    conn.commit()
    conn.close()

    return {"type": 0, "error": False, "content": "Checkout successful"}
