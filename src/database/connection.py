import os
import psycopg2
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env
load_dotenv()

def get_connection():
    """
    Crea y retorna una conexión a la base de datos PostgreSQL,
    usando las credenciales definidas en el archivo .env
    """
    connection = psycopg2.connect(
        host="localhost",
        port=5432,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB")
    )
    return connection