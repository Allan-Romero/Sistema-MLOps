from src.database.connection import get_connection

def test_connection():
    """
    Prueba la conexión a la base de datos y muestra un mensaje
    indicando si fue exitosa o si ocurrió un error.
    """
    try:
        conn = get_connection()
        print("Conexión exitosa")
        conn.close()
    except Exception as error:
        print("Error al conectar a la base de datos:")
        print(error)

if __name__ == "__main__":
    test_connection()