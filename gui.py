from PyQt5.QtWidgets import ( QApplication,QComboBox, QMainWindow, QLabel, QPushButton, QVBoxLayout,QWidgetAction,QDialog,
    QHBoxLayout, QWidget, QScrollArea, QFrame, QInputDialog, QMessageBox, QLineEdit, QMenu, QListWidget, QListWidgetItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QPoint, QMetaObject, pyqtSignal, pyqtSlot, Q_ARG,  QTimer
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPolygon, QPixmap
import math
import sys  
from functions import *
from socket import *
import json
import threading
import time
import requests
from datetime import datetime

# Function to send a command to the server
def send_command(command, data=None):
    message = {"command": command}
    if data:
        message.update(data)
    client.send(json.dumps(message).encode('utf-8'))
    while len(responses)==0:
        time.sleep(0.1)
    x=responses.pop()
    
    return x

# Function to listen for incoming messages
def listen_for_responses():
    while True:
        try:
            response = client.recv(4096).decode('utf-8')
            if len(response)<=1: continue
            data = json.loads(response)
            if data["type"] == 0:  # Command Reply
                responses.append(data)
            elif data["type"] == 1:  # Notification
                app = QApplication.instance()
                for window in app.topLevelWidgets():
                    if isinstance(window, MainWindow):
                        current_page = window.container_layout.itemAt(0).widget()
                        if isinstance(current_page, ProductListPage):
                            current_page.notification_received.emit(data)
                            break
        except BlockingIOError:
            time.sleep(0.1)
        except Exception as e:
            print(f"Error listening: {e}")
            break

def handle_peer_connection(conn, addr):
    """
    Handle a single peer connection and directly update the chat UI.
    """
    try:
        # Receive the message
        peer_message = conn.recv(1024).decode('utf-8')
        data = json.loads(peer_message)
        
        # Extract message details
        sender = data["sender"]
        message = data["message"]
        timestamp = data["time"]
        
        app = QApplication.instance()
        for window in app.topLevelWidgets():
            if isinstance(window, MainWindow):
                
                current_page = window.container_layout.itemAt(0).widget()
                if isinstance(current_page, ProductListPage):
                    
                    current_page.chat_panel.incoming_message(sender, message, timestamp,is_user=False)
                    break
                
    except Exception as e:
        print(f"Error handling peer connection from {addr}: {e}")
    finally:
        conn.close()  # Close the connection

def listen_for_peers():
    """
    Listen for incoming peer-to-peer connections and handle them immediately.
    """
    while True:
        try:
            conn, addr = peer_socket.accept()  # Accept an incoming connection
            print(f"New peer connection from {addr}")
            # Handle each peer connection in a new thread
            threading.Thread(target=handle_peer_connection, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"Error in peer listener: {e}")
            break




client = socket(AF_INET, SOCK_STREAM)
client.connect(('localhost', 8888))

peer_socket = socket(AF_INET, SOCK_STREAM)
peer_socket.bind(('localhost', 0))  # Bind to any available port
peer_socket.listen(5)
print("Listening for peers on ", peer_socket.getsockname())
# Get the assigned port
peer_port = peer_socket.getsockname()[1]


responses=[]
listener_thread = threading.Thread(target=listen_for_responses, daemon=True)
listener_thread.start()

peer_listener_thread = threading.Thread(target=listen_for_peers, daemon=True)
peer_listener_thread.start()

style = """
    QWidget {
        background-color: #f0f0f0;
        font-family: Arial, sans-serif;
        font-size: 14px;
    }
    
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px;
        font-size: 16px;
    }

    QPushButton:hover {
        background-color: #45a049;
    }
    
    QLineEdit {
        background-color: white;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 14px;
    }

    QLabel {
        color: #333;
        font-weight: bold;
        text-align: center;
    }

    QVBoxLayout, QHBoxLayout {
        margin: 10px;
        padding: 10px;
    }
"""

class EntryPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Store reference to MainWindow
        layout = QVBoxLayout()

        header = QLabel("AUBoutique")
        header.setStyleSheet("font-size: 150px; font-weight: bold; text-align: center; background: transparent;")
        header.setAlignment(Qt.AlignCenter)  # Center the label text
        layout.addWidget(header)
        
        # Adjust layout margins and spacing
        layout.setContentsMargins(100, 100, 100, 50)
        layout.setSpacing(10)

        # Login Button
        login_button = QPushButton("Login")
        login_button.setStyleSheet("font-size: 50px; padding: 15px;")
        login_button.setFixedSize(300, 200)
        login_button.clicked.connect(self.go_to_login)
        
        # Register Button
        register_button = QPushButton("Register")
        register_button.setStyleSheet("font-size: 50px; padding: 15px;")
        register_button.setFixedSize(300, 200)
        register_button.clicked.connect(self.go_to_register)
        
        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.setStyleSheet("font-size: 50px; background-color: red; color: white; padding: 15px;")
        quit_button.setFixedSize(300, 200)
        quit_button.clicked.connect(self.quit_page)

        
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(login_button, alignment=Qt.AlignCenter)
        buttons_layout.addWidget(register_button, alignment=Qt.AlignCenter)
        buttons_layout.addWidget(quit_button, alignment=Qt.AlignCenter)
        
        self.background_label = QLabel(self)
        self.background_label.setPixmap(QPixmap('test.jpg'))
        self.background_label.setScaledContents(True)
        self.background_label.lower()
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
    def resizeEvent(self, event):
        """Ensure the background image scales with the window."""
        super().resizeEvent(event)  # Ensures default resize behavior is maintained
        self.background_label.resize(self.size())  # Resize the background to match the window size
    
    def quit_page(self):
        """Quit the entire application."""
        for widget in QApplication.instance().allWidgets():
            widget.close()  # Close all open widgets
        send_command("quit")
        QApplication.instance().quit()  # Gracefully terminate the application
        


    def go_to_login(self):
        self.main_window.set_page(LoginPage(self.main_window))  # Use self.main_window to call set_page

    def go_to_register(self):
        self.main_window.set_page(RegistrationPage(self.main_window))  # Use self.main_window to call set_page

class RegistrationPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Store reference to MainWindow
        layout = QVBoxLayout()

        header = QLabel("Register")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Registration input fields
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Name")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.name_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.register)
        layout.addWidget(submit_button)

        back_button = QPushButton("Go Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)
        
        self.setLayout(layout)

    def register(self):
        name = self.name_input.text()
        email = self.email_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        
        registration_data = {
            "name": name,
            "email": email,
            "username": username,
            "password": password
        }

        if name and email and username and password:
            response =send_command("register", registration_data)
            if  not response["error"]:
                QMessageBox.information(self, "Success", response["content"])
                self.main_window.set_page(EntryPage(self.main_window))
            else:
                QMessageBox.critical(self, "Error",  "Username is already taken!")
        else:
            QMessageBox.critical(self, "Error",  "Please fill in all fields.")
        
    def go_back(self):
        self.main_window.set_page(EntryPage(self.main_window))


class LoginPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()

        header = QLabel("Login")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.login)
        layout.addWidget(submit_button)

        back_button = QPushButton("Go Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        login_data = {
            "username": username,
            "password": password,
            "p2p_address": peer_socket.getsockname()
        }
        
        if username and password:
            response = send_command("login", login_data)
            if not response["error"]:
                QMessageBox.information(self, "Success", response["content"])
                self.parent().username = username  # Store logged-in username
                self.main_window.set_page(ProductListPage(self.main_window, username))
                self.main_window.showMaximized()
            else:
                QMessageBox.warning(self, "Error", response["content"])
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")


    def go_back(self):
        self.main_window.set_page(EntryPage(self.main_window))

class ProductWidget(QFrame):
    """Widget to display a single product as a box with border."""
    def __init__(self, product_id, name, description, price, owner, rating, quantity, username, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.name = name
        self.description = description
        self.original_price = price  # Store the original USD price
        self.price = price  # Current price (updated with currency)
        self.owner = owner
        self.rating = rating
        self.quantity = quantity
        self.username = username
        self.currency_symbol = "$"
        
        # Set QFrame styling to look like a box
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 15px;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.setFixedHeight(351) #Easter Egg
        
        # Main layout for the product widget
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # Left: Product details
        details_layout = QVBoxLayout()

        # Name and description
        name_label = QLabel(self.name)
        name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        description_label = QLabel(self.description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px; color: #555;")
        self.quantity_label = QLabel(f"Quantity: {self.quantity}")
        self.quantity_label.setStyleSheet("font-size: 14px; color: #333;")

        # Average rating and rate button
        rating_layout = QHBoxLayout()
        rating_layout.setSpacing(5)  # Reduced spacing to bring the Rate button closer to the stars
        rating_layout.setAlignment(Qt.AlignLeft)

        average_rating_label = QLabel("Average Rating:")  # Added label for average rating
        average_rating_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")

        self.rating_widget = RatingWidget(self.rating)
        rate_button = QPushButton("Rate")
        rate_button.setFixedSize(80, 30)
        rate_button.clicked.connect(self.rate)

        rating_layout.addWidget(average_rating_label)
        rating_layout.addWidget(self.rating_widget)
        rating_layout.addWidget(rate_button)

        # Add labels and rate button to the details layout
        details_layout.addWidget(name_label)
        details_layout.addWidget(description_label)
        details_layout.addWidget(self.quantity_label)
        details_layout.addLayout(rating_layout)

        layout.addLayout(details_layout)

        # Right: Owner, price, and add to cart button
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignTop)

        # Owner label
        owner_label = QLabel(f"Owner: {self.owner}")
        owner_label.setStyleSheet("font-size: 14px; color: #777;")

        # Price label
        self.price_label = QLabel(f"Price: {self.currency_symbol}{self.price:.2f}")
        self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")

        # Add to Cart button
        add_to_cart_button = QPushButton("Add to Cart")
        add_to_cart_button.setFixedSize(100, 40)
        add_to_cart_button.clicked.connect(self.add_to_cart)

        # Add widgets to the buttons layout
        buttons_layout.addWidget(owner_label)
        buttons_layout.addWidget(self.price_label)
        buttons_layout.addStretch()  # Add some space between price and button
        buttons_layout.addWidget(add_to_cart_button)

        
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def update_price(self, exchange_rate, symbol):
        """Update the displayed price using the original USD price."""
        self.price = round(self.original_price * exchange_rate, 2)  # Convert using the original USD price
        self.currency_symbol = symbol
        self.price_label.setText(f"Price: {self.currency_symbol}{self.price:.2f}")

    def add_to_cart(self):
        """Prompt for quantity and add the product to the cart."""
        quantity, ok = QInputDialog.getInt(self, "Add to Cart", "Enter quantity:", min=1, max=self.quantity)
        if ok:
            cart_data = {
                "product_id": self.product_id,
                "username": self.username,
                "quantity": quantity
            }
    
            try:
                response = send_command("add_to_cart", cart_data)
                if response["error"]:
                    QMessageBox.warning(self, "Error", response["content"])
                else:
                    QMessageBox.information(self, "Success", response["content"])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to communicate with the server: {str(e)}")


    def update_quantity_display(self):
        """Update the displayed quantity in the UI."""
        details_layout = self.layout().itemAt(0).layout()  # Locate the details layout
        quantity_label = None
    
        # Ensure we find the correct quantity label
        for i in range(details_layout.count()):
            widget = details_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and "Quantity:" in widget.text():
                quantity_label = widget
                break
    
        if quantity_label:
            quantity_label.setText(f"Quantity: {self.quantity}")  # Update the quantity
        else:
            print("Error: Quantity label not found.")


    
    def rate(self):
        # Ask the user for a rating (1-5)
        rating, ok = QInputDialog.getInt(self, "Rate Product", "Enter your rating (1-5):", min=1, max=5)
        if ok:
            # Prepare the data to be sent to the server
            rating_data = {
                "username": self.username,  # Pass the logged-in user's username
                "product_id": self.product_id,
                "rating": rating
            }
    
            # Send the command to the server
            response = send_command("rate", rating_data)
    
            if not response["error"]:
                # Update the rating widget with the new average rating
                new_average_rating = response["content"]
                self.rating_widget.update_rating(new_average_rating)
            else:
                QMessageBox.warning(self, "Error", "Failed to rate the product.")


class AddProductPage(QWidget):
    def __init__(self, main_window, username):
        super().__init__()
        self.main_window = main_window
        self.username = username

        layout = QVBoxLayout()

        header = QLabel("Add Product")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Input fields
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Product Name")
        self.description_input = QLineEdit(self)
        self.description_input.setPlaceholderText("Description")
        self.price_input = QLineEdit(self)
        self.price_input.setPlaceholderText("Price")
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setPlaceholderText("Quantity")

        layout.addWidget(self.name_input)
        layout.addWidget(self.description_input)
        layout.addWidget(self.price_input)
        layout.addWidget(self.quantity_input)

        # Submit button
        submit_button = QPushButton("Add Product")
        submit_button.clicked.connect(self.add_product)
        layout.addWidget(submit_button)

        back_button = QPushButton("Cancel")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def add_product(self):
        name = self.name_input.text()
        description = self.description_input.text()
        price = self.price_input.text()
        quantity = self.quantity_input.text()

        if not (name and description and price and quantity):
            QMessageBox.warning(self, "Error", "All fields must be filled.")
            return

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid price or quantity format.")
            return

        data = {
            "name": name,
            "description": description,
            "price": price,
            "quantity": quantity,
            "owner": self.username
        }
        response = send_command("add_product", data)

        if response["error"]:
            QMessageBox.warning(self, "Error", response["content"])
        else:
            QMessageBox.information(self, "Success", response["content"])
            self.main_window.set_page(ProductListPage(self.main_window, self.username))

    def go_back(self):
        self.main_window.set_page(ProductListPage(self.main_window, self.username))



class ModifyProductPage(QWidget):
    """Page to modify an existing product."""
    def __init__(self, main_window, username, product_id, name, description, price, quantity):
        super().__init__()
        self.main_window = main_window
        self.username = username
        self.product_id = product_id

        layout = QVBoxLayout()

        header = QLabel("Modify Product")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Input fields pre-filled with product data
        self.name_input = QLineEdit(self)
        self.name_input.setText(name)
        self.description_input = QLineEdit(self)
        self.description_input.setText(description)
        self.price_input = QLineEdit(self)
        self.price_input.setText(str(price))
        self.quantity_input = QLineEdit(self)
        self.quantity_input.setText(str(quantity))

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        layout.addWidget(QLabel("Price:"))
        layout.addWidget(self.price_input)
        layout.addWidget(QLabel("Quantity:"))
        layout.addWidget(self.quantity_input)

        # Submit button
        submit_button = QPushButton("Save Changes")
        submit_button.clicked.connect(self.modify_product)
        layout.addWidget(submit_button)

        back_button = QPushButton("Cancel")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def modify_product(self):
        """Send the modified product details to the server."""
        name = self.name_input.text()
        description = self.description_input.text()
        price = self.price_input.text()
        quantity = self.quantity_input.text()

        if not (name and description and price and quantity):
            QMessageBox.warning(self, "Error", "All fields must be filled.")
            return

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid price or quantity format.")
            return

        data = {
            "product_id": self.product_id,
            "name": name,
            "description": description,
            "price": price,
            "quantity": quantity
        }
        response = send_command("modify_product", data)

        if response["error"]:
            QMessageBox.warning(self, "Error", response["content"])
        else:
            QMessageBox.information(self, "Success", "Product modified successfully.")
            self.main_window.set_page(MyProductsPage(self.main_window, self.username))

    def go_back(self):
        """Go back to the My Products page."""
        self.main_window.set_page(MyProductsPage(self.main_window, self.username))
        
class MyProductWidget(QFrame):
    """Widget to display a product owned by the user."""
    def __init__(self, product_id, name, description, price, quantity, main_window, username, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity
        self.main_window = main_window
        self.username = username

        # Set QFrame styling to look like a box
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 15px;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
        """)

        # Main layout for the product widget
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Name and description
        name_label = QLabel(self.name)
        name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        description_label = QLabel(self.description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px; color: #555;")

        # Price and quantity
        price_label = QLabel(f"Price: ${self.price:.2f}")
        price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        quantity_label = QLabel(f"Quantity: {self.quantity}")
        quantity_label.setStyleSheet("font-size: 14px; color: #333;")

        # Modify Product button
        modify_button = QPushButton("Modify Product")
        modify_button.setStyleSheet("background-color: blue; color: white; font-size: 14px;")
        modify_button.clicked.connect(self.modify_product)

        # View Buyers button
        self.view_buyers_button = QPushButton("View Buyers")
        self.view_buyers_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 3px;
                background-color: #4CAF50;  /* Green button */
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        self.view_buyers_button.clicked.connect(self.toggle_buyers_visibility)

        # Add labels and buttons to the layout
        self.layout.addWidget(name_label)
        self.layout.addWidget(description_label)
        self.layout.addWidget(price_label)
        self.layout.addWidget(quantity_label)
        self.layout.addWidget(modify_button)
        self.layout.addWidget(self.view_buyers_button)

        self.setLayout(self.layout)

    def modify_product(self):
        """Open the Modify Product page for this product."""
        self.main_window.set_page(
            ModifyProductPage(
                self.main_window,
                self.username,
                self.product_id,
                self.name,
                self.description,
                self.price,
                self.quantity
            )
        )

    def toggle_buyers_visibility(self):
        """Toggle the visibility of the buyers widget."""
        if hasattr(self, 'buyers_widget') and self.buyers_widget.isVisible():
            # Hide buyers widget and update the button text
            self.buyers_widget.setVisible(False)
            self.view_buyers_button.setText("View Buyers")
        else:
            # Fetch buyers and show the buyers widget
            self.fetch_and_display_buyers()

    def fetch_and_display_buyers(self):
        """Fetch buyers from the server and display them."""
        try:
            data = {"product_id": self.product_id}
            response = send_command("view_product_buyers", data)  # Server call

            if response["error"]:
                QMessageBox.warning(self, "Error", response["message"])
            else:
                buyers = response["content"]
                self.display_buyers(buyers)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch buyers: {str(e)}")

    def display_buyers(self, buyers):
        """Show buyers in a dropdown-style widget below the current product widget."""
        # Remove the existing buyers widget if it exists
        if hasattr(self, 'buyers_widget'):
            self.layout.removeWidget(self.buyers_widget)
            self.buyers_widget.deleteLater()

        # Create the buyers widget
        self.buyers_widget = QWidget()
        buyers_layout = QVBoxLayout()
        self.buyers_widget.setLayout(buyers_layout)
        self.buyers_widget.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
        """)

        # Populate buyers information
        if buyers:
            for buyer in buyers:
                buyer_info = f"Name: {buyer['name']} | Username: {buyer['username']} | Email: {buyer['email']}"
                buyer_label = QLabel(buyer_info)
                buyers_layout.addWidget(buyer_label)
        else:
            buyers_layout.addWidget(QLabel("No buyers found for this product."))

        # Add the buyers widget to the main layout
        self.layout.addWidget(self.buyers_widget)
        self.buyers_widget.setVisible(True)

        # Update the button text
        self.view_buyers_button.setText("Hide Buyers")


class MyProductsPage(QWidget):
    def __init__(self, main_window, username):
        super().__init__()
        self.main_window = main_window
        self.username = username

        layout = QVBoxLayout()

        # Header
        header = QLabel("My Products")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Scrollable area for products
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)


        content_layout.setSpacing(10)  # Add spacing between widgets
        content_layout.setContentsMargins(10, 10, 10, 10)  # Add margins
        content_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        
        # Fetch and display user's products
        try:
            data = {"username": self.username}
            response = send_command("view_products_by_owner", data)

            if response["error"]:
                QMessageBox.warning(self, "Error", response["content"])
            else:
                products = response["content"]
                if products:
                    for product in products:
                        # Adjust the unpacking to match the server's response
                        product_id, name, description, price, quantity, *_ = product

                        # Add each product as a MyProductWidget
                        product_widget = MyProductWidget(
                            product_id, name, description, price, quantity, self.main_window, self.username
                        )
                        content_layout.addWidget(product_widget)
                else:
                    no_products_label = QLabel("You have no products.")
                    no_products_label.setStyleSheet("font-size: 16px; text-align: center;")
                    no_products_label.setAlignment(Qt.AlignCenter)
                    content_layout.addWidget(no_products_label)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")


        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Back button
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def go_back(self):
        """Navigate back to the product list page."""
        self.main_window.set_page(ProductListPage(self.main_window, self.username))

        
class RatingWidget(QWidget):
    """Widget to display rating as stars."""
    def __init__(self, rating, parent=None):
        super().__init__(parent)
        self.rating = rating
        self.setFixedSize(260, 40)  
        
    def update_rating(self, rating):
        """Update the rating displayed by the widget."""
        self.rating = rating
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        star_size = 12  # Size of each star
        spacing = 8     # Reduced space between stars to bring them closer
        total_stars = 5

        filled_color = QColor("#FFD700")  # Gold color for filled star
        empty_color = QColor("#ccc")      # Gray color for empty star

        def draw_star(x, y, size, fill_ratio=1.0):
            """Helper function to draw a star with a given fill ratio."""
            # Define the star points
            star_points = []
            for i in range(10):
                angle = math.pi / 5 * i
                radius = size if i % 2 == 0 else size / 2.5
                px = int(x + math.cos(angle) * radius)
                py = int(y - math.sin(angle) * radius)
                star_points.append(QPoint(px, py))

            star_polygon = QPolygon(star_points)

            if fill_ratio == 1:
                # Full star
                painter.setBrush(QBrush(filled_color))
                painter.drawPolygon(star_polygon)
            elif fill_ratio > 0:
                # Partial star - draw filled part
                painter.setBrush(QBrush(filled_color))
                painter.setClipRect(x - size, y - size, int(size * 2 * fill_ratio), int(size * 2), Qt.ReplaceClip)
                painter.drawPolygon(star_polygon)
                painter.setClipping(False)

                # Draw empty part
                painter.setBrush(QBrush(empty_color))
                painter.setClipRect(x - size + int(size * 2 * fill_ratio), y - size, int(size * 2 * (1 - fill_ratio)), int(size * 2), Qt.ReplaceClip)
                painter.drawPolygon(star_polygon)
                painter.setClipping(False)
            else:
                # Empty star
                painter.setBrush(QBrush(empty_color))
                painter.drawPolygon(star_polygon)

        
        # Determine how many stars are completely filled and if there is a partially filled star
        full_stars = int(self.rating)
        partial_star_ratio = self.rating - full_stars

        # Draw the stars based on the rating
        for i in range(total_stars):
            x = 10 + i * (star_size + spacing) + (star_size // 2)  # Added 10 to x to move all stars to the right
            y = star_size + 8  # Lowered stars by adjusting y value

            if i < full_stars:
                draw_star(x, y, star_size, 1)  # Draw full star
            elif i == full_stars and partial_star_ratio > 0:
                draw_star(x, y, star_size, partial_star_ratio)  # Draw partially filled star
            else:
                draw_star(x, y, star_size, 0)  # Draw empty star

        # Draw numeric rating value to the right of stars
        painter.setPen(QColor("#333"))
        text_x = total_stars * (star_size + spacing) + 20  # Adjusted to add more space between stars and text
        text_y = y + 3  # Lowered the text to align better with the stars
        painter.drawText(text_x, text_y, f"{self.rating:.1f}")

class ProductListPage(QWidget):
    """Page to display a scrollable list of product boxes with additional features."""
    notification_received = pyqtSignal(dict)  # Signal to handle incoming notifications

    def __init__(self, main_window, username):
        super().__init__()
        self.username = username  # Store the logged-in username
        self.main_window=main_window
        self.current_currency = "USD"  # Default currency
        self.exchange_rates = self.fetch_exchange_rates()
        self.currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}
        
        
        # Connect the notification signal to a handler
        self.notification_received.connect(self.handle_notification)

        # Main layout
        main_layout = QVBoxLayout(self)

        # --- HEADER LAYOUT ---
        header_layout = QHBoxLayout()

        # Unified header layout
        header_layout = QHBoxLayout()

        # Username button with dropdown menu
        self.username_button = QPushButton(self.username)
        self.username_button.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        menu = QMenu()
        menu.addAction("My Products").triggered.connect(lambda: self.main_window.set_page(MyProductsPage(self.main_window, self.username)))
        menu.addAction("Add Product").triggered.connect(lambda: self.main_window.set_page(AddProductPage(self.main_window, self.username)))
        menu.addAction("Log out").triggered.connect(self.logout)
        self.username_button.setMenu(menu)
        header_layout.addWidget(self.username_button, stretch=0)  # No stretch for the username button
        

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for products or owners...")
        self.search_bar.textChanged.connect(self.filter_products)  # Connect to filtering function
        header_layout.addWidget(self.search_bar, stretch=5)  # Stretch factor for a wider search bar

        # Cart button 
        cart_button = QPushButton("🛒")  
        cart_button.setFixedSize(40, 40)  # Adjust the size for better appearance
        cart_button.setStyleSheet("""
            QPushButton {
                font-size: 20px;  /* Larger font size for emoji */
                background-color: transparent;  /* Transparent background */
                border: none;
            }
            QPushButton:hover {
                background-color: #f0f0f0;  /* Light gray background on hover */
                border-radius: 5px;
            }
        """)
        cart_button.clicked.connect(lambda: self.main_window.set_page(CartPage(self.main_window, self.username)))
        header_layout.addWidget(cart_button, stretch=0)  # No stretch for the cart button

        # Currency selector
        self.currency_selector = QComboBox()
        self.currency_selector.addItems(["USD", "EUR", "GBP", "JPY", "INR"])
        self.currency_selector.setCurrentText("USD")
        self.currency_selector.currentTextChanged.connect(self.update_currency)
        self.currency_selector.setFixedWidth(100)  # Fixed width for the currency box
        header_layout.addWidget(self.currency_selector, stretch=0)  # No stretch for the currency selector

        # Add the unified header layout to the main layout
        main_layout.addLayout(header_layout)


        # --- CONTENT AREA ---
        content_area_layout = QHBoxLayout()  # Horizontal layout for products and button

        # --- SCROLL AREA FOR PRODUCTS ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Content widget for the scroll area
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        self.content_layout.setSpacing(10)  # Add spacing between widgets
        self.content_layout.setContentsMargins(10, 10, 10, 10)  # Add margins

        # Prevent excessive stretching
        content_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        # Fetch products from the database and add to the content layout
        products = send_command("view_products")
        for product in products["content"]:
            product_id, name, description, price, owner, rating, quantity = product
            product_widget = ProductWidget(product_id, name, description, price, owner, rating, quantity, self.username)
            self.content_layout.addWidget(product_widget)

        content_widget.setLayout(self.content_layout)
        scroll_area.setWidget(content_widget)

        # Add scroll area to the content area layout
        content_area_layout.addWidget(scroll_area, stretch=5)

        # --- CHAT TOGGLE BUTTON CONTAINER ---
        button_container = QVBoxLayout()  # Create a container layout for the button
        button_container.setAlignment(Qt.AlignVCenter)  # Vertically center the button

        self.chat_button = QPushButton("◀")
        self.chat_button.setFixedSize(40, 40)  # Circular button
        self.chat_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.chat_button.clicked.connect(self.toggle_chat_panel)

        button_container.addWidget(self.chat_button)

        # Add the button container layout to the content area layout
        content_area_layout.addLayout(button_container, stretch=1)

        # Add content area layout to the main layout
        main_layout.addLayout(content_area_layout)

        # Chat panel
        self.chat_panel = ChatPanel(self.username,self)
        self.chat_panel.setGeometry(800, 0, 0, 600)  # Initially hidden
        self.chat_animation = QPropertyAnimation(self.chat_panel, b"geometry")

        self.setLayout(main_layout)

        # Notification popup widget (initially hidden)
        self.notification_popup = QLabel(self)
        self.notification_popup.setStyleSheet("""
            QLabel {
                background-color: #444;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #000;
            }
        """)
        self.notification_popup.setGeometry(0, -50, self.width(), 50)  # Initially hidden above the window
        self.notification_animation = QPropertyAnimation(self.notification_popup, b"geometry")


    def resizeEvent(self, event):
        super().resizeEvent(event)
        chat_width = self.width() // 3
    
        if self.chat_panel.width() > 0:
            self.chat_panel.setGeometry(self.width() - chat_width, 0, chat_width, self.height())
        else:
            self.chat_panel.setGeometry(self.width(), 0, 0, self.height())
    
        
        self.notification_popup.setGeometry(0, -50, self.width(), 50)
    
        # Update the button position
        self.update_chat_button_position()
        
        
    def handle_notification(self, notification):
        """
        Display a notification drop-down from the top of the window.
        """

        # Set the text of the notification popup
        self.notification_popup.setText(f"Notification: {notification['owner']} {notification['action']} '{notification['product_name']}'")
        self.notification_popup.setGeometry(0, -50, self.width(), 50)  # Start position above the window

        # Animate the popup to slide down
        self.notification_animation.setDuration(500)  # Animation duration in milliseconds
        self.notification_animation.setStartValue(QRect(0, -50, self.width(), 50))
        self.notification_animation.setEndValue(QRect(0, 0, self.width(), 50))
        self.notification_animation.start()

        # Hide the popup after 3 seconds
        QTimer.singleShot(8000, lambda: self.hide_notification())

    def hide_notification(self):
        """
        Hide the notification popup by sliding it back up.
        """
        self.notification_animation.setDuration(500)  # Animation duration in milliseconds
        self.notification_animation.setStartValue(QRect(0, 0, self.width(), 50))
        self.notification_animation.setEndValue(QRect(0, -50, self.width(), 50))
        self.notification_animation.start()

    def toggle_chat_panel(self):
        """Slide the chat panel in and out, keeping it proportional."""
        chat_width = self.width() // 3

        if self.chat_panel.width() == 0:  # Slide in
            self.chat_animation.setStartValue(QRect(self.width(), 0, 0, self.height()))
            self.chat_animation.setEndValue(QRect(self.width() - chat_width, 0, chat_width, self.height()))
            self.chat_button.setText("▶")
        else:  # Slide out
            self.chat_animation.setStartValue(QRect(self.width() - chat_width, 0, chat_width, self.height()))
            self.chat_animation.setEndValue(QRect(self.width(), 0, 0, self.height()))
            self.chat_button.setText("◀")

        self.chat_animation.setDuration(300)
        self.chat_animation.valueChanged.connect(self.update_chat_button_position)
        self.chat_animation.start()
        self.chat_button.update()

    def update_chat_button_position(self):
        """Update the chat button position to align with the chat panel."""
        button_y = self.height() // 2 - self.chat_button.height() // 2
        self.chat_button.move(self.width() - self.chat_panel.width() - self.chat_button.width(), button_y)
  
    def fetch_exchange_rates(self):
        """Fetch real-time exchange rates from an API."""
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            response.raise_for_status()
            data = response.json()
            return data.get("rates", {})         
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return {"USD": 1, "EUR": 0.85, "GBP": 0.75, "JPY": 110, "INR": 73}

    def update_currency(self, currency):
        """Update displayed prices when the currency changes."""
        self.current_currency = currency
        symbol = self.currency_symbols.get(currency, "$")
        exchange_rate = self.exchange_rates.get(currency, 1)

        # Update each product widget
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, ProductWidget):
                widget.update_price(exchange_rate, symbol)

    def filter_products(self, text):
        """Filter displayed products based on the search query."""
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, ProductWidget):
                # Check if the search query matches the product name or owner name
                widget.setVisible(
                    text.lower() in widget.name.lower() or text.lower() in widget.owner.lower()
                )
                
    def logout(self):
        """Handle user logout and redirect to the login page."""
        send_command("log_out")
        confirm = QMessageBox.question(self, "Log Out", "Are you sure you want to log out?",QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.main_window.set_page(MainWindow())



class CartPage(QWidget):
    def __init__(self, main_window, username):
        super().__init__()
        self.main_window = main_window
        self.username = username
        self.setWindowTitle("Your Cart")
        self.setGeometry(100, 100, 600, 800)

        self.current_currency = "USD"  # Default currency
        self.exchange_rates = self.fetch_exchange_rates()  # Fetch exchange rates
        self.currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}

        # Main layout
        self.layout = QVBoxLayout(self)

        # Header layout with back button and currency selector
        header_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("Back")
        back_button.setStyleSheet("background-color: lightgray; color: black; font-size: 16px; padding: 5px;")
        back_button.clicked.connect(self.go_back)
        header_layout.addWidget(back_button)

        # Currency Dropdown
        self.currency_selector = QComboBox()
        self.currency_selector.addItems(["USD", "EUR", "GBP", "JPY", "INR"])
        self.currency_selector.setCurrentText("USD")
        self.currency_selector.currentTextChanged.connect(self.update_currency)
        header_layout.addWidget(QLabel("Currency:"))
        header_layout.addWidget(self.currency_selector)

        # Add header layout to main layout
        self.layout.addLayout(header_layout)

        # Header: Add a label to distinguish the product list
        self.header_label = QLabel("Cart Items")
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
        self.layout.addWidget(self.header_label)

        # Cart items layout (where items will be displayed)
        self.cart_items_layout = QVBoxLayout()
        self.cart_items_layout.setAlignment(Qt.AlignTop)  # Align items to the top of the container

        # Bottom layout (for total price and checkout button)
        self.bottom_layout = QHBoxLayout()

        # Add the bottom layout (checkout + total price) at the bottom
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        checkout_button = QPushButton("Checkout")
        checkout_button.setStyleSheet("background-color: green; color: white; font-size: 16px; padding: 10px;")
        checkout_button.clicked.connect(self.checkout)

        self.bottom_layout.addWidget(checkout_button)
        self.bottom_layout.addWidget(self.total_label, alignment=Qt.AlignRight)

        # Add cart items layout and bottom layout to the main layout
        self.layout.addLayout(self.cart_items_layout)
        self.layout.addLayout(self.bottom_layout)

        # Fetch and display cart items initially
        self.fetch_cart_items()

    def fetch_exchange_rates(self):
        """Fetch real-time exchange rates from an API."""
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            response.raise_for_status()
            data = response.json()
            return data.get("rates", {})
        except Exception as e:
            return {"USD": 1, "EUR": 0.85, "GBP": 0.75, "JPY": 110, "INR": 73}

    def update_currency(self, currency):
        """Update displayed prices for all cart items and total price when the currency changes."""
        try:
            self.current_currency = currency
            symbol = self.currency_symbols.get(currency, "$")
            exchange_rate = self.exchange_rates.get(currency, 1)
    
            total_price = 0
    
            # Update each cart item
            for i in range(self.cart_items_layout.count()):
                widget = self.cart_items_layout.itemAt(i).widget()
                if isinstance(widget, QFrame):  # Ensure we are working with cart item frames
                    # Update the price
                    price_label = widget.findChild(QLabel, "price_label")
                    base_price = float(price_label.property("base_price"))  # Base price is stored in a custom property
                    converted_price = base_price * exchange_rate
                    price_label.setText(f"{symbol}{converted_price:.2f}")
                    total_price += converted_price
    
            # Update the total label with the new currency and total
            self.total_label.setText(f"Total: {symbol}{total_price:.2f}")
        except Exception as e:
            print(f"Error updating currency: {e}")


    def go_back(self):
        """Go back to the previous page."""
        self.main_window.set_page(ProductListPage(self.main_window, self.username))
        

    def fetch_cart_items(self):
        """Fetch the cart items from the server and display them."""
        response = send_command("view_cart", {"username": self.username})
        if response["error"]:
            QMessageBox.warning(self, "Error", "Failed to fetch cart items.")
            return

        # Display the cart items
        self.display_cart(response["content"])

    def display_cart(self, cart_items):
        """Display all cart items in the cart_items_layout."""
        # Clear the current layout
        for i in reversed(range(self.cart_items_layout.count())):
            widget = self.cart_items_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
        total_price = 0
    
        for item in cart_items:
            product_id = item["product_id"]
            name = item["name"]
            price = item["price"]
            quantity = item["quantity"]
    
            # Create a box (QFrame) to contain the product info
            product_frame = QFrame()
            product_frame.setStyleSheet("border: 1px solid #ccc; border-radius: 10px; padding: 10px; margin-bottom: 10px;")
    
            # Create a horizontal layout for the product frame
            product_layout = QHBoxLayout()
    
            # Product Details
            details_layout = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setObjectName("name_label")  # Set object name to identify it later
            name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
    
            quantity_label = QLabel(f"Quantity: {quantity}")
            quantity_label.setObjectName("quantity_label")  # Set object name to identify it later
            quantity_label.setStyleSheet("font-size: 14px;")
    
            price_label = QLabel(f"${price:.2f}")
            price_label.setObjectName("price_label")  # Set object name to identify it later
            price_label.setProperty("base_price", price)  # Store base price in a custom property
            price_label.setStyleSheet("font-size: 14px; color: green;")
    
            # Add details to the layout
            details_layout.addWidget(name_label)
            details_layout.addWidget(quantity_label)
            details_layout.addWidget(price_label)
    
            product_layout.addLayout(details_layout)
    
            # "Remove" Button
            button_layout = QVBoxLayout()
            remove_button = QPushButton("Remove")
            remove_button.setStyleSheet("background-color: red; color: white; font-size: 18px;")
            remove_button.setFixedSize(300, 100)
            remove_button.clicked.connect(lambda _, pid=product_id: self.remove_from_cart(pid))
            button_layout.addWidget(remove_button, alignment=Qt.AlignCenter)  # Center the button
            product_layout.addLayout(button_layout)
    
            # Set the layout for the product frame
            product_frame.setLayout(product_layout)
    
            # Add the product frame to the cart items layout
            self.cart_items_layout.addWidget(product_frame)
    
            # Update total price
            total_price += price * quantity
    
        # Update the total label
        symbol = self.currency_symbols.get(self.current_currency, "$")
        self.total_label.setText(f"Total: {symbol}{total_price:.2f}")



    def checkout(self):
        """Clear the cart and display a success message."""
        response = send_command("checkout", {"username": self.username})
        if response["error"]:
            QMessageBox.warning(self, "Error", response["content"])
            return

        QMessageBox.information(self, "Success", response["content"])
        # Refresh the cart after checkout
        self.fetch_cart_items()
        
    def remove_from_cart(self, product_id):
        """Remove an item from the cart."""
        response = send_command("remove_from_cart", {"username": self.username, "product_id": product_id})
        if response["error"]:
            QMessageBox.warning(self, "Error", "Failed to remove item from cart.")
            return
    
        # Refresh the cart
        self.fetch_cart_items()



