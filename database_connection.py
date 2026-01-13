import mysql.connector
from functions import *

def create_connection():
    try:
        host = read_config_value("config.txt", "DB_Host")
        user = read_config_value("config.txt", "DB_User")
        password = read_config_value("config.txt", "DB_Password")
        database = read_config_value("config.txt", "DB_Name")
        port = read_config_value("config.txt", "DB_Port")

        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        if connection.is_connected():
            print("Database connection established successfully.")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


if __name__ == "__main__":
    create_connection()
