import sys
import sqlite3
from functions import*
from styleSheet import style
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QMessageBox
)

class EntryPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Store reference to MainWindow
        layout = QVBoxLayout()
        header = QLabel("AUBoutique")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
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
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
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
        
        self.setLayout(layout)

    def register(self):
        name = self.name_input.text()
        email = self.email_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        if name and email and username and password:
            try:
                register_user(name, email, username, password)
                QMessageBox.information(self, "Success", "Registration successful! Please log in.")
                self.main_window.set_page(EntryPage(self.main_window))
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Username already exists.")
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")

class LoginPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        header = QLabel("Login")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Ensure that self.password_input is correctly initialized
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit(self)  # Initialize password input
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide password characters
        
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.login)
        layout.addWidget(submit_button)
        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username and password:
            if validate_user(username, password):
                self.main_window.set_page(MainPage(self.main_window))
            else:
                QMessageBox.warning(self, "Error", "Invalid credentials")
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")

class MainPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        header = QLabel("Welcome to AUBoutique!")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)
        layout.addWidget(QLabel("Home page"))
        
        my_items_button = QPushButton("View my items")
        my_items_button.clicked.connect(self.view_my_items)
        layout.addWidget(my_items_button)
        browse_button = QPushButton("Browse items")
        browse_button.clicked.connect(self.go_to_shop)
        layout.addWidget(browse_button)
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.go_to_entry)
        layout.addWidget(logout_button)
        self.setLayout(layout)
        
    def view_my_items(self):
        self.main_window.set_page(MyItemsPage(self.main_window))
    def go_to_shop(self):
        self.main_window.set_page(ShopPage(self.main_window))
    def go_to_entry(self):
        self.main_window.set_page(EntryPage(self.main_window))

class MyItemsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        header = QLabel("My Products")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)

        self.product_list = QLabel("Your products will be displayed here.")  #todo
        layout.addWidget(self.product_list)

        add_product_button = QPushButton("Add Product")
        add_product_button.clicked.connect(self.add_product)
        layout.addWidget(add_product_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

class AddProductPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        header = QLabel("Add Product")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Product Name")
        self.description_input = QLineEdit(self)
        self.description_input.setPlaceholderText("Description")
        self.price_input = QLineEdit(self)
        self.price_input.setPlaceholderText("Price")
        layout.addWidget(self.name_input)
        layout.addWidget(self.description_input)
        layout.addWidget(self.price_input)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_product)
        layout.addWidget(submit_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def add_product(name, description, price, owner_username):
        conn = sqlite3.connect('auboutique.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (name, description, price, owner_username)
            VALUES (?, ?, ?, ?)
        """, (name, description, price, owner_username))
        conn.commit()
        conn.close()

def get_products_by_owner(owner_username):
    conn = sqlite3.connect('auboutique')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, name, description, price, buyer_username
        FROM Products
        WHERE owner_username = ?
    """, (owner_username,))
    products = cursor.fetchall()
    conn.close()
    return products
    def go_back(self):
        self.main_window.set_page(MyItemsPage(self.main_window))
        
class ShopPage():
    print("todo")
    
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
        # Remove the previous widget from layout
        if self.container_layout.count() > 0:
            widget = self.container_layout.itemAt(0).widget()
            if widget:
                widget.setParent(None)  # Remove the widget from the layout
        self.container_layout.addWidget(page) # Add the new widget (page) to the layout
        page.show()  # Ensure the new page is shown


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
