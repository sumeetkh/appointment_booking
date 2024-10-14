import sqlite3

# Function to delete an appointment for a specific specialist, service, and time
def delete_appointment(specialist_name, service_type, slot_time):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        # SQL command to delete the specific appointment
        cursor.execute('''
            UPDATE appointment
            SET status = 'Free', booked_by = ''
            WHERE name = ? AND service = ? AND time = ?
        ''', (specialist_name, service_type, slot_time))

        # Check if any rows were affected
        if cursor.rowcount == 0:
            print(f"No appointment found for {specialist_name} at {slot_time} providing {service_type} service.")
        else:
            print(f"Appointment for {specialist_name} at {slot_time} providing {service_type} service has been removed.")

        # Commit the changes and close the connection
        conn.commit()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    specialist_name = 'Daniel'
    service_type = 'Premium'
    slot_time = '14:00'
    delete_appointment(specialist_name, service_type, slot_time)
