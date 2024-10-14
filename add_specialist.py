import sqlite3

# Function to add a new specialist
def add_specialist(name, service, time):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        # Insert a new specialist with the specified slot and service type
        cursor.execute('''
            INSERT INTO appointment (name, service, time, status, booked_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, service, time, 'Free', ''))

        # Commit the changes and close the connection
        conn.commit()

        print(f"Specialist {name} added with a {time} slot for {service} service.")
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# Example usage to add Adam at 8 PM for Premium service
add_specialist('Adam', 'Premium', '20:00')
