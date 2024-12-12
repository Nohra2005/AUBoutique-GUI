# AUBoutique - GUI Edition

## Project Description
AUBoutique is an online marketplace tailored for the AUB community, providing a platform for buying and selling products. Initially developed as a simple marketplace in Phase I, it has evolved into a feature-rich platform with a graphical user interface (GUI), peer-to-peer messaging, and advanced functionalities in Phase II.

---

## Features

### Core Features (Phase I & II)
- **Account Management**: User registration and login.
- **Product Management**: Add, view, and modify product listings.
- **Shopping Cart**: Add products to a cart and checkout.
- **Search Functionality**: Search for products by name or owner.
- **Currency Conversion**: Real-time exchange rates for multiple currencies (e.g., USD, EUR).
- **Product Ratings**: Users can rate products and view average ratings.
- **Peer-to-Peer Messaging**: Direct communication between users.
- **Notifications**: Alerts for product updates or new additions by followed owners.

### Creative Features
- **Follow Feature**: Follow specific owners to receive updates.
- **Offline Messaging**: Messages are queued and delivered once users are online.
- **Custom GUI**: Built using PyQt for a rich user experience.

---

## System Architecture

### Overview
The system follows a hybrid client-server and peer-to-peer architecture:

- **Client**: A PyQt-based GUI that manages user interactions and sends commands to the server.
- **Server**: A Python-based server handling multiple clients through multi-threading.
- **Database**: SQLite database for managing users, products, carts, ratings, and messages.

### Protocol
Communication between the client and server uses JSON-formatted messages over TCP. Key commands include:
- `register`: User registration.
- `login`: User authentication.
- `add_product`: Add new product listings.
- `view_products`: Retrieve product listings.
- `add_to_cart`: Add items to the shopping cart.
- `checkout`: Complete a purchase.
- `rate`: Submit product ratings.
- `search`: Filter products.
- `toggle_follow`: Follow/unfollow a user.

---

## Project Structure

```
AUBoutique/
├── server.py            # Server-side code handling requests and multi-threading
├── gui.py               # Client-side GUI implementation using PyQt
├── functions.py         # Core server logic and database operations
├── auboutique.db        # SQLite database
├── README.md            # Project documentation
├── test.jpg             # GUI assets
├── AUBoutique_Project_Report.pdf  # Project report with details on Phases I & II
```

---

## How to Run

### Prerequisites
- Python 3.8 or higher
- Required libraries: `PyQt5`, `sqlite3`, `socket`, `json`, `requests`
- Requests and wifi needed for the live currency exchange rates
- Install dependencies using:
  ```bash
  pip install PyQt5 requests
  ```

### Steps
1. Start the server:
   ```bash
   python server.py
   ```
2. Run the client:
   ```bash
   python gui.py
   ```
3. Use the GUI to interact with the marketplace.

---

## Database Schema
- **Users Table**: Stores user credentials and profiles.
- **Products Table**: Tracks product details (name, description, price, owner).
- **Cart Table**: Stores cart items for each user.
- **Subscribed Owners Table**: Stores the usernames of all owners a user is following.
- **Product Buyers Table**: Tracks which users bought which products.
- **Messages Table**: Manages peer-to-peer communications.
- **Ratings Table**: Records product ratings and calculates averages.
- **Carts Table**: Stores serialized cart information for each user.

---

## Deliverables
- **Source Code**: Available in this repository.
- **Project Report**: Documents the system architecture, protocol, and features.
- **Demo Video**: Showcases the application's functionalities.

---

## Team Members
- **Joey Saade** (202305993, jhs15@mail.aub.edu) - 33.33%
- **Tatiana Nohra** (202400396, tsn08@mail.aub.edu) - 33.33%
- **Christophe El Chabab** (202401778, cge24@mail.aub.edu) - 33.34%

---

## References
- `AUBoutique_Project_Report.pdf`: Detailed project report.
