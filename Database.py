import sqlite3

# Connect to the database
conn = sqlite3.connect("room_locator.db")
cursor = conn.cursor()

# Fetch all records from the users table
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

# Print the data
if rows:
    print("ID | Name | Room Number")
    print("-" * 30)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]}")
else:
    print("No data found in the users table.")

# Close the connection
conn.close()