class ChatPanel(QWidget):
    """Sliding chat panel with recent chats and full chat functionality."""
    new_message_signal = pyqtSignal(str, str, str, bool)
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.new_message_signal.connect(self.handle_incoming_message)
        self.setStyleSheet("""
            QWidget {
                background-color: #f1f1f1;
                border-left: 1px solid #ccc;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Add recent chats view by default
        self.recent_chats_widget = self.build_recent_chats_view()
        self.chat_area_widget = None

        self.main_layout.addWidget(self.recent_chats_widget)

    def build_recent_chats_view(self):
        """Build the recent chats list view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for an owner...")
        self.search_bar.textChanged.connect(self.filter_chats)
        layout.addWidget(self.search_bar)

        # Recent chats list
        self.recent_chats_list = QListWidget()
        self.fetch_recent_chats()  # Fetch and populate the recent chats
        layout.addWidget(self.recent_chats_list)

        return widget
    
    def fetch_recent_chats(self):
        """Fetch recent chats from the server and update the UI."""
        response = send_command("fetch_users", {"username": self.current_user})
        if not response["error"]:
            chats = response["content"]
            self.recent_chats_list.clear()

            for chat in chats:
                owner = chat["owner"]
                is_followed = chat.get("is_followed", False)

                # Create a custom item for the chat
                item_widget = QWidget()
                item_layout = QVBoxLayout(item_widget)

                user_box = QFrame()
                user_box.setStyleSheet("""
                    QFrame {
                        border: 1px solid #ccc;
                        border-radius: 10px;
                        background-color: #f9f9f9;
                        padding: 10px;
                    }
                """)
                user_box_layout = QHBoxLayout(user_box)

                # Owner name
                owner_label = QLabel(owner)
                owner_label.setStyleSheet("font-size: 16px; font-weight: bold;")
                user_box_layout.addWidget(owner_label, alignment=Qt.AlignLeft)

                # Check Online Status Button
                check_button = QPushButton("Check if Online")
                check_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                check_button.clicked.connect(lambda _, owner=owner: self.check_online_status(owner))
                user_box_layout.addWidget(check_button, alignment=Qt.AlignLeft)

                # Follow/Unfollow Button
                follow_button = QPushButton("Unfollow" if is_followed else "Follow")
                follow_button.setStyleSheet("""
                    QPushButton {
                        background-color: #007BFF;
                        color: white;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #0056b3;
                    }
                """)
                follow_button.clicked.connect(lambda _, owner=owner, btn=follow_button: self.toggle_follow(owner, btn))
                user_box_layout.addWidget(follow_button, alignment=Qt.AlignLeft)

                # Chat Button
                chat_button = QPushButton("Chat")
                chat_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                chat_button.clicked.connect(lambda _, owner=owner: self.load_chat(self.current_user, owner))
                user_box_layout.addWidget(chat_button, alignment=Qt.AlignRight)

                # Finalize layout
                item_layout.addWidget(user_box)
                item_widget.setLayout(item_layout)

                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                self.recent_chats_list.addItem(list_item)
                self.recent_chats_list.setItemWidget(list_item, item_widget)
        else:
            QMessageBox.warning(self, "Error", "Failed to fetch recent chats.")

    def toggle_follow(self, owner, button):
        """Toggle follow/unfollow state for an owner."""
        action = "follow" if button.text() == "Follow" else "unfollow"
        response = send_command("toggle_follow", {"username": self.current_user, "owner": owner, "action": action})
        if not response["error"]:
            # Update button text based on the new state
            button.setText("Unfollow" if action == "follow" else "Follow")
        else:
            QMessageBox.warning(self, "Error", "Failed to update follow state.")


    def check_online_status(self, user):
        """Check if the specified user is online."""
        response = send_command("check_online_status", {"username": user})
        if not response["error"]:
            is_online = response["content"]["is_online"]
            status_message = f"{user} is {'Online' if is_online else 'Offline'}."
            QMessageBox.information(self, "Online Status", status_message)
        else:
            QMessageBox.warning(self, "Error", "Failed to check online status.")
            
            
    def build_chat_area_view(self, current_user, chat_with):
        """Build a dynamic chat area view for a specific user."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
    
        # Chat header with back button and owner name
        chat_header_layout = QHBoxLayout()
        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self.show_recent_chats)
        chat_header_layout.addWidget(self.back_button)
    
        self.chat_owner_label = QLabel(f"Chat with {chat_with}")
        self.chat_owner_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        chat_header_layout.addWidget(self.chat_owner_label)
    
        chat_header_layout.addStretch()
        layout.addLayout(chat_header_layout)
    
        # Chat history
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_content = QWidget()
        self.chat_content_layout = QVBoxLayout(self.chat_content)
        self.chat_content_layout.setAlignment(Qt.AlignTop)
        self.chat_history.setWidget(self.chat_content)
    
        # Fetch chat data from the server
        response = send_command("fetch_chats_between_users", {"other": chat_with})
        
        if not response["error"]:
            chat_data = response["content"]
    
            for msg in chat_data:
                sender = msg["sender"]
                message = msg["message"]
                timestamp=msg["time"]
                is_sent_by_current_user = (sender == current_user)
                
                self.add_chat_bubble(sender, message, is_sent_by_current_user,timestamp)
        else:
            QMessageBox.warning(self, "Error", "Failed to load chat messages.")
    
        layout.addWidget(self.chat_history)
    
        # Message input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input, stretch=2)
    
        self.send_button = QPushButton("➤")
        self.send_button.setFixedSize(40, 40)
        self.send_button.clicked.connect(lambda: self.send_message(current_user, chat_with))
        input_layout.addWidget(self.send_button)
    
        layout.addLayout(input_layout)
        return widget


    def load_chat(self, current_user, chat_with):
        """Load a chat area for the specified user."""
        if self.chat_area_widget:
            self.main_layout.removeWidget(self.chat_area_widget)
            self.chat_area_widget.deleteLater()

        self.chat_area_widget = self.build_chat_area_view(current_user, chat_with)
        self.main_layout.addWidget(self.chat_area_widget)

        self.recent_chats_widget.setVisible(False)
        self.chat_area_widget.setVisible(True)

        self.parent().update_chat_button_position()
        

    def add_chat_bubble(self, sender, message, is_user, timestamp):
        """Add a chat bubble to the chat history with a timestamp."""
        # Main layout for the bubble
        bubble_layout = QVBoxLayout()  # Vertical layout for the message and time
        message_layout = QHBoxLayout()  # Horizontal layout for alignment of message
        
        # Create the message label
        bubble_label = QLabel(message)
        bubble_label.setWordWrap(True)
        bubble_label.setFont(QFont("Arial", 12))
        bubble_label.setContentsMargins(10, 10, 10, 10)
        bubble_label.setFixedWidth(300)
    
        # Create the timestamp label
        time_label = QLabel(str(timestamp)[:-7])
        time_label.setFont(QFont("Arial", 8))
        time_label.setStyleSheet("color: gray;")
        
        
        # Style the bubble based on the sender
        if is_user:
            bubble_label.setStyleSheet("""
                QLabel {
                    background-color: #dcf8c6;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)
            time_label.setAlignment(Qt.AlignRight)
            message_layout.addStretch()
            message_layout.addWidget(bubble_label)
        else:
            bubble_label.setStyleSheet("""
                QLabel {
                    background-color: #ffffff;
                    border-radius: 15px;
                    padding: 10px;
                    border: 1px solid #ccc;
                }
            """)
            time_label.setAlignment(Qt.AlignLeft)
            message_layout.addWidget(bubble_label)
            message_layout.addStretch()
        
        # Add message and timestamp to the bubble layout
        bubble_layout.addLayout(message_layout)
        bubble_layout.addWidget(time_label)
    
        # Add the bubble to the chat content layout
        self.chat_content_layout.addLayout(bubble_layout)
        self.chat_content.update()
        self.chat_history.setWidget(self.chat_content)  # Ensure the widget is refreshed
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )


        
    def filter_chats(self):
        """Filter the recent chats based on the search text."""
        search_text = self.search_bar.text().lower()
        for i in range(self.recent_chats_list.count()):
            item = self.recent_chats_list.item(i)
            widget = self.recent_chats_list.itemWidget(item)
            if widget:
                owner_label = widget.findChild(QLabel)
                if owner_label and search_text not in owner_label.text().lower():
                    item.setHidden(True)
                else:
                    item.setHidden(False)

    def show_recent_chats(self):
        """Show the recent chats list and hide the chat area."""
        if self.chat_area_widget:
            self.main_layout.removeWidget(self.chat_area_widget)
            self.chat_area_widget.deleteLater()
            self.chat_area_widget = None

        self.recent_chats_widget.setVisible(True)

        # Ensure the chat toggle button is updated
        self.parent().update_chat_button_position()

    
    def incoming_message(self, sender, message, timestamp, is_user=False):
        """Handle an incoming message. Update the chat if the chat area is active."""
        def update_ui():
            if self.chat_area_widget and self.chat_owner_label.text().endswith(sender):

                self.add_chat_bubble(sender, message, is_user, timestamp)
            else:
                QMessageBox.information(self, "New Message", f"New message from {sender}: {message}")
        
        # Ensure this runs on the main thread
        QMetaObject.invokeMethod(self, "handle_incoming_message", Qt.QueuedConnection, Q_ARG(str, sender), Q_ARG(str, message), Q_ARG(str, timestamp), Q_ARG(bool, is_user))

    
    @pyqtSlot(str, str, str, bool)
    def handle_incoming_message(self, sender, message, timestamp, is_user):
        if self.chat_area_widget and self.chat_owner_label.text().endswith(sender):
           
            self.add_chat_bubble(sender, message, is_user, timestamp)
        else:
            QMessageBox.information(self, "New Message", f"New message from {sender}: {message}")

            
    def send_message(self, sender, recipient):
        """Send a message to the recipient using their IP address and port."""
        message_text = self.message_input.text()
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if not message_text:
            QMessageBox.warning(self, "Error", "Message cannot be empty.")
            return
    
        # Check if the recipient is online
        response = send_command("check_online_status", {"username": recipient})
        if not response["error"]:
            is_online = response["content"]["is_online"]
            if is_online:
                ip_address = response["content"]["ip_address"]
                port = response["content"]["port"]
                try:
                    # Establish a temporary socket connection to send the message
                    with socket(AF_INET, SOCK_STREAM) as temp_socket:
                        
                        temp_socket.connect((ip_address, port))
                        
                        message_data = {
                            "sender": sender,
                            "receiver": recipient,
                            "message": message_text,
                            "time": timestamp,
                        }
                        temp_socket.send(json.dumps(message_data).encode('utf-8'))
                        self.add_chat_bubble(sender, message_text, True, timestamp)
                        send_command("store_message", message_data)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")
            else:
                # Add the message to the database as pending
                message_data = {
                    "sender": sender,
                    "receiver": recipient,
                    "message": message_text,
                    "time": timestamp,
                }
                self.add_chat_bubble(sender, message_text, True,timestamp)
                send_command("store_message", message_data)
        else:
            QMessageBox.critical(self, "Error", "Failed to check online status.")
    
        # Clear the message input area after sending
        self.message_input.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique")
        self.setStyleSheet(style)
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.container_layout = QVBoxLayout() 
        self.container.setLayout(self.container_layout)
        self.set_page(EntryPage(self))  
        self.showMaximized()
        

    def set_page(self, page):
        if self.container_layout.count() > 0:
            widget = self.container_layout.itemAt(0).widget()
            if widget:
                widget.setParent(None)
        self.container_layout.addWidget(page)
        page.show()

    def resize_window(self, width, height):
        """Resize the window dynamically."""
        self.setGeometry(self.x(), self.y(), width, height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

 
