import sqlite3

def register_user(name, email, username, password):
    conn = sqlite3.connect('auboutique.db')
    cursor = conn.cursor()
    # Insert the new user into the database
    cursor.execute('''INSERT INTO users (name, email, username, password) 
                      VALUES (?, ?, ?, ?)''', (name, email, username, password))
    
    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = sqlite3.connect('auboutique.db')
    cursor = conn.cursor()

    # Check if the username exists in the database and if the password matches
    cursor.execute('''SELECT * FROM users WHERE username = ? AND password = ?''', (username, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        return True
    else:
        return False



