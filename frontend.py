from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Connect to your SQLite database and fetch data
def get_data():
    conn = sqlite3.connect('appointments.db')  # Replace with your SQLite file
    cursor = conn.cursor()
    
    # Fetch all data from your table (replace 'your_table' with your table name)
    cursor.execute('SELECT * FROM appointment')
    rows = cursor.fetchall()
    
    conn.close()
    return rows

@app.route('/')
def index():
    data = get_data()
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
