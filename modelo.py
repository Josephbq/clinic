import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report

data = pd.read_csv('datos.csv')

label_encoder = LabelEncoder()
data['genero'] = label_encoder.fit_transform(data['genero'])
data['fuma'] = label_encoder.fit_transform(data['fuma'])
data['antecedentes_familiares'] = label_encoder.fit_transform(data['antecedentes_familiares'])
data['tos_cronica'] = label_encoder.fit_transform(data['tos_cronica'])
data['dificultad_respirar'] = label_encoder.fit_transform(data['dificultad_respirar'])
data['sibilancias'] = label_encoder.fit_transform(data['sibilancias'])
data['habitos'] = label_encoder.fit_transform(data['habitos'])
data['exposicion_sustancias_irritantes'] = label_encoder.fit_transform(data['exposicion_sustancias_irritantes'])
data['ocupacion'] = label_encoder.fit_transform(data['ocupacion'])
data['otros_diagnosticos'] = label_encoder.fit_transform(data['otros_diagnosticos'])
data['enfermedad_posible'] = label_encoder.fit_transform(data['enfermedad_posible'])

X = data.drop(columns=['enfermedad_posible'])
y = data['enfermedad_posible']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)
print(f'Precisión: {accuracy}')
#print(f'Informe de clasificación:\n{report}')

nuevos_datos = pd.read_csv('nuevos.csv')
nuevos_datos['genero'] = label_encoder.fit_transform(nuevos_datos['genero'])
nuevos_datos['fuma'] = label_encoder.fit_transform(nuevos_datos['fuma'])
nuevos_datos['antecedentes_familiares'] = label_encoder.fit_transform(nuevos_datos['antecedentes_familiares'])
nuevos_datos['tos_cronica'] = label_encoder.fit_transform(nuevos_datos['tos_cronica'])
nuevos_datos['dificultad_respirar'] = label_encoder.fit_transform(nuevos_datos['dificultad_respirar'])
nuevos_datos['sibilancias'] = label_encoder.fit_transform(nuevos_datos['sibilancias'])
nuevos_datos['habitos'] = label_encoder.fit_transform(nuevos_datos['habitos'])
nuevos_datos['exposicion_sustancias_irritantes'] = label_encoder.fit_transform(nuevos_datos['exposicion_sustancias_irritantes'])
nuevos_datos['ocupacion'] = label_encoder.fit_transform(nuevos_datos['ocupacion'])
nuevos_datos['otros_diagnosticos'] = label_encoder.fit_transform(nuevos_datos['otros_diagnosticos'])

predicciones = model.predict(nuevos_datos)


print(data.head())
print(nuevos_datos.head())
print(f'Predicciones para los nuevos datos: {predicciones}')