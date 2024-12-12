import sqlite3
from socket import *
import json
from datetime import *

online_users = {}

def client_handler(client_socket):
    username = None
    
    while True:
        try:
            # Receive and decode the client's message
            message = client_socket.recv(4096).decode('utf-8')
            br=False
            if not message:
                break

            # Parse the message (JSON formatted)
            data = json.loads(message)

            # Dispatch the correct action based on the command
            if data["command"] == "register":
                response = register_user(data)
                if response=="Registration successful":
                    username = data["username"]
            elif data["command"] == "login":
                response = login_user(data)
                if response["content"] == "Login successful":
                    username = data["username"]
                    online_users[username] = {"p2p_address":data["p2p_address"],"client_socket":client_socket}
            elif data["command"] == "rate":
                response = rate_product(data)
            elif data["command"] == "add_to_cart":
                response = add_to_cart(data)
            elif data["command"] == "view_cart":
                response = view_cart(data)
            elif data["command"] == "remove_from_cart":
                response = remove_from_cart(data)
            elif data["command"] == "view_product_buyers":
                response = view_product_buyers(data)
            elif data["command"] == "checkout":
                response = checkout(data)
            elif data["command"] == "add_product":
                response = add_product(data)
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
            elif data["command"] == "toggle_follow":
                response = toggle_follow(data)
            elif data["command"] == "modify_product":
                response = modify_product(username,data)
            elif data["command"] == "log_out":
                if username in online_users:
                    del online_users[username]
                response= {"type":0,"error": False, "content": "Log out sucessful."}
            elif data["command"] == "quit":
                if username in online_users:
                    del online_users[username]
                print("Client disconnected")
                br=True
                response= {"type":0,"error": False, "content": "Quit sucessful."}
            else:
                response= {"type":0,"error": True, "content": "Unknown command"}

            # Send the response back to the client
            print(response,data)
            client_socket.send(json.dumps(response).encode('utf-8'))
            if br: break
 
        except ConnectionResetError:
            print("Client disconnected")
            if username in online_users:
                del online_users[username]
            break

    client_socket.close()


