import os
import sqlite3
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file

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

@app.route('/api/get_reports', methods=['GET'])
def get_reports():
    conn = sqlite3.connect('pharmacy_control.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT branch, staff_name, log_type, details, timestamp FROM staff_logs ORDER BY id DESC LIMIT 50")
    staff = cursor.fetchall()
    
    cursor.execute("SELECT branch, trans_type, amount, category, comment, timestamp FROM finance ORDER BY id DESC LIMIT 50")
    finance = cursor.fetchall()
    
    conn.close()
    return jsonify({"staff": staff, "finance": finance})

@app.route('/api/export_excel', methods=['GET'])
def export_excel():
    conn = sqlite3.connect('pharmacy_control.db')
    
    df_staff = pd.read_sql_query("SELECT branch AS 'Филиал', staff_name AS 'Сотрудник', log_type AS 'Тип', details AS 'Детали', timestamp AS 'Дата' FROM staff_logs", conn)
    df_finance = pd.read_sql_query("SELECT branch AS 'Филиал', trans_type AS 'Тип', amount AS 'Сумма', category AS 'Категория', comment AS 'Комментарий', timestamp AS 'Дата' FROM finance", conn)
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_staff.to_excel(writer, sheet_name='Дисциплина', index=False)
        df_finance.to_excel(writer, sheet_name='Финансы', index=False)
        
    output.seek(0)
    return send_file(output, download_name="pharmacy_report.xlsx", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
