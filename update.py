import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('appointments.db')
cursor = conn.cursor()

# Update the appointment table to replace NULL values with empty strings
cursor.execute('''
    UPDATE appointment
    SET name = COALESCE(name, ''),
        service = COALESCE(service, ''),
        time = COALESCE(time, ''),
        status = COALESCE(status, ''),
        booked_by = COALESCE(booked_by, '')
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("All NULL values in the appointment table have been replaced with empty strings.")