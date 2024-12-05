from PyQt5.QtWidgets import (
    QApplication, QComboBox, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QScrollArea, QFrame, QInputDialog, QMessageBox, QLineEdit, QMenu, QListWidget, QListWidgetItem, QTextEdit 
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon
import sqlite3


class ProductWidget(QFrame):
    """Widget to display a single product as a box with border."""
    def __init__(self, product_id, name, description, price, owner, rating, quantity, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.name = name
        self.description = description
        self.original_price = price  # Store the original USD price
        self.price = price  # Current price (updated with currency)
        self.owner = owner
        self.rating = rating
        self.quantity = quantity
        self.currency_symbol = "$"

        # Set QFrame styling to look like a box
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 10px;
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

        # Create labels
        name_label = QLabel(f"Name: {self.name}")
        description_label = QLabel(f"Description: {self.description}")
        self.price_label = QLabel(f"Price: {self.currency_symbol}{self.price:.2f}")
        owner_label = QLabel(f"Owner: {self.owner}")
        rating_label = QLabel(f"Rating: {self.rating:.1f} ★")
        quantity_label = QLabel(f"Quantity: {self.quantity}")

        # Add labels to the details layout
        details_layout.addWidget(name_label)
        details_layout.addWidget(description_label)
        details_layout.addWidget(self.price_label)
        details_layout.addWidget(owner_label)
        details_layout.addWidget(rating_label)
        details_layout.addWidget(quantity_label)

        layout.addLayout(details_layout)

        # Right: Buy and Rate buttons
        buttons_layout = QVBoxLayout()

        buy_button = QPushButton("Buy")
        buy_button.setFixedSize(100, 30)
        buy_button.clicked.connect(self.buy_product)
        buttons_layout.addWidget(buy_button)

        rate_button = QPushButton("Rate")
        rate_button.setFixedSize(100, 30)
        rate_button.clicked.connect(self.rate_product)
        buttons_layout.addWidget(rate_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def update_price(self, exchange_rate, symbol):
        """Update the displayed price using the original USD price."""
        self.price = round(self.original_price * exchange_rate, 2)  # Convert using the original USD price
        self.currency_symbol = symbol
        self.price_label.setText(f"Price: {self.currency_symbol}{self.price:.2f}")

    def buy_product(self):
        if self.quantity > 0:
            conn = sqlite3.connect("auboutique.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products
                SET quantity = quantity - 1
                WHERE product_id = ? AND quantity > 0
            """, (self.product_id,))
            conn.commit()
            conn.close()

            self.quantity -= 1
            self.update_quantity_display()
        else:
            QMessageBox.warning(self, "Out of Stock", f"The product '{self.name}' is out of stock!")

    def update_quantity_display(self):
        """Update the displayed quantity in the UI."""
        details_layout = self.layout().itemAt(0).layout()
        quantity_label = details_layout.itemAt(details_layout.count() - 1).widget()
        quantity_label.setText(f"Quantity: {self.quantity}")

    def rate_product(self):
        rating, ok = QInputDialog.getInt(self, "Rate Product", "Enter your rating (1-5):", min=1, max=5)
        if ok:
            conn = sqlite3.connect("auboutique.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products
                SET average_rating = (average_rating * review_count + ?) / (review_count + 1),
                    review_count = review_count + 1
                WHERE product_id = ?
            """, (rating, self.product_id))
            conn.commit()

            cursor.execute("SELECT average_rating FROM products WHERE product_id = ?", (self.product_id,))
            self.rating = cursor.fetchone()[0]
            conn.close()
            self.update_rating_display()

    def update_rating_display(self):
        details_layout = self.layout().itemAt(0).layout()
        rating_label = details_layout.itemAt(details_layout.count() - 2).widget()
        rating_label.setText(f"Rating: {self.rating:.1f} ★")


class ProductListPage(QWidget):
    """Page to display a scrollable list of product boxes with additional features."""
    def __init__(self, username):
        super().__init__()
        self.username = username  # Store the logged-in username
        self.current_currency = "USD"  # Default currency
        self.exchange_rates = self.fetch_exchange_rates()
        self.currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}

        # Main layout
        main_layout = QVBoxLayout(self)

        # --- HEADER LAYOUT ---
        header_layout = QHBoxLayout()

        # Username button with dropdown menu
        self.username_button = QPushButton(self.username)
        self.username_button.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        menu = QMenu()
        menu.addAction("My Products")
        menu.addAction("Add Product")
        self.username_button.setMenu(menu)
        header_layout.addWidget(self.username_button)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for products...")
        self.search_bar.textChanged.connect(self.filter_products)  # Connect to filtering function
        header_layout.addWidget(self.search_bar, stretch=2)

        # Currency selector
        self.currency_selector = QComboBox()
        self.currency_selector.addItems(["USD", "EUR", "GBP", "JPY", "INR"])
        self.currency_selector.setCurrentText("USD")
        self.currency_selector.currentTextChanged.connect(self.update_currency)
        header_layout.addWidget(self.currency_selector)

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
        products = self.fetch_products()
        for product in products:
            product_id, name, description, price, owner, rating, quantity = product
            product_widget = ProductWidget(product_id, name, description, price, owner, rating, quantity)
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
        self.chat_panel = ChatPanel(self)
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
        self.chat_button.update()  # Force repaint

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

    def fetch_products(self):
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
        return products

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


class ChatPanel(QWidget):
    """Sliding chat panel with recent chats and full chat functionality."""
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.chat_area_widget = self.build_chat_area_view()

        # Start with the recent chats visible
        self.chat_area_widget.setVisible(False)

        self.main_layout.addWidget(self.recent_chats_widget)
        self.main_layout.addWidget(self.chat_area_widget)

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
        self.recent_chats_list.addItem("Owner 1")
        self.recent_chats_list.addItem("Owner 2")
        self.recent_chats_list.addItem("Owner 3")
        self.recent_chats_list.itemClicked.connect(self.load_chat)
        layout.addWidget(self.recent_chats_list)

        return widget

    def build_chat_area_view(self):
        """Build the chat area view."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Chat header with back button and owner name
        chat_header_layout = QHBoxLayout()
        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self.show_recent_chats)
        chat_header_layout.addWidget(self.back_button)

        self.chat_owner_label = QLabel("Chat with [Owner]")
        self.chat_owner_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        chat_header_layout.addWidget(self.chat_owner_label)

        chat_header_layout.addStretch()  # Push the label to the left
        layout.addLayout(chat_header_layout)

        # Chat history (scrollable area)
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_content = QLabel()  # Display previous messages
        self.chat_content.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Allow selection of text
        self.chat_content.setStyleSheet("padding: 10px; font-size: 14px;")
        self.chat_history.setWidget(self.chat_content)
        layout.addWidget(self.chat_history)

        # Message input area
        input_layout = QHBoxLayout()

        # Text box for entering messages
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input, stretch=2)

        # Send button
        self.send_button = QPushButton("➤")
        self.send_button.setFixedSize(40, 40)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        # Audio and photo buttons
        self.audio_button = QPushButton()
        self.audio_button.setIcon(QIcon("audio_icon.png"))  # Replace with actual audio icon path
        self.audio_button.setFixedSize(40, 40)
        input_layout.addWidget(self.audio_button)

        self.photo_button = QPushButton()
        self.photo_button.setIcon(QIcon("photo_icon.png"))  # Replace with actual photo icon path
        self.photo_button.setFixedSize(40, 40)
        input_layout.addWidget(self.photo_button)

        layout.addLayout(input_layout)

        return widget

    def filter_chats(self):
        """Filter the recent chats based on the search text."""
        search_text = self.search_bar.text().lower()
        for i in range(self.recent_chats_list.count()):
            item = self.recent_chats_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def show_recent_chats(self):
        """Show the recent chats list and hide the chat area."""
        self.chat_area_widget.setVisible(False)
        self.recent_chats_widget.setVisible(True)
        self.parent().update_chat_button_position()  # Ensure button is updated

    def load_chat(self, item):
        """Load the selected chat's history."""
        self.recent_chats_widget.setVisible(False)
        self.chat_area_widget.setVisible(True)
        self.parent().update_chat_button_position()  # Ensure button is updated

    def send_message(self):
        """Send a new message."""
        message = self.message_input.text()
        if message:
            # Append the message to the chat content
            current_text = self.chat_content.text()
            new_text = f"{current_text}\nYou: {message}"
            self.chat_content.setText(new_text)

            # Clear the input box
            self.message_input.clear()


class AUBoutiqueApp(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("AUBoutique")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the product list page
        self.product_list_page = ProductListPage(username)
        self.setCentralWidget(self.product_list_page)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    username = "JohnDoe"  # Replace with the actual logged-in username
    main_window = AUBoutiqueApp(username)
    main_window.show()

    sys.exit(app.exec_())
