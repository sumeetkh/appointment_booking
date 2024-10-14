import sqlite3
import pandas as pd

# Load the CSV file
csv_file_path = '/Users/sumeetk/Downloads/appointments_schedule_with_booked_by.csv'
df = pd.read_csv(csv_file_path)

# Replace empty strings with NULL (NaN in pandas)
df.replace("", pd.NA, inplace=True)

# Connect to the SQLite database
conn = sqlite3.connect('appointments.db')
cursor = conn.cursor()

# Drop the existing appointment table if it exists
cursor.execute('''
    DROP TABLE IF EXISTS appointment
''')

# Create a new table based on the columns from the CSV file
cursor.execute('''
    CREATE TABLE appointment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        service TEXT,
        time TEXT,
        status TEXT,
        booked_by TEXT
    )
''')

# Insert the data from the CSV into the SQLite table, handling NULL values
for _, row in df.iterrows():
    cursor.execute('''
        INSERT INTO appointment (name, service, time, status, booked_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (row['Name'], row['Service'], row['Time'], row['Status'], row['Booked By']))

# Commit and close the connection
conn.commit()
conn.close()

print("Appointment table created from the CSV file with NULLs inserted where applicable.")