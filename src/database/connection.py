import os
import psycopg2
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env
load_dotenv()

def get_connection():
    """
    Crea y retorna una conexión a la base de datos PostgreSQL,
    usando las credenciales definidas en el archivo .env

    El host y el puerto se leen del entorno para que el mismo código
    funcione en local (localhost) y dentro de docker compose (postgres).
    """
    connection = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB")
    )
    return connection
