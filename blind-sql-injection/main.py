from flask import Flask, request, jsonify, g
import sqlite3
import jwt
import datetime
from functools import wraps
import os

app = Flask(__name__)
DATABASE = 'users.db'
SECRET_KEY = os.urandom(128).hex()

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
                email TEXT NOT NULL,
                age INTEGER NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL
            );
        ''')
        cursor.execute(f'''
            INSERT INTO logs (username, user_id, action) VALUES ('admin', 0, 'Generated a secure key: {os.environ.get("FLAG")}')
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
        email = data.get('email')
        age = data.get('age')

        if not all([username, password, email, age]):
            return jsonify({"error": "All fields are required"}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username, password, email, age) VALUES (?, ?, ?, ?)', 
                       (username, password, email, age))
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
            "username": user[1],
            "email": user[3],
            "age": user[4],
            "exp": datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(minutes=10)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/profile', methods=['GET'])
@token_required
def profile():
    db = get_db()
    cursor = db.cursor()
    username = request.user['username']

    id_query = f"SELECT id FROM users WHERE username = '{username}'"
    cursor.execute(id_query)
    user_id = cursor.fetchone()[0]

    cursor = db.cursor()
    # log this request to the database
    query = f"INSERT INTO logs (action, user_id, username) VALUES ('{user_id} has requested page /profile', {user_id}, 'user')"
    cursor.execute(query)
    db.commit()

    return jsonify({"profile": request.user }), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=3000, host='0.0.0.0')
