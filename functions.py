import sqlite3
from socket import *
import json


online_users = {}

def client_handler(client_socket):
    username = None
    print("in client handler")
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
                if response["content"] == "Login successful":
                    username = data["username"]
                    online_users[username] = client_socket 
                    #pending_msgs = get_pending_messages(username)
                    #if len(pending_msgs)!=0:
                        #response += "\n\nYou have pending messages:\n" + "\n".join(pending_msgs)
            elif data["command"] == "rate":
                response = rate_product(data)
            elif data["command"] == "add_to_cart":
                response = add_to_cart(data)
                print("response recorded")
            elif data["command"] == "view_cart":
                response = view_cart(data)
            elif data["command"] == "remove_from_cart":
                response = remove_from_cart(data)
            elif data["command"] == "checkout":
                response = checkout(data)
            elif data["command"] == "add_product":
                response = add_product(data)
            #elif data["command"] == "view_buyers":
                #response = view_buyers(username)
            elif data["command"] == "view_products":
                response = fetch_products()
            elif data["command"] == "view_products_by_owner":
                response = view_products_by_owner(data)
            elif data["command"] == "fetch_users":
                response = fetch_users(username) 
            elif data["command"] == "check_online_status":
                response = check_online_status(data) 
            elif data["command"] == "fetch_chats_between_users":
                response = fetch_chats_between_users(username,data["other"]) 
            elif data["command"] == "store_message":
                response = store_message(data)
            elif data["command"] == "quit":
                online_users[username]=None
                break
            else:
                response= {"error": True, "message": "Unknown command"}

            # Send the response back to the client
            print("about to send the add_to_cart response")
            client_socket.send(json.dumps(response).encode('utf-8'))
            print("sent")
 
        except ConnectionResetError:
            print("Client disconnected")
            online_users[username]=None
            break

    client_socket.close()


def view_products_by_owner(data):
    """Fetch all products owned by the logged-in user."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        # Query to fetch relevant columns including owner_username
        cursor.execute("""
            SELECT product_id, name, description, price, quantity, owner_username
            FROM products
            WHERE owner_username = ?
        """, (data["username"],))
        products = cursor.fetchall()
        conn.close()

        return {"type": 0, "error": False, "content": products}
    except Exception as e:
        return {"type": 0, "error": True, "content": f"Failed to fetch products: {str(e)}"}


def add_product(data):
    """Add a new product to the database."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        # Insert product details into the database
        cursor.execute("""
            INSERT INTO products (name, description, price, quantity, owner_username)
            VALUES (?, ?, ?, ?, ?)
        """, (data["name"], data["description"], data["price"], data["quantity"], data["owner"]))

        conn.commit()
        conn.close()

        return {"type": 0, "error": False, "content": "Product added successfully."}
    except Exception as e:
        return {"type": 0, "error": True, "content": f"Failed to add product: {str(e)}"}


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

    user_username = data["username"]
    product_id = data["product_id"]
    rating = data["rating"]

    # Insert or update the user's rating for the product
    cursor.execute("""
        INSERT INTO ratings (user_username, product_id, rating)
        VALUES (?, ?, ?)
        ON CONFLICT(user_username, product_id)
        DO UPDATE SET rating = excluded.rating
    """, (user_username, product_id, rating))

    # Recalculate the average rating for the product
    cursor.execute("""
        UPDATE products
        SET average_rating = (
            SELECT AVG(rating)
            FROM ratings
            WHERE product_id = ?
        ),
        review_count = (
            SELECT COUNT(*)
            FROM ratings
            WHERE product_id = ?
        )
        WHERE product_id = ?
    """, (product_id, product_id, product_id))

    # Fetch the updated average rating
    cursor.execute("SELECT average_rating FROM products WHERE product_id = ?", (product_id,))
    new_average_rating = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return {"type": 0, "error": False, "content": float(new_average_rating)}


def add_to_cart(data):
    """Adds a product to the user's cart, validating cumulative quantity."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        username = data["username"]
        product_id = str(data["product_id"])
        requested_quantity = data["quantity"]

        # Check the product's available quantity
        cursor.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            return {"type": 0, "error": True, "content": "Product not found."}
        
        available_quantity = result[0]

        # Fetch the user's cart
        cursor.execute("SELECT cart_list FROM carts WHERE username = ?", (username,))
        result = cursor.fetchone()
        cart_dict = json.loads(result[0]) if result and result[0] else {}

        # Check the cumulative quantity (current + requested)
        current_cart_quantity = cart_dict.get(product_id, 0)
        if current_cart_quantity + requested_quantity > available_quantity:
            return {"type": 0, "error": True, "content": f"Quantity exceeded. Only {available_quantity - current_cart_quantity} more can be added."}

        # Update the cart
        if product_id in cart_dict:
            cart_dict[product_id] += requested_quantity
        else:
            cart_dict[product_id] = requested_quantity

        # Serialize and save the updated cart
        cart_list = json.dumps(cart_dict)
        cursor.execute(
            "INSERT OR REPLACE INTO carts (username, cart_list) VALUES (?, ?)",
            (username, cart_list),
        )

        conn.commit()
        return {"type": 0, "error": False, "content": "Product added to cart."}
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return {"type": 0, "error": True, "content": f"Database error: {str(e)}"}
    finally:
        conn.close()

def view_cart(data):
    """Fetches the user's cart and returns the cart items."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()
        print("we are in view_cart")
        username = data["username"]
        print(f"Fetching cart for username: {username}")

        # Fetch the user's cart
        cursor.execute("SELECT cart_list FROM carts WHERE username = ?", (username,))
        result = cursor.fetchone()
        print(f"Fetched cart data: {result}")

        if result and result[0]:
            print("Cart data found, loading it into a dictionary")
            cart_dict = json.loads(result[0])  # Load the cart as a dictionary
        else:
            print("No cart data found, initializing empty cart")
            cart_dict = {}  # Empty cart if no data found

        print("Fetching product details for each cart item...")
        cart_items = []
        for product_id, quantity in cart_dict.items():
            print(f"Fetching product details for product_id: {product_id}")
            cursor.execute("SELECT name, price FROM products WHERE product_id = ?", (product_id,))
            product_result = cursor.fetchone()
            if product_result:
                name, price = product_result
                print(f"Fetched product: {name}, price: {price}, quantity: {quantity}")
                cart_items.append({
                    "product_id": int(product_id),
                    "name": name,
                    "price": price,
                    "quantity": quantity
                })
            else:
                print(f"Product with product_id {product_id} not found in database.")

        print("Successfully fetched products")
        conn.close()
        return {"type": 0, "error": False, "content": cart_items}

    except sqlite3.Error as e:
        print(f"Error occurred while fetching cart: {e}")
        return {"type": 0, "error": True, "content": "Failed to fetch cart items: " + str(e)}

