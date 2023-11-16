from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
import pandas as pd
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app)
app.secret_key = "tu_secreto_secreto"  # Clave secreta para la sesión
app.config["SESSION_TYPE"] = "filesystem"  # Almacenamiento en el sistema de archivos
Session(app)

db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='prueba_agra',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
# Ruta para registrar un usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    lastname = data.get('lastname')
    lastnamem = data.get('lastnamem')
    sexo = data.get('sexo')
    option = data.get('option')
    email = data.get('email')
    password = data.get('password')

    try:
        with db.cursor() as cursor:
            cursor.execute('SELECT * FROM doctor WHERE correo=%s', (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Email Dupli'})

            hashed_password = generate_password_hash(password, method='scrypt')

            cursor.execute('INSERT INTO doctor (idtipo, nombres, apellidop, apellidom, sexo, area, correo, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                           ( 1 , username, lastname, lastnamem, sexo, option, email, hashed_password))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error
    

@app.route('/hour', methods=['POST'])
def registertime():
    data = request.json
    id_doctor = data.get('doc')
    dia = data.get('dia')
    horae = data.get('horae')
    horas = data.get('horas')

    try:
        with db.cursor() as cursor:

            cursor.execute('INSERT INTO horario (iddoctor, dia, horae, horas) VALUES (%s, %s, %s, %s)', (id_doctor, dia, horae, horas))
            db.commit()

            return jsonify({'message': 'register_successful'})

    except Exception as e:
        return jsonify({'message': 'problem', 'error': str(e)}),print(e)

@app.route('/api/getdocs')
def get_datadoc():
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT idDoctor, nombres FROM doctor WHERE idtipo = 2")
            records = cursor.fetchall()
            return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)})

# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('username')
    password = data.get('password')

    try:
        with db.cursor() as cursor:
            cursor.execute('SELECT * FROM doctor WHERE correo=%s', (email,))
            user = cursor.fetchone()

            if user:
                stored_password = user['password']

                if check_password_hash(stored_password, password):

                    role = user['idtipo']
                    current_day = datetime.now().strftime('%A').lower()
                    current_time = datetime.now().time()
                    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    cursor.execute('SELECT * FROM horario WHERE iddoctor=%s AND dia=%s', (user['idDoctor'], current_day))
                    doctor_schedule = cursor.fetchone()

                    if (doctor_schedule and role == 2) or role == 1:
                        if role == 1:
                            session['user_id'] = user['idDoctor']
                            return jsonify({'message': 'Adm Log', 'username': user['nombres'], 'session_id': session.sid, 'role': role})
                        else:
                            start_time = (datetime.min + doctor_schedule['horae']).time()
                            end_time = (datetime.min + doctor_schedule['horas']).time()

                            if start_time <= current_time <= end_time:
                                cursor.execute('INSERT INTO registro_login (iddoctor, hora_inicio, estado) VALUES (%s, %s, %s)',
                                               (user['idDoctor'], login_time, 'exitoso'))
                                session['user_id'] = user['idDoctor']
                                db.commit()
                                return jsonify({'message': 'Login successful', 'username': user['nombres'], 'session_id': session.sid, 'role': role })
                            else:
                                cursor.execute('INSERT INTO registro_login (iddoctor, hora_inicio, estado) VALUES (%s, %s, %s)',
                                               (user['idDoctor'], login_time, 'fuera de horario'))
                                db.commit()
                                return jsonify({'message': 'Fuera de horario laboral'})
                    else:
                        cursor.execute('INSERT INTO registro_login (iddoctor, hora_inicio, estado) VALUES (%s, %s, %s)',
                                       (user['idDoctor'], login_time, 'sin horario'))
                        db.commit()
                        return jsonify({'message': 'El doctor no tiene horario laboral hoy'})

            return jsonify({'message': 'Login failed'})

    except Exception as e:
        print('Error:', str(e))
        return jsonify({'message': 'An error occurred', 'error': str(e)})
    

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/data')
def get_data():
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT registro_login.*, doctor.nombres as nombre_doc FROM registro_login INNER JOIN doctor ON registro_login.iddoctor = doctor.idDoctor")
            records = cursor.fetchall()
            return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route('/data/pacientes')
