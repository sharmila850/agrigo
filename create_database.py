import sqlite3

connection = sqlite3.connect("database/agriconnect.db")

connection.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    location TEXT NOT NULL,
    role TEXT NOT NULL
)
""")
connection.execute("""
CREATE TABLE IF NOT EXISTS crop_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    crop_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    quality TEXT NOT NULL,
    expected_price REAL NOT NULL,
    location TEXT NOT NULL,
    harvest_date TEXT NOT NULL,
    available_date TEXT NOT NULL,
    image TEXT,
    FOREIGN KEY (farmer_id) REFERENCES users(id)
)
""")
connection.execute("""
CREATE TABLE IF NOT EXISTS buyer_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER NOT NULL,
    crop_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    max_price REAL NOT NULL,
    quality TEXT NOT NULL,
    location TEXT NOT NULL,
    required_date TEXT NOT NULL,
    FOREIGN KEY (buyer_id) REFERENCES users(id)
)
""")
connection.commit()
connection.close()

print("Users table created successfully!")