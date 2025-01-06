import os
from openai import OpenAI
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de API de OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")

# Configuración de la conexión a PostgreSQL
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# Establecer conexión global
try:
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("Conectado a la base de datos correctamente.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()

# Función para obtener los autores sin biografía
def get_authors():
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS name FROM author WHERE bio IS NULL")
    return cursor.fetchall()  # Lista de tuplas (id, name)

# Función para generar la biografía con OpenAI
def get_author_biography(author_name):
    prompt = f"Write a brief 50-word biography of {author_name}, focusing on their most famous work, literary style, and key contributions to literature. Keep it concise and impactful."
    try:
        client= OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error al obtener la biografía de {author_name}: {e}")
        return None

# Función para actualizar la biografía en la base de datos
def update_author_biography(author_id, biography):
    if biography:  # Solo actualiza si la biografía no es None
        cursor.execute("""
                UPDATE author 
                SET bio = %s, updated_at = NOW() 
                WHERE id = %s
            """, (biography, author_id))
        connection.commit()

# Ejecutar el proceso
authors = get_authors()
if not authors:
    print("No hay autores pendientes de biografía.")
else:
    for author_id, author_name in authors:
        print(f"Generando biografía para: {author_name}")
        bio = get_author_biography(author_name)
        if bio:
            update_author_biography(author_id, bio)
            print(f"Biografía actualizada para {author_name}\n")
        else:
            print(f"No se pudo generar biografía para {author_name}\n")

# Cerrar conexión al finalizar
cursor.close()
connection.close()
print("Conexión cerrada. Proceso completado.")
