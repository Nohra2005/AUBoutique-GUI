from PyQt5.QtWidgets import (
    QApplication, QComboBox, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QScrollArea, QFrame, QInputDialog, QMessageBox, QLineEdit, QMenu
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
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
        content_layout = QHBoxLayout()

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
        
        content_layout.addWidget(scroll_area, stretch=2)

         # Chat toggle button
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
        content_layout.addWidget(self.chat_button, alignment=Qt.AlignVCenter)

        main_layout.addLayout(content_layout)

        # Chat panel
        self.chat_panel = ChatPanel(self)
        self.chat_panel.setGeometry(800, 0, 0, 600)  # Initially hidden
        self.chat_animation = QPropertyAnimation(self.chat_panel, b"geometry")

        self.setLayout(main_layout)


    def toggle_chat_panel(self):
        """Slide the chat panel in and out."""
        if self.chat_panel.width() == 0:  # Slide in
            self.chat_animation.setStartValue(QRect(self.width(), 0, 0, self.height()))
            self.chat_animation.setEndValue(QRect(self.width() - 270, 0, 270, self.height()))
            self.chat_button.setText("▶")
        else:  # Slide out
            self.chat_animation.setStartValue(QRect(self.width() - 270, 0, 270, self.height()))
            self.chat_animation.setEndValue(QRect(self.width(), 0, 0, self.height()))
            self.chat_button.setText("◀")

        self.chat_animation.setDuration(300)
        self.chat_animation.valueChanged.connect(self.update_chat_button_position)  # Update position dynamically
        self.chat_animation.start()

    def update_chat_button_position(self):
        """Update the chat button position to align with the chat panel."""
        button_y = self.height() // 2 - self.chat_button.height() // 2
        if self.chat_panel.width() == 0:  # Chat panel is hidden
            button_x = self.width() - self.chat_button.width()
        else:  # Chat panel is visible
            button_x = self.width() - self.chat_panel.width() - self.chat_button.width()

        self.chat_button.move(button_x, button_y)


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
    """Sliding chat panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #f1f1f1;
                border-left: 1px solid #ccc;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Chat Area"))
        self.setLayout(layout)


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
