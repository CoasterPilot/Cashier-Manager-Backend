import datetime

from flask import Flask, request, abort, jsonify, send_from_directory
import subprocess
import json
import sys
import os
from functions import *
from database_connection import create_connection

app = Flask(__name__)


@app.route('/accounts', methods=['POST'])
#Get all accounts
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
        cursor.execute("SELECT Username, cash_balance, ID FROM Accounts")
        accounts = cursor.fetchall()
        #Ausgabe für den Server zum Debuggen. Ausgabe wird an Server geschickt, damit der Client die Daten erhält.
        print(f"Accounts retrieved successfully: {accounts}")
        return jsonify({"message": f"Accounts retrieved successfully", "accounts": accounts})
    
    except Exception as e:
        print(f"Error retrieving accounts: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/get_account_data', methods=['POST'])
#Get Account Data
def get_account_data():
    TOKEN = read_config_value("config.txt", "API_Token")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return abort(401, "Authentifizierung erforderlich.")

    token_received = auth_header.split("Bearer ")[1].strip()
    if token_received != TOKEN:
        return abort(401, "Falsches Token")

    try:
        data = request.get_json()
        account_id = data.get("id")
        if not account_id:
            return abort(400, "Account-ID ist erforderlich.")

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, cash_balance FROM Accounts WHERE id = %s", (account_id,))
        result = cursor.fetchone()
        if result:
            username, cash_balance = result
            print(f"Account data for {username} retrieved successfully: {cash_balance}")
            return jsonify({"account_id": account_id, "username": username, "cash_balance": cash_balance, "message": f"Account data for {username} retrieved successfully, cash_balance: {cash_balance}"})
        else:
            return abort(404, "Benutzer nicht gefunden.")
    except Exception as e:
        print(f"Error retrieving account data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:        
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Calculate new cash balance after a trade
@app.route('/update_balance', methods=['POST'])
def update_balance():
    TOKEN = read_config_value("config.txt", "API_Token")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return abort(401, "Authentifizierung erforderlich.")

    token_received = auth_header.split("Bearer ")[1].strip()
    if token_received != TOKEN:
        return abort(401, "Falsches Token")
    
    try:
        data = request.get_json()
        account_id = data.get("account_id")
        value = data.get("value")
        reason = data.get("reason", "No reason provided")
        amount_from = data.get("amount_from", "Unknown")

        if not account_id or value is None:
            return abort(400, "Account-ID und Value sind erforderlich.")

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cash_balance FROM Accounts WHERE id = %s", (account_id,))
        result = cursor.fetchone()
        if result:
            current_balance = result[0]
            new_balance = current_balance + float(value)

            # get Accountinfo for BalanceHistory
            cursor.execute("SELECT username FROM Accounts WHERE id = %s", (account_id,))
            result = cursor.fetchone()
            username = result[0]
            cursor.execute("UPDATE Accounts SET cash_balance = %s WHERE id = %s", (new_balance, account_id))
            cursor.execute("INSERT INTO BalanceHistory (username, reason, old_balance, change_amount, new_balance, date, amount_from) VALUES (%s, %s, %s, %s, %s, %s, %s)", (username, reason, current_balance, float(value), new_balance, datetime.datetime.now(), amount_from))
            conn.commit()
            print(f"Balance updated successfully for account {account_id}: new balance is {new_balance}")
            return jsonify({"new_balance": new_balance, "message": f"Balance updated successfully for account {account_id}, new balance: {new_balance}"})
        else:
            return abort(404, "Benutzer nicht gefunden.")
    except Exception as e:
        print(f"Error updating balance: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/add_new_food', methods=['POST'])
def add_new_food():
    TOKEN = read_config_value("config.txt", "API_Token")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return abort(401, "Authentifizierung erforderlich.")

    token_received = auth_header.split("Bearer ")[1].strip()
    if token_received != TOKEN:
        return abort(401, "Falsches Token")
    

    try:
        paylist = []
        data = request.get_json()
        username = data["username"]
        person_and_price_list = data["person_and_price_list"]
        for transaction in person_and_price_list:
            print(f"Received transaction: {transaction}")
            price = transaction["price"]
            name = transaction["paid_by"]
            paylist.append((name, float(price), username))

        if not name or price is None:
            return abort(400, "Name und Price sind erforderlich.")

        conn = create_connection()
        cursor = conn.cursor()
        for transaction in paylist:
            name = transaction[0]
            price = transaction[1]
            username = transaction[2]
            cursor.execute("SELECT cash_balance FROM Accounts WHERE username = %s", (name,))
            old_balance = cursor.fetchone()[0]
            new_price = old_balance + price

            # Update the cash balance in the Accounts table
            cursor.execute("UPDATE Accounts SET cash_balance = %s WHERE username = %s", (new_price, name))
            # Insert into a History table for tracking food purchases
            cursor.execute("INSERT INTO BalanceHistory (username, reason, old_balance, change_amount, new_balance, date, amount_from) VALUES (%s, %s, %s, %s, %s, %s, %s)", (name, "Food Purchase", old_balance, price, new_price, datetime.datetime.now(), username))
        conn.commit()
        print(f"New food item added successfully: {name} with price {price}")
        return jsonify({"message": f"New food item added successfully: {name} with price {price}"})
    except Exception as e:
        print(f"Error adding new food item: {e}")
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