import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()


# Update chat_id to 3 for all rows
update_query = "UPDATE users SET chat_id = 3"

try:
    cursor.execute(update_query)
    conn.commit()
    print("All chat_id values updated to 3 successfully.")
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connection
    conn.close()
