from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='agra_bd',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    try:
        with db.cursor() as cursor:
            cursor.execute('SELECT * FROM doctor WHERE correo=%s AND password=%s', (username, password))
            user = cursor.fetchone()

            if user:
                return jsonify({'message': 'Login successful', 'username': user['nombres']}), print('si');
            else:
                return jsonify({'message': 'Login failed'}), print('no');

    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)})
    
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    lastname = data.get('lastname')
    email = data.get('email')
    password = data.get('password')


    try:
        with db.cursor() as cursor:
            cursor.execute('SELECT * FROM doctor WHERE correo=%s', (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Email Dupli'})

            cursor.execute('INSERT INTO doctor (nombres, apellidop, correo, password) VALUES (%s, %s, %s, %s)', (username,lastname,email, password))
            db.commit() 

            return jsonify({'message': 'Register successful'}), print({'funciona'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}) # Internal Server Error


if __name__ == '__main__':
    app.run(debug=True)
    
