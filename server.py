from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# === ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            token TEXT UNIQUE,
            ip TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# === 📌 РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ===
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    telegram_id = data.get("telegram_id")
    token = data.get("token")
    ip = request.remote_addr  # Автоматически получаем IP

    if not telegram_id or not token:
        return jsonify({"error": "telegram_id и token обязательны"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем, есть ли уже запись с таким Telegram ID
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"error": "Этот Telegram ID уже зарегистрирован"}), 400

    # Записываем в базу
    cursor.execute("INSERT INTO users (telegram_id, token, ip) VALUES (?, ?, ?)", (telegram_id, token, ip))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Пользователь зарегистрирован", "ip": ip}), 201

# === 📌 ПРОВЕРКА ТОКЕНА ПРИ УСТАНОВКЕ ===
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    telegram_id = data.get("telegram_id")
    token = data.get("token")
    ip = request.remote_addr  # IP пользователя

    if not telegram_id or not token:
        return jsonify({"error": "telegram_id и token обязательны"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE telegram_id = ? AND token = ?", (telegram_id, token))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Неверный токен или Telegram ID"}), 403

    # Если IP не совпадает с зарегистрированным, блокируем установку
    if user[3] and user[3] != ip:
        return jsonify({"error": "IP-адрес не совпадает с зарегистрированным"}), 403

    return jsonify({"success": True, "message": "Токен подтверждён"}), 200

# === 📌 ЗАПУСК СЕРВЕРА ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
