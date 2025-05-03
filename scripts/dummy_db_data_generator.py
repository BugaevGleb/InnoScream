import json
import sqlite3
from datetime import datetime
from pathlib import Path

sqlite3.register_adapter(dict, lambda d: json.dumps(d).encode("utf8"))

conn = sqlite3.connect(Path(__file__).parent.parent / "db.sqlite3")
cursor = conn.cursor()

print("Deleting user_messages and reactions table data.", end=" ")
print("Press Enter to continue...")
input()
cursor.execute("DELETE FROM user_messages")
cursor.execute("DELETE FROM reactions")
conn.commit()

print("Inserting data into user_messages table...")
for i in range(300):
    cursor.execute(
        "INSERT INTO user_messages VALUES (?, ?, ?, ?)",
        (i, i, f"test_{i}", datetime.now()),
    )
conn.commit()

print("Rows in user_messages table: ", end="")
cursor.execute("SELECT count(*) FROM user_messages")
print(cursor.fetchone()[0])

print("Inserting data into reactions table...")
for i in range(300):
    cursor.execute(
        "INSERT INTO reactions VALUES (?, ?, ?)",
        (i, datetime.now(), {f"test_{j}": j for j in range(3)}),
    )
conn.commit()

print("Rows in reactions table: ", end="")
cursor.execute("SELECT count(*) FROM reactions")
print(cursor.fetchone()[0])

conn.close()
