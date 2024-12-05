from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget, QListWidget
import sqlite3

class AddItemDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Add Item")
        self.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name")
        layout.addWidget(self.name_input)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description")
        layout.addWidget(self.description_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")
        layout.addWidget(self.price_input)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        layout.addWidget(self.quantity_input)

        submit_button = QPushButton("Add Item")
        submit_button.clicked.connect(self.add_item_to_db)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def add_item_to_db(self):
        name = self.name_input.text()
        description = self.description_input.text()
        price = self.price_input.text()
        quantity = self.quantity_input.text()

        if name and description and price and quantity:
            try:
                conn = sqlite3.connect("auboutique.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO products (name, description, price, quantity, owner_username)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, description, price, quantity, self.username))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", "Item added successfully!")
                self.close()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add item: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")


class ViewMyItemsPage(QWidget):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        header = QLabel(f"Items owned by {self.username}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        self.layout.addWidget(header)

        self.items_list = QListWidget()
        self.layout.addWidget(self.items_list)

        self.load_items()
        self.setLayout(self.layout)

    def load_items(self):
        conn = sqlite3.connect("auboutique.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, description, price, quantity
            FROM products
            WHERE owner_username = ?
        """, (self.username,))
        items = cursor.fetchall()
        conn.close()

        for item in items:
            self.items_list.addItem(f"Name: {item[0]}, Description: {item[1]}, Price: {item[2]}, Quantity: {item[3]}")
