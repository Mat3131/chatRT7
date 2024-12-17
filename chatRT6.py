import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
import random

# Connessione al database
conn = sqlite3.connect('chat_app.db')
cursor = conn.cursor()

# Creazione delle tabelle nel database (se non esistono)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    user_id INTEGER UNIQUE NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS contacts (
    user_id INTEGER,
    contact_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(contact_id) REFERENCES users(user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(id),
    FOREIGN KEY(receiver_id) REFERENCES users(id)
)
''')
conn.commit()

# Funzione per registrare un nuovo utente
def register_user(username, password):
    user_id = random.randint(10000, 99999)
    cursor.execute('''
    INSERT INTO users (username, password, user_id) 
    VALUES (?, ?, ?)
    ''', (username, password, user_id))
    conn.commit()
    return user_id

# Funzione per il login
def login_user(username, password):
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    if user:
        return user
    else:
        return None

# Funzione per aprire la finestra di login
def open_login_window():
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()

        user = login_user(username, password)
        if user:
            user_id = user[3]
            messagebox.showinfo("Login", "Login successful!")
            login_window.destroy()
            open_main_window(user_id)
        else:
            # Se l'utente non esiste, lo registriamo
            user_id = register_user(username, password)
            messagebox.showinfo("Register", f"User created! Your user ID: {user_id}")
            login_window.destroy()
            open_main_window(user_id)

    login_window = tk.Tk()
    login_window.title("Login")

    tk.Label(login_window, text="Username:").pack()
    username_entry = tk.Entry(login_window)
    username_entry.pack()

    tk.Label(login_window, text="Password:").pack()
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack()

    tk.Button(login_window, text="Login", command=handle_login).pack()

    login_window.mainloop()

# Funzione per la schermata principale (contatti)
def open_main_window(user_id):
    def update_contacts():
        # Recupera solo i contatti che sono stati aggiunti
        cursor.execute('''
        SELECT u.username, u.user_id FROM users u 
        JOIN contacts c ON u.user_id = c.contact_id 
        WHERE c.user_id = ?
        ''', (user_id,))
        contacts = cursor.fetchall()
        
        for widget in contacts_frame.winfo_children():
            widget.destroy()

        if not contacts:
            tk.Label(contacts_frame, text="No contacts found. Add a contact!").pack()

        for contact in contacts:
            tk.Button(contacts_frame, text=contact[0], command=lambda id=contact[1]: open_chat_window(user_id, id)).pack()

    def add_contact():
        contact_id = simpledialog.askstring("Add Contact", "Enter the contact's ID:")
        cursor.execute('SELECT * FROM users WHERE user_id=?', (contact_id,))
        contact = cursor.fetchone()

        if contact:
            cursor.execute('INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)', (user_id, contact_id))
            conn.commit()
            messagebox.showinfo("Success", "Contact added!")
            update_contacts()
        else:
            messagebox.showerror("Error", "Contact not found!")

    main_window = tk.Tk()
    main_window.title("Contacts")

    contacts_frame = tk.Frame(main_window)
    contacts_frame.pack()

    update_contacts()

    tk.Button(main_window, text="Add Contact", command=add_contact).pack()

    main_window.mainloop()

# Funzione per la chat privata
def open_chat_window(user_id, contact_id):
    window = tk.Tk()
    window.title("Chat")

    messages_box = tk.Text(window)
    messages_box.pack()

    def update_messages():
        cursor.execute('''
        SELECT m.sender_id, m.message, u.username FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?)
        ORDER BY m.timestamp
        ''', (user_id, contact_id, contact_id, user_id))
        messages = cursor.fetchall()

        messages_box.delete(1.0, tk.END)
        for message in messages:
            sender = message[2]  # Nome utente
            text = message[1]    # Messaggio
            messages_box.insert(tk.END, f"{sender}: {text}\n")
        
        window.after(2000, update_messages)

    update_messages()

    def send_message():
        message = message_entry.get()
        if message:
            cursor.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)', (user_id, contact_id, message))
            conn.commit()
            message_entry.delete(0, tk.END)

    message_entry = tk.Entry(window)
    message_entry.pack()

    send_button = tk.Button(window, text="Send", command=send_message)
    send_button.pack()

    window.mainloop()

# Avvio dell'applicazione
if __name__ == "__main__":
    open_login_window()