def modify_product(username,data):
    """Modify an existing product in the database."""
    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE products
            SET name = ?, description = ?, price = ?, quantity = ?
            WHERE product_id = ?
        """, (data["name"], data["description"], data["price"], data["quantity"], data["product_id"]))

        # Notify followers
        notify_followers(username, data["name"], "modified")
        
        conn.commit()
        conn.close()

        return {"type": 0, "error": False, "content": "Product modified successfully."}
    except sqlite3.Error as e:
        return {"type": 0, "error": True, "content": f"Database error: {str(e)}"}
    except Exception as e:
        return {"type": 0, "error": True, "content": f"Unexpected error: {str(e)}"}


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

def view_product_buyers(data):
    """Retrieve all buyers for a specific product along with their name and email."""
    product_id = data.get("product_id")

    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        # Fetch all buyers for the product
        query = "SELECT buyer_username FROM product_buyers WHERE product_id = ?"
        cursor.execute(query, (product_id,))
        buyer_usernames = [row[0] for row in cursor.fetchall()]

        # Fetch the name and email for each buyer
        buyers = []
        for username in buyer_usernames:
            query = "SELECT name, email FROM users WHERE username = ?"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            if result:
                name, email = result
                buyers.append({"username": username, "name": name, "email": email})
            else:
                # Handle case where user info is not found
                buyers.append({"username": username, "name": "Unknown", "email": "Unknown"})

        conn.close()
        return {"type": 0, "error": False, "content": buyers}
    except Exception as e:
        # Debug: Log exception
        return {"type": 0, "error": True, "message": str(e)}


def add_product(data):
    """Add a new product to the database."""
    try:
        conn = sqlite3.connect("auboutique.db", check_same_thread=False)
        cursor = conn.cursor()

        # Validate input data
        product_name = data.get("name")
        owner = data.get("owner")
        if not product_name or not owner:
            raise ValueError("Missing 'name' or 'owner' in the data payload.")

        # Insert product details into the database
        cursor.execute("""
            INSERT INTO products (name, description, price, quantity, owner_username)
            VALUES (?, ?, ?, ?, ?)
        """, (product_name, data["description"], data["price"], data["quantity"], owner))


        conn.commit()
        conn.close()
        
        # Notify followers in real-time if they are online
        notify_followers(owner, product_name, "added")

        
        return {"type": 0, "error": False, "content": "Product added successfully."}
    except sqlite3.Error as db_error:
        if conn:
            conn.rollback()
        return {"type": 0, "error": True, "content": f"Database error: {str(db_error)}"}
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
        return {"type":0, "error": False, "content": "User registered successfully. Please login."}
    except sqlite3.IntegrityError:
        return {"type":0, "error": True, "content": "Username already exists."}

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
    """Fetch products from the SQLite database with non-zero quantity."""
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, name, description, price, owner_username, average_rating, quantity 
        FROM products
        WHERE quantity > 0
    """)
    products = cursor.fetchall()
    conn.close()
    return {"type": 0, "error": False, "content": products}

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
        username = data["username"]

        # Fetch the user's cart
        cursor.execute("SELECT cart_list FROM carts WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and result[0]:
            cart_dict = json.loads(result[0])  # Load the cart as a dictionary
        else:
            cart_dict = {}  # Empty cart if no data found

        cart_items = []
        for product_id, quantity in cart_dict.items():
            cursor.execute("SELECT name, price FROM products WHERE product_id = ?", (product_id,))
            product_result = cursor.fetchone()
            if product_result:
                name, price = product_result
                cart_items.append({
                    "product_id": int(product_id),
                    "name": name,
                    "price": price,
                    "quantity": quantity
                })
          
        conn.close()
        return {"type": 0, "error": False, "content": cart_items}

    except sqlite3.Error as e:
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
                    cursor.execute("INSERT INTO product_buyers (product_id, buyer_username) VALUES (?, ?)",(product_id, username),
        )
                else:
                    return {"type": 0, "error": True, "content": f"Insufficient stock for product ID {product_id}"}

        # Clear the user's cart
        cursor.execute("INSERT OR REPLACE INTO carts (username, cart_list) VALUES (?, ?)", (username, json.dumps({})))

        conn.commit()
        pickup_date = datetime.now() + timedelta(days=2)
        return {"type": 0, "error": False, "content": f"Product purchased successfully.\nPick up your item on {pickup_date.date()} any time after 8:00 AM from AUB Post Office."}
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        return {"type": 0, "error": True, "content": "Failed to complete checkout: " + str(e)}
    finally:
        conn.close()

def fetch_users(username):
    """
    Fetch all users with an indication if they are followed by the given user.
    """
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    # Query to fetch all users except the current user
    query = """
    SELECT u.username, 
           CASE 
               WHEN so.owner IS NOT NULL THEN 1
               ELSE 0
           END AS is_followed
    FROM users u
    LEFT JOIN subscribed_owners so 
    ON u.username = so.owner AND so.user = ?
    WHERE u.username != ?
    ORDER BY u.username ASC;
    """
    cursor.execute(query, (username, username))
    results = cursor.fetchall()

    conn.close()

    # Prepare the response
    response = []
    for row in results:
        chat_partner = row[0]
        is_followed = bool(row[1])  # Convert 1/0 to True/False
        response.append({
            "owner": chat_partner,
            "is_followed": is_followed
        })

    return {"type": 0, "error": False, "content": response}



def check_online_status(data):
    """
    Check if a specific user is online and return their IP and port.
    """
    username = data["username"]
    if username in online_users:
        ip_address, port = online_users[username]["p2p_address"]  # Retrieve IP and port of peer to peer connection
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
    timestamp = data["time"]

    try:
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()

        # Insert message into the messages table
        query = """
        INSERT INTO messages (sender, receiver, message, time)
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (sender, receiver, message, timestamp))
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
    SELECT sender, receiver, message, time
    FROM messages
    WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
    ORDER BY time ASC;
    """
    cursor.execute(query, (user1, user2, user2, user1))
    results = cursor.fetchall()
    
    # Prepare the response
    response = []
    for row in results:
        sender, receiver, message, time = row
        response.append({
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "time": time
        })
    
    return {"type":0,"error": False, "content": response}

def toggle_follow(data):
    """Handle follow/unfollow commands."""
    username = data.get("username")
    owner = data.get("owner")
    action = data.get("action")

    if not username or not owner or action not in ["follow", "unfollow"]:
        
        return {"type": 0, "error": True, "message": "Invalid request parameters."}

    try:
        # Connect to the database
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()
        
        # Perform the database operation
        if action == "follow":
            cursor.execute("INSERT INTO subscribed_owners (user, owner) VALUES (?, ?)", (username, owner))
        elif action == "unfollow":
            cursor.execute("DELETE FROM subscribed_owners WHERE user = ? AND owner = ?", (username, owner))

        # Commit changes
        conn.commit()

        # Close the connection
        conn.close()

        # Return success
        return {"type": 0, "error": False, "message": f"Successfully {action}ed {owner}."}

    except Exception as e:
        return {"type": 0, "error": True, "message": str(e)}

def notify_followers(owner, product_name, action_type):
    """
    Notify all followers of the owner when a product is added or modified.
    """
    conn = sqlite3.connect("auboutique.db")
    cursor = conn.cursor()

    # Fetch all followers of the owner
    query = "SELECT user FROM subscribed_owners WHERE owner = ?"
    cursor.execute(query, (owner,))
    followers = cursor.fetchall()
    conn.commit()
    conn.close()
    
    notification = {
        "type": 1,  # Notification type
        "owner": owner,
        "product_name": product_name,
        "action": action_type  # 'added' or 'modified'
    }
    
    for follower in followers:
        follower_username = follower[0]
        if follower_username in online_users:
            # Notify online users
            send_to_client(follower_username, notification)
    


def send_to_client(username, notification):
    """
    Send a notification to an online user using their existing client-server socket.
    """
    if username in online_users:
        client_socket = online_users[username]["client_socket"]  # Get the client's socket
        try:
            # Send the notification directly through the existing socket
            client_socket.send(json.dumps(notification).encode('utf-8'))
        except Exception as e:
            print(f"Failed to send notification to {username}: {e}")
            # Optionally handle the error, e.g., remove the user from online_users
    


