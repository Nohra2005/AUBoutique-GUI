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
                reponse = rate_product(data)
            #elif data["command"] == "add_product":
                #response = add_product(data)
            #elif data["command"] == "view_buyers":
                #response = view_buyers(username)
            elif data["command"] == "view_products":
                response = fetch_products()
            #elif data["command"] == "view_products_by_owner":
                #response = view_products_by_owner(data)
            #elif data["command"] == "add_to_cart":
                #response = buy_product(username,data)
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
