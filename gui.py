from PyQt5.QtWidgets import ( QApplication,QComboBox, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QScrollArea, QFrame, QInputDialog, QMessageBox, QLineEdit, QMenu, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QPoint
from PyQt5.QtGui import QIcon, QFont, QPainter, QBrush, QColor, QPolygon
import sqlite3
import math
import sys  
import sqlite3
from functions import *
from socket import *
import json
import threading
import time

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
            response = client.recv(1024).decode('utf-8')
            data = json.loads(response)
            if data["type"]==0: #Command Reply
                responses.append(data)
            elif data["type"]==1: #Message
                messages.append(data)
            elif data["type"]==2: #Notification
                notifs.append(data)
        except BlockingIOError:
            time.sleep(0.1)  
        except:
            print("Connection to the server was lost.")
            break

client = socket(AF_INET, SOCK_STREAM)
client.connect(('localhost', 8888))

responses=[]
messages=[]
notifs=[]
listener_thread = threading.Thread(target=listen_for_responses, daemon=True)
listener_thread.start()

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
        header.setStyleSheet("font-size: 24px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)  # Center the label text
        layout.addWidget(header)

        login_button = QPushButton("Login")
        register_button = QPushButton("Register")
        login_button.clicked.connect(self.go_to_login)
        register_button.clicked.connect(self.go_to_register)

        layout.addWidget(login_button)
        layout.addWidget(register_button)
        self.setLayout(layout)

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
            QMessageBox.critical(self, "Error", response["content"])
        
    def go_back(self):
        self.main_window.set_page(EntryPage(self.main_window))

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
            "password": password
        }
        
        if username and password:
            response = send_command("login", login_data)
            if not response["error"]:
                QMessageBox.information(self, "Success", response["content"])
                self.parent().username = username  # Store logged-in username
                self.main_window.set_page(ProductListPage(self.main_window, username))
                screen = QApplication.desktop().screenGeometry()
                self.main_window.resize(screen.width(), screen.height() - 40)
                self.main_window.move(0, 0)  # Move closer to the top
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
        """Adds a product to the cart."""
        # Prepare the data to be sent to the server
        cart_data = {
            "product_id": self.product_id,
            "username": self.username  
        }
        # Send the command to the server
        try:
            print("command sent")
            response = send_command("add_to_cart", cart_data)
            print("response recorded")
            # Handle the server response
            if response["error"]:
                QMessageBox.warning(self, "Error", response["content"])
            else:
                QMessageBox.information(self, "Success", response["content"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to communicate with the server: {str(e)}")


    def update_quantity_display(self):
        """Update the displayed quantity in the UI."""
        details_layout = self.layout().itemAt(0).layout()
        quantity_label = details_layout.itemAt(details_layout.count() - 1).widget()
        quantity_label.setText(f"Quantity: {self.quantity}")
    
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



class MyProductsPage(QWidget):
    def __init__(self, main_window, username):
        super().__init__()
        self.main_window = main_window
        self.username = username

        layout = QVBoxLayout()

        header = QLabel("My Products")
        header.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Scrollable area for products
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Fetch and display user's products
        try:
            data = {"username": self.username}
            response = send_command("view_products_by_owner", data)

            if response["error"]:
                QMessageBox.warning(self, "Error", response["content"])
            else:
                products = response["content"]
                for product in products:
                    try:
                        product_id, name, description, price, quantity, owner_username = product
                        product_label = QLabel(
                            f"Name: {name}\nDescription: {description}\nPrice: ${price:.2f}\n"
                            f"Quantity: {quantity}\nOwner: {owner_username}"
                        )
                        product_label.setStyleSheet("""
                            QLabel {
                                background-color: #f9f9f9;
                                border: 1px solid #ccc;
                                border-radius: 5px;
                                padding: 10px;
                                margin: 5px 0;
                            }
                        """)
                        content_layout.addWidget(product_label)
                    except ValueError as e:
                        QMessageBox.critical(self, "Error", f"Unexpected data format: {str(e)}")
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
    def __init__(self, main_window, username):
        super().__init__()
        self.username = username  # Store the logged-in username
        self.main_window=main_window
        self.current_currency = "USD"  # Default currency
        self.exchange_rates = self.fetch_exchange_rates()
        self.currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}

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
        menu.addAction("Log out")
        self.username_button.setMenu(menu)
        header_layout.addWidget(self.username_button, stretch=0)  # No stretch for the username button

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for products...")
        self.search_bar.textChanged.connect(self.filter_products)  # Connect to filtering function
        header_layout.addWidget(self.search_bar, stretch=5)  # Stretch factor for a wider search bar

        # Cart button 
        cart_button = QPushButton("🛒")  # Use the shopping cart emoji as the button label
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

    def resizeEvent(self, event):
        """Ensure the chat button and chat panel resize properly with the window."""
        super().resizeEvent(event)
        chat_width = self.width() // 3

        # Adjust the chat panel's position and size based on its current state
        if self.chat_panel.width() > 0:  # If the chat panel is open
            self.chat_panel.setGeometry(self.width() - chat_width, 0, chat_width, self.height())
        else:  # If the chat panel is closed
            self.chat_panel.setGeometry(self.width(), 0, 0, self.height())

        # Update the button position
        self.update_chat_button_position()

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
            # response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            # response.raise_for_status()
            # data = response.json()
            # return data.get("rates", {})
            return {"USD": 1, "EUR": 0.85, "GBP": 0.75, "JPY": 110, "INR": 73}
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return {"USD": 1}

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
                widget.setVisible(text.lower() in widget.name.lower())

class CartPage(QWidget):
    def __init__(self, main_window, username):
        super().__init__()
        self.main_window = main_window
        self.username = username
        self.setWindowTitle("Your Cart")
        self.setGeometry(100, 100, 600, 800)

        # Main layout
        self.layout = QVBoxLayout(self)

        # Back button (Top-left)
        back_button = QPushButton("Back")
        back_button.setStyleSheet("background-color: lightgray; color: black; font-size: 16px; padding: 5px;")
        back_button.clicked.connect(self.go_back)
        self.layout.addWidget(back_button)

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

    def go_back(self):
        """Go back to the previous page."""
        self.main_window.set_page(ProductListPage(self.main_window, self.username))

    def fetch_cart_items(self):
        """Fetch the cart items from the server and display them."""
        print(f"Fetching cart items for user {self.username}...")  # Debugging statement
        response = send_command("view_cart", {"username": self.username})
        if response["error"]:
            QMessageBox.warning(self, "Error", "Failed to fetch cart items.")
            return

        # Call the method to update the cart display
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

            # Display product information (name, quantity, price) in a bigger font
            product_label = QLabel(f"{name} x {quantity} - ${price * quantity:.2f}")
            product_label.setStyleSheet("font-size: 18px; font-weight: bold;")  # Larger font size

            # Remove button with "Remove" text and updated size
            remove_button = QPushButton("Remove")
            remove_button.setFixedSize(120, 35)  # Slightly larger size
            remove_button.setStyleSheet("""
                background-color: green; 
                color: white; 
                border-radius: 15px; 
                font-size: 16px; 
                padding: 5px 10px;
            """)
            remove_button.clicked.connect(lambda _, pid=product_id: self.remove_from_cart(pid))

            # Add the product label and remove button to the product layout
            product_layout.addWidget(product_label)
            product_layout.addStretch()  # Push the remove button to the right
            product_layout.addWidget(remove_button)

            # Set the layout for the product frame
            product_frame.setLayout(product_layout)

            # Add the product frame to the cart items layout
            self.cart_items_layout.addWidget(product_frame)

            # Update total price
            total_price += price * quantity

        # Update the total label
        self.total_label.setText(f"Total: ${total_price:.2f}")

    def remove_from_cart(self, product_id):
        """Remove an item from the cart."""
        print(f"Removing product {product_id} from cart...")  # Debugging statement
        response = send_command("remove_from_cart", {"username": self.username, "product_id": product_id})
        
        if response["error"]:
            QMessageBox.warning(self, "Error", "Failed to remove item from cart.")
            print("Error removing item:", response["content"])  # Debugging the error
            return
        
        print("Item removed successfully. Fetching updated cart...")  # Debugging statement
        self.fetch_cart_items()  # Refresh the cart after removal

    def checkout(self):
        """Clear the cart and display a success message."""
        response = send_command("checkout", {"username": self.username})
        if response["error"]:
            QMessageBox.warning(self, "Error", "Failed to complete checkout.")
            return

        QMessageBox.information(self, "Success", "Checkout successful!")
        # Refresh the cart after checkout
        self.fetch_cart_items()


class ChatPanel(QWidget):
    """Sliding chat panel with recent chats and full chat functionality."""
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
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
    
                # Check Online Status Button (on the left)
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
    
                # Chat Button (on the right)
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
                is_sent_by_current_user = (sender == current_user)
                
                self.add_chat_bubble(sender, message, is_sent_by_current_user)
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
        
    def listen_for_new_messages(self):
        """Continuously check for new messages and update the chat."""
        while True:
            if messages:
                new_message = messages.pop(0)
                sender = new_message["sender"]
                recipient = new_message["recipient"]
                content = new_message["message"]
                if recipient == self.current_user:  # Message meant for this user
                    self.add_chat_bubble(sender, content, is_user=False)
            time.sleep(0.1)
            
    def add_chat_bubble(self, sender, message, is_user):
        """Add a chat bubble to the chat history."""
        bubble_layout = QHBoxLayout()
        bubble_label = QLabel(message)
        bubble_label.setWordWrap(True)
        bubble_label.setFont(QFont("Arial", 12))
        bubble_label.setContentsMargins(10, 10, 10, 10)
        bubble_label.setFixedWidth(300)

        if is_user:
            bubble_label.setStyleSheet("""
                QLabel {
                    background-color: #dcf8c6;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble_label)
        else:
            bubble_label.setStyleSheet("""
                QLabel {
                    background-color: #ffffff;
                    border-radius: 15px;
                    padding: 10px;
                    border: 1px solid #ccc;
                }
            """)
            bubble_layout.addWidget(bubble_label)
            bubble_layout.addStretch()

        self.chat_content_layout.addLayout(bubble_layout)

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


    def send_message(self, sender, recipient):
        """Send a message to the recipient using their IP address and port."""
        message_text = self.message_input.text()
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
                        print("Connected")
                        message_data = {
                            "sender": sender,
                            "recipient": recipient,
                            "sent":True,
                            "message": message_text,
                            "time": time.time(),
                        }
                        temp_socket.send(json.dumps(message_data).encode('utf-8'))
                        self.add_chat_bubble(sender, message_text, True)
                        send_command("store_message", message_data)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")
            else:
                # Add the message to the database as pending
                message_data = {
                    "sender": sender,
                    "receiver": recipient,
                    "message": message_text,
                    "sent": False,
                    "time": time.time(),
                }
                self.add_chat_bubble(sender, message_text, True)
                send_command("store_message", message_data)
        else:
            QMessageBox.critical(self, "Error", "Failed to check online status.")
    
        # Clear the message input area after sending
        self.message_input.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique")
        self.setGeometry(300, 100, 400, 300)
        self.setStyleSheet(style)
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.container_layout = QVBoxLayout() 
        self.container.setLayout(self.container_layout)
        self.set_page(EntryPage(self))  

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

