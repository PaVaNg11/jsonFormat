import sqlite3

conn=sqlite3.connect("TEST_JSON.db")

cursor=conn.cursor()



# cursor.execute("""
# CREATE TABLE IF NOT EXISTS table2 (
#                id INTEGER PRIMARY KEY,
#                name TEXT NOT NULL,
#                age INTEGER
#                )
# """)


# cursor.execute("INSERT INTO table1 (id,name,age) VALUES (?,?,?)",(1,"pavan",22))
# conn.commit()



# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# tables=cursor.fetchall()

# for table in tables:
#     print(table[0])
# cursor.execute("SELECT * FROM table2")
# rows = cursor.fetchall()
    
# print(rows)
cursor.execute("DELETE FROM table2;")
conn.commit()
print("DELETED")
