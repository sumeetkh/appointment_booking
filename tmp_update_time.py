import sqlite3

# Function to update the time of an appointment for a specific specialist, service, and time
def update_appointment_time(specialist_name, service_type, old_slot_time, new_slot_time):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        # SQL command to update the time of the specific appointment
        cursor.execute('''
            UPDATE appointment
            SET time = ?
            WHERE name = ? AND service = ? AND time = ?
        ''', (new_slot_time, specialist_name, service_type, old_slot_time))

        # Check if any rows were affected
        if cursor.rowcount == 0:
            print(f"No appointment found for {specialist_name} at {old_slot_time} providing {service_type} service.")
        else:
            print(f"Appointment for {specialist_name} providing {service_type} service has been updated to {new_slot_time}.")

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
    old_slot_time = '16:00'
    new_slot_time = '14:00'
    update_appointment_time(specialist_name, service_type, old_slot_time, new_slot_time)
