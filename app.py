import os
import io
import sqlite3
from flask import Flask, render_template, request, jsonify
import telebot
from telebot import types
import openpyxl

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch INTEGER,
            staff_name TEXT,
            log_type TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch INTEGER,
            trans_type TEXT,
            amount REAL,
            category TEXT,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add_staff_log', methods=['POST'])
def add_staff_log():
    data = request.json or {}
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO staff_logs (branch, staff_name, log_type, details) VALUES (?, ?, ?, ?)',
        (data.get('branch'), data.get('staff_name'), data.get('log_type'), data.get('details'))
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/add_finance', methods=['POST'])
def add_finance():
    data = request.json or {}
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO finance_logs (branch, trans_type, amount, category, comment) VALUES (?, ?, ?, ?, ?)',
        (data.get('branch'), data.get('trans_type'), data.get('amount'), data.get('category'), data.get('comment'))
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/get_reports', methods=['GET'])
def get_reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT branch, staff_name, log_type, details, timestamp FROM staff_logs ORDER BY id DESC LIMIT 15')
    staff = cursor.fetchall()
    cursor.execute('SELECT branch, trans_type, amount, category, comment, timestamp FROM finance_logs ORDER BY id DESC LIMIT 15')
    finance = cursor.fetchall()
    conn.close()
    return jsonify({'staff': staff, 'finance': finance})

@app.route('/api/send_excel_telegram', methods=['POST'])
def send_excel_telegram():
    data = request.json or {}
    chat_id = data.get('chat_id')
    
    if not chat_id or not bot:
        return jsonify({'status': 'error', 'message': 'Chat ID or Bot instance missing'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT timestamp, branch, staff_name, log_type, details FROM staff_logs ORDER BY id DESC')
    staff_rows = cursor.fetchall()

    cursor.execute('SELECT timestamp, branch, trans_type, amount, category, comment FROM finance_logs ORDER BY id DESC')
    finance_rows = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    
    # Вкладка 1: Дисциплина
    ws1 = wb.active
    ws1.title = "Дисциплина и Кадры"
    ws1.append(["Дата и Время", "Филиал №", "Сотрудник", "Тип записи", "Детали"])
    for row in staff_rows:
        ws1.append(list(row))

    # Вкладка 2: Финансы
    ws2 = wb.create_sheet(title="Финансы и Акции")
    ws2.append(["Дата и Время", "Филиал №", "Тип операции", "Сумма", "Категория", "Комментарий"])
    for row in finance_rows:
        ws2.append(list(row))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    try:
        bot.send_document(
            chat_id,
            ('Pharmacy_Report.xlsx', output.getvalue()),
            caption="📊 **Ваш актуальный Excel отчёт**"
        )
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    if bot:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    return 'ok', 200

@bot.message_handler(commands=['start']) if bot else None
def send_welcome(message):
    web_app_url = os.environ.get('WEB_APP_URL', 'https://pharmacy-app.onrender.com')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Панель управления", web_app_url=types.WebAppInfo(url=web_app_url)))
    bot.reply_to(message, "Привет! Нажмите кнопку ниже для открытия панели управления:", reply_markup=markup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
