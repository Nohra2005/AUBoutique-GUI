import sys
import sqlite3
from functions import *
from socket import *
import json
import threading
import time
from gui import *


from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QMessageBox
)

from PyQt5.QtCore import Qt


client = socket(AF_INET, SOCK_STREAM)
client.connect(('localhost', 8888))

responses=[]
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
            if response.get("status") == "success":
                QMessageBox.information(self, "Success", "Registration successful! Please login.")
                self.main_window.set_page(EntryPage(self.main_window))
        else:
            QMessageBox.critical(self, "Error", response.get("message", "Registration failed"))
        
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
            if response.get("status") == "success":
                QMessageBox.information(self, "Success", "Login successful!")
                self.parent().username = username  # Store logged-in username
                self.main_window.set_page(ProductListPage(self.main_window))
            else:
                QMessageBox.critical(self, "Error", response.get("message", "Invalid credentials."))
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")


    def go_back(self):
        self.main_window.set_page(EntryPage(self.main_window))

