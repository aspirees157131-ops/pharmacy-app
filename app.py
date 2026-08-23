import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('pharmacy_control.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS staff_logs 
                      (id INTEGER PRIMARY KEY, branch INTEGER, staff_name TEXT, log_type TEXT, details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS finance 
                      (id INTEGER PRIMARY KEY, branch INTEGER, trans_type TEXT, amount REAL, category TEXT, comment TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add_staff_log', methods=['POST'])
def add_staff_log():
    data = request.json
    conn = sqlite3.connect('pharmacy_control.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO staff_logs (branch, staff_name, log_type, details) VALUES (?, ?, ?, ?)",
                   (data['branch'], data['staff_name'], data['log_type'], data['details']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/add_finance', methods=['POST'])
def add_finance():
    data = request.json
    conn = sqlite3.connect('pharmacy_control.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO finance (branch, trans_type, amount, category, comment) VALUES (?, ?, ?, ?, ?)",
                   (data['branch'], data['trans_type'], data['amount'], data['category'], data['comment']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