def get_datap():
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM paciente")
            records = cursor.fetchall()
            return jsonify(records)
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/pacientes/<int:paciente_id>')
def get_detalle_paciente(paciente_id):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM paciente WHERE idpaciente=%s", (paciente_id,))
            paciente = cursor.fetchone()

            if paciente:
                
                cursor.execute("SELECT * FROM historiaclinica WHERE idpaciente=%s", (paciente_id,))
                historiales_clinicos = cursor.fetchall()

                paciente_info = {
                    "id": paciente['idpaciente'],
                    "nombre": paciente['nombres'],
                    "celular": paciente['telefono'],
                    "apellidoM": paciente['apellidom'],
                    "sexo": paciente['sexo'],
                    "historiales_clinicos": historiales_clinicos
                }

                return jsonify(paciente_info)
            else:
                return jsonify({'message': 'Paciente no encontrado'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/registrar_consulta', methods=['POST'])
def registrar_consulta():
    genero = request.form.get('genero')
    edad = request.form.get('edad')
    fuma = request.form.get('fuma')
    antecedentes_familiares = request.form.get('antecedentes_familiares')
    tos_cronica = request.form.get('tos_cronica')
    dificultad_respirar = request.form.get('dificultad_respirar')
    sibilancias = request.form.get('sibilancias')
    habitos = request.form.get('habitos')
    exposicion_sustancias_irritantes = request.form.get('exposicion_sustancias_irritantes')
    ocupacion = request.form.get('ocupacion')
    otros_diagnosticos = request.form.get('otros_diagnosticos')


    nuevos_datos = pd.DataFrame({
        'genero': [genero],
        'edad': [edad],
        'fuma': [fuma],
        'antecedentes_familiares': [antecedentes_familiares],
        'tos_cronica': [tos_cronica],
        'dificultad_respirar': [dificultad_respirar],
        'sibilancias': [sibilancias],
        'habitos': [habitos],
        'exposicion_sustancias_irritantes': [exposicion_sustancias_irritantes],
        'ocupacion': [ocupacion],
        'otros_diagnosticos': [otros_diagnosticos],
    })

    open('nuevos.csv', 'w').close()
    nuevos_datos.to_csv('nuevos.csv', index=False, header=True, mode='a')
    datos_entrenamiento = pd.DataFrame([nuevos_datos])
    datos_entrenamiento.to_csv("datos.csv", mode="a", header=False, index=False)

    return 'Consulta registrada con éxito'


# Ruta para registrar un usuario
@app.route('/register_paciente', methods=['POST'])
def register_paciente():
    data = request.json
    fechanac = data.get('fechanac')
    telefono = data.get('telefono')
    nombres = data.get('nombres')
    apellidop = data.get('apellidop')
    apellidom = data.get('apellidom')
    sexo = data.get('sexo')
    ci = data.get('ci')
    domicilio = data.get('domicilio')
    estado = data.get('estado')
    fechanacimiento = datetime.strptime(fechanac, "%Y-%m-%d")
    fechaactual = datetime.now()
    diferencia = fechaactual - fechanacimiento
    edad = diferencia.days // 365
    try:
        with db.cursor() as cursor:
            cursor.execute('INSERT INTO paciente (fechanac, edad, telefono, nombres, apellidop, apellidom, sexo, ci, domicilio, fecha_registro, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                           ( fechanac , edad, telefono, nombres, apellidop, apellidom, sexo, ci, domicilio, fechaactual, estado))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error

@app.route('/data/session', methods=['POST'])
def getidsession():
    data = request.json
    estado = data.get('estado')
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT idpaciente FROM paciente where estado = %s", (estado,))
            paciente_id = cursor.fetchone()
            if paciente_id:
                return jsonify({'message': 'positivo', 'paciente': paciente_id['idpaciente']}), print('ya esta')
            else:
                return jsonify({'message': 'negativo'}), print('no esta')
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/register_antecedentes', methods=['POST'])
def register_antecedentes():
    data = request.json
    paciente = data.get('paciente')
    estudios = data.get('estudios')
    estado_civil = data.get('estado_civil')
    ocupacion = data.get('ocupacion')
    origen = data.get('origen')
    sanamiento = data.get('sanamiento')
    alimentacion = data.get('alimentacion')
    habitos = data.get('habitos')

    try:
        with db.cursor() as cursor:
            cursor.execute('INSERT INTO antecedentes (idpaciente, estudios, estado_civil, ocupacion, origen, sanamiento, alimentacion, habitos) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                           (paciente, estudios, estado_civil, ocupacion, origen, sanamiento, alimentacion, habitos))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error
    
if __name__ == '__main__':
    app.run(debug=True)
    
