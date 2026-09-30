import sqlite3

connection = sqlite3.connect("database/agriconnect.db")

crops = connection.execute(
    "SELECT * FROM crop_listings"
).fetchall()

print("Crop Listings:")

for crop in crops:
    print(crop)

connection.close()