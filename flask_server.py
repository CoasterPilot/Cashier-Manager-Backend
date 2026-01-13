from flask import Flask, request, abort, jsonify, send_from_directory
import subprocess
import json
import sys
import os
from functions import *
from database_connection import create_connection

app = Flask(__name__)

@app.route('/accounts', methods=['POST'])
def get_accounts():
    TOKEN = read_config_value("config.txt", "API_Token")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return abort(401, "Authentifizierung erforderlich.")

    token_received = auth_header.split("Bearer ")[1].strip()
    if token_received != TOKEN:
        return abort(401, "Falsches Token")

    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Username, cash_balance FROM Accounts")
        accounts = cursor.fetchall()

        return jsonify({"message": "Accounts retrieved successfully", "accounts": accounts})
    
    except Exception as e:
        print(f"Error retrieving accounts: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



if __name__ == "__main__":
    host = read_config_value("config.txt", "Server_Host")
    port = read_config_value("config.txt", "Server_Port")
    app.run(host=host, port=port, debug=True)