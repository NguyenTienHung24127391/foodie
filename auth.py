# auth.py
from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

auth_bp = Blueprint('auth', __name__)
DATABASE = 'users.db'

# Hàm tạo database user (chạy 1 lần đầu)
def init_user_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

# ========== ĐĂNG KÝ ==========
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Thiếu thông tin!'}), 400

    hashed = generate_password_hash(password)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, hashed))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username hoặc email đã tồn tại!'}), 400
    conn.close()

    return jsonify({'message': 'Đăng ký thành công!'}), 201

# ========== ĐĂNG NHẬP ==========
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):  # ✅ đúng cột
            session['username'] = username
            return redirect(url_for('home'))  # ✅ chuyển về home.html
        else:
            return render_template('login.html', error='Sai tên đăng nhập hoặc mật khẩu!')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))