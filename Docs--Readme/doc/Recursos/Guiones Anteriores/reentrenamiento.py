import sqlite3

# Conectar a la base de datos SQLite
conn = sqlite3.connect('D:\\.Origen\\Dash_\\db.sqlite3')
cursor = conn.cursor()

def obtener_interacciones():
    cursor.execute('SELECT consulta, respuesta FROM sesiones')
    return cursor.fetchall()

def reentrenar_modelo():
    datos_entrenamiento = obtener_interacciones()
    # Aquí deberías implementar el código específico para reentrenar tu modelo con los datos obtenidos
    # Esto depende de la API y métodos que Ollama proporciona para reentrenamiento

    # Ejemplo ficticio de cómo podría ser el reentrenamiento con una API hipotética
    # ollama.retrain(model='llama3:8b', training_data=datos_entrenamiento)

    print("Modelo reentrenado con éxito.")

# Llamar a la función de reentrenamiento
if __name__ == "__main__":
    reentrenar_modelo()
