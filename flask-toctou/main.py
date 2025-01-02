from functools import wraps
import sqlite3
import datetime
import os

import jwt
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'data.db'
SECRET_KEY = os.getenv("SECRET_KEY")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance BIGINT NOT NULL
            );
        ''')
        db.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            token = token.split("Bearer ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(data, flush=True)
            request.user = data
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not all([username, password]):
            return jsonify({"error": "All fields are required"}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username, password, balance) VALUES (?, ?, ?)', 
                       (username, password, 0))
        db.commit()
        return jsonify({"message": "User created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()

    if user:
        payload = {
            "id": user[0],
            "username": user[1],
            "exp": datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(minutes=10)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/', methods=['GET'])
@token_required
def index():
    balance = get_balance(request.user['id'])
    return jsonify({
        "user": request.user,
        "balance": balance
    })

@app.route('/redeem', methods=['POST'])
@token_required
def redeem():
    """Reddem a free 100$ once"""
    balance = get_balance(request.user['id'])
    if balance == 0:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users set balance  = balance + 400 WHERE id =  ?', (request.user['id'],))
        db.commit()
        return "Added 100$ to your account"
    return "You already redeemed your free 100$"

@app.route('/flag', methods=['POST'])
@token_required
def flag():
    if (balance := get_balance(request.user['id'])) < 500:
        return jsonify({"message": f"insufficient funds, your balance is {balance}"}), 200
    return jsonify({"flag": os.getenv('FLAG')}), 200

def get_balance(user_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT balance FROM users WHERE id =  ?', (user_id,))
    return cursor.fetchone()[0]

init_db()
