from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
import pandas as pd
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report


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
                            return jsonify({'message': 'Adm Log', 'username': user['nombres'], 'session_id': session.sid, 'idd': user['idDoctor'], 'role': role})
                        else:
                            start_time = (datetime.min + doctor_schedule['horae']).time()
                            end_time = (datetime.min + doctor_schedule['horas']).time()

                            if start_time <= current_time <= end_time:
                                cursor.execute('INSERT INTO registro_login (iddoctor, hora_inicio, estado) VALUES (%s, %s, %s)',
                                               (user['idDoctor'], login_time, 'exitoso'))
                                session['user_id'] = user['idDoctor']
                                db.commit()
                                return jsonify({'message': 'Login successful', 'username': user['nombres'], 'session_id': session.sid, 'id': user['idDoctor'], 'role': role })
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
            cursor.execute("SELECT idpaciente,fechanac FROM paciente where estado = %s", (estado,))
            paciente_id = cursor.fetchone()
            if paciente_id:
                return jsonify({'message': 'positivo', 'paciente': paciente_id['idpaciente'], 'fechanac': paciente_id['fechanac']}), print('ya esta')
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
    
@app.route('/register_patologias', methods=['POST'])
def register_patologias():
    data = request.json
    paciente = data.get('paciente')
    patologia = data.get('patologia')
    familiar = data.get('familiar')
    detalles = data.get('detalles')
    resumen = data.get('resumen')

    try:
        with db.cursor() as cursor:
            cursor.execute('INSERT INTO antecedentespatologicos (idpaciente, patologia_familiar, patologia_familiar_parentesco, detalles, resumen) VALUES (%s, %s, %s, %s, %s)', 
                           (paciente, patologia, familiar, detalles, resumen))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error
    