def remove_from_cart(data):
    """Removes a product from the user's cart."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        username = data["username"]
        product_id = str(data["product_id"])  # Ensure the product ID is treated as a string

        # Fetch the user's cart
        cursor.execute("SELECT cart_list FROM carts WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and result[0]:
            cart_dict = json.loads(result[0])
        else:
            return {"type": 0, "error": True, "content": "Cart is empty or not found."}

        # Remove or decrement the product from the cart
        if product_id in cart_dict:
            if cart_dict[product_id] > 1:
                cart_dict[product_id] -= 1  # Decrement quantity
            else:
                del cart_dict[product_id]  # Remove product if quantity is 1
        else:
            return {"type": 0, "error": True, "content": "Product not found in cart."}

        # Save updated cart back to the database
        updated_cart = json.dumps(cart_dict)
        cursor.execute(
            "INSERT OR REPLACE INTO carts (username, cart_list) VALUES (?, ?)",
            (username, updated_cart)
        )
        conn.commit()
        conn.close()

        return {"type": 0, "error": False, "content": "Product removed from cart successfully."}

    except sqlite3.Error as e:
        return {"type": 0, "error": True, "content": "Failed to remove product from cart: " + str(e)}

def checkout(data):
    """Completes the checkout process by updating product quantities and clearing the cart."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        username = data["username"]

        # Fetch the user's cart
        cursor.execute("SELECT cart_list FROM carts WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and result[0]:
            cart_dict = json.loads(result[0])
        else:
            return {"type": 0, "error": True, "content": "Cart is empty or not found."}

        # Update product quantities
        for product_id, quantity in cart_dict.items():
            cursor.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
            product_result = cursor.fetchone()

            if product_result:
                available_quantity = product_result[0]
                if available_quantity >= quantity:
                    new_quantity = available_quantity - quantity
                    cursor.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
                    if new_quantity == 0:
                        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
                else:
                    return {"type": 0, "error": True, "content": f"Insufficient stock for product ID {product_id}"}

        # Clear the user's cart
        cursor.execute("INSERT OR REPLACE INTO carts (username, cart_list) VALUES (?, ?)", (username, json.dumps({})))

        conn.commit()
        return {"type": 0, "error": False, "content": "Checkout successful. Cart is now empty."}
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return {"type": 0, "error": True, "content": "Failed to complete checkout: " + str(e)}
    finally:
        conn.close()

    
def fetch_users(username):
    """
    Fetch all users
    """
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    # Query to fetch all users except the current user
    query = """
    SELECT username
    FROM users
    WHERE username != ?
    ORDER BY username ASC;
    """
    cursor.execute(query, (username,))
    results = cursor.fetchall()

    conn.close()

    # Prepare the response
    response = []
    for row in results:
        chat_partner = row[0]
        response.append({
            "owner": chat_partner,
        })

    return {"type": 0, "error": False, "content": response}


def check_online_status(data):
    """
    Check if a specific user is online and return their IP and port.
    """
    username = data["username"]
    if username in online_users:
        ip_address, port = online_users[username].getpeername()  # Retrieve IP and port
        return {"type": 0, "error": False, "content": {"is_online": True, "ip_address": ip_address, "port": port}}
    else:
        return {"type": 0, "error": False, "content": {"is_online": False}}


def store_message(data):
    """
    Store a message in the database. Mark as unsent if the recipient is offline.
    """
    sender = data["sender"]
    receiver = data["receiver"]
    message = data["message"]
    sent = data["sent"]
    timestamp = data["time"]

    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        # Insert message into the messages table
        query = """
        INSERT INTO messages (sender, receiver, message, sent, time)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (sender, receiver, message, sent, timestamp))
        conn.commit()
        conn.close()

        return {"type": 0, "error": False, "content": "Message stored successfully."}
    except Exception as e:
        return {"type": 0, "error": True, "content": f"Failed to store message: {str(e)}"}


def fetch_chats_between_users(user1, user2):
    """
    Fetch the chat history between two users.
    """
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()
    
    # Query to fetch messages exchanged between two users
    query = """
    SELECT sender, receiver, message, sent, time
    FROM messages
    WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
    ORDER BY time ASC;
    """
    cursor.execute(query, (user1, user2, user2, user1))
    results = cursor.fetchall()
    
    # Prepare the response
    response = []
    for row in results:
        sender, receiver, message, sent, time = row
        response.append({
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "sent": bool(sent),
            "time": time
        })
    
    return {"type":0,"error": False, "content": response}