@app.route('/register_exafisi', methods=['POST'])
def register_hc():
    data = request.json
    paciente = data.get('paciente')
    fechanac = data.get('fechanac')
    talla = data.get('talla')
    peso = data.get('peso')
    presiona = data.get('presiona')
    frecuenciac = data.get('frecuenciac')
    frecuenciar = data.get('frecuenciar')
    temperatura = data.get('temperatura')
    saturacion = data.get('saturacion')
    otras = data.get('otras')
    estado = data.get('estado')
    fechanacimiento = datetime.strptime(fechanac, "%Y-%m-%d")
    fechaactual = datetime.now()
    diferencia = fechaactual - fechanacimiento
    edad = diferencia.days // 365
    try:
        with db.cursor() as cursor:
            cursor.execute('INSERT INTO historiaclinica (idpaciente, fecha, edadh, talla, peso, frecuenciac, frecuenciar, presiona, saturacion, temperatura, otros, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                           (paciente, fechaactual, edad, talla, peso, frecuenciac, frecuenciar, presiona, saturacion, temperatura, otras, estado))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error

@app.route('/data/gethc', methods=['POST'])
def getidhc():
    data = request.json
    estado = data.get('estado')
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT idHC FROM historiaclinica where estado = %s", (estado,))
            historia_id = cursor.fetchone()
            if historia_id:
                return jsonify({'message': 'positivo', 'hcid': historia_id['idHC']}), print('ya esta')
            else:
                return jsonify({'message': 'negativo'}), print('no esta')
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/register_consulta', methods=['POST'])
def regiser_consulta():
    data = request.json
    hc = data.get('hc')
    iddoctor = data.get('iddoctor')
    tos = data.get('tos')
    respiracion = data.get('respiracion')
    sibilancias = data.get('sibilancias')
    exposicion = data.get('exposicion')
    fisica = data.get('fisica')
    otras_enfer = data.get('otras_enfer')
    try:
        with db.cursor() as cursor:
            cursor.execute('INSERT INTO consulta (idHC, iddoctor, tos_cronica, dificultad_respirar, sibilancias, exposicion_sustancias, nivel_actividad_fisica, enfermedades_respiratorias) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', 
                           (hc, iddoctor, tos, respiracion, sibilancias, exposicion, fisica, otras_enfer))
            db.commit()

            return jsonify({'message': 'Register successful'})

    except Exception as e:
        return jsonify({'message': 'Ocurrió un error al registrar el usuario', 'error': str(e)}), print(e) # Internal Server Error

# Función para preparar los datos del paciente para el modelo
def preparar_datos_paciente(paciente):
    datos_paciente = {
        "genero": paciente['sexo'],
        "edad": paciente['edadh'],
        "talla": paciente['talla'],
        "peso": paciente['peso'],
        "antecedentes_familiares": paciente['patologia_familiar'],
        "tos_cronica": paciente['tos_cronica'],
        "dificultad_respirar": paciente['dificultad_respirar'],
        "sibilancias": paciente['sibilancias'],
        "habitos": paciente['habitos'],
        "exposicion_sustancias_irritantes": paciente['exposicion_sustancias'],
        "ocupacion": paciente['ocupacion'],
        "otros_diagnosticos": paciente['enfermedades_respiratorias'],
        "nivel_actividad_fisica": paciente['nivel_actividad_fisica'],
        "enfermedad_posible": paciente['enfermedad_posible'],
    }
    datos_paciente_df = pd.DataFrame([datos_paciente])
    return datos_paciente_df

# Función para preparar los datos del paciente para el modelo
def preparar_nuevos_datos_paciente(pacientenuevo):
    datos_nuevo_paciente = {
        "genero": pacientenuevo['sexo'],
        "edad": pacientenuevo['edadh'],
        "talla": pacientenuevo['talla'],
        "peso": pacientenuevo['peso'],
        "antecedentes_familiares": pacientenuevo['patologia_familiar'],
        "tos_cronica": pacientenuevo['tos_cronica'],
        "dificultad_respirar": pacientenuevo['dificultad_respirar'],
        "sibilancias": pacientenuevo['sibilancias'],
        "habitos": pacientenuevo['habitos'],
        "exposicion_sustancias_irritantes": pacientenuevo['exposicion_sustancias'],
        "ocupacion": pacientenuevo['ocupacion'],
        "otros_diagnosticos": pacientenuevo['enfermedades_respiratorias'],
        "nivel_actividad_fisica": pacientenuevo['nivel_actividad_fisica'],
    }
    datos_nuevo_paciente_df = pd.DataFrame([datos_nuevo_paciente])
    return datos_nuevo_paciente_df

@app.route('/ml/<string:sessionid>')
def register_ml(sessionid):
    try:
        with db.cursor() as cursor:
            cursor.execute("""SELECT paciente.*, antecedentes.*, antecedentespatologicos.*, consulta.*, historiaclinica.*, diagnosticos.* FROM paciente 
                           LEFT JOIN antecedentes ON paciente.idpaciente = antecedentes.idpaciente 
                           LEFT JOIN antecedentespatologicos ON paciente.idpaciente = antecedentespatologicos.idpaciente 
                           LEFT JOIN historiaclinica ON paciente.idpaciente = historiaclinica.idpaciente
                           LEFT JOIN consulta ON historiaclinica.idHC = consulta.idHC
                           LEFT JOIN diagnosticos ON consulta.idconsulta = diagnosticos.idconsulta
                           WHERE paciente.estado = 'entrenamiento' """)
            paciente = cursor.fetchone()

            cursor.execute("""SELECT paciente.*, antecedentes.*, antecedentespatologicos.*, consulta.*, historiaclinica.* FROM paciente 
                           LEFT JOIN antecedentes ON paciente.idpaciente = antecedentes.idpaciente 
                           LEFT JOIN antecedentespatologicos ON paciente.idpaciente = antecedentespatologicos.idpaciente 
                           LEFT JOIN historiaclinica ON paciente.idpaciente = historiaclinica.idpaciente
                           LEFT JOIN consulta ON historiaclinica.idHC = consulta.idHC
                           WHERE paciente.estado = %s""", (sessionid,))
            pacientenuevo = cursor.fetchone()

            if paciente:
                datos_iniciales = preparar_datos_paciente(paciente)
                label_encoder = LabelEncoder()
                for col in datos_iniciales.columns:
                    if datos_iniciales[col].dtype == 'object':
                        datos_iniciales[col] = label_encoder.fit_transform(datos_iniciales[col])

                # Crear y entrenar el modelo solo si es la primera vez
                if 'modelo' not in locals():
                    X = datos_iniciales.drop(columns=['enfermedad_posible'])
                    y = datos_iniciales['enfermedad_posible']
                    modelo = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
                    modelo.fit(X, y)

                nuevos_datos = preparar_nuevos_datos_paciente(pacientenuevo)
                # Aplicar la misma codificación a las columnas categóricas en los nuevos datos
                for col in nuevos_datos.columns:
                    if nuevos_datos[col].dtype == 'object':
                        nuevos_datos[col] = label_encoder.fit_transform(nuevos_datos[col])

                # Hacer predicciones con los nuevos datos
                predicciones = modelo.predict(nuevos_datos)

                print(predicciones)
                return jsonify(predicciones)
            else:
                return jsonify({'message': 'Paciente no encontrado'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)})
    

if __name__ == '__main__':
    app.run(debug=True)
    
