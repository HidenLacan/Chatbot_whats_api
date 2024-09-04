from flask import Flask, jsonify, request
import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
from heyoo import WhatsApp

app = Flask(__name__)

# Load environment variables once at the start
load_dotenv()
openai_api_key = os.getenv("API_KEY")

tokenface = os.getenv("token")
idnumbertoken = os.getenv("idphonenumber")
client = OpenAI(api_key=openai_api_key)

# SQLite Configuration
DATABASE = 'whatsapp_responses.db'  # This will create a file named whatsapp_responses.db in your project directory

def create_db():
    connection = None
    cursor = None
    try:
        # Connect to SQLite (it will create the file if it doesn't exist)
        connection = sqlite3.connect(DATABASE)
        cursor = connection.cursor()

        # Create the table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            message TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_table_query)
        connection.commit()

    except sqlite3.Error as err:
        print(f"SQLite error: {err}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def save_response_to_db(phone_number, message, response):
    connection = None
    cursor = None
    try:
        # Connect to SQLite
        connection = sqlite3.connect(DATABASE)
        cursor = connection.cursor()

        # Insert the response into the database
        sql = "INSERT INTO responses (phone_number, message, response) VALUES (?, ?, ?)"
        values = (phone_number, message, response)
        cursor.execute(sql, values)
        connection.commit()  # Commit the transaction

    except sqlite3.Error as err:
        print(f"SQLite error: {err}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
def sendmessage(phonenumberdestiny,response):
    token = tokenface
    idphonenumber= idnumbertoken
    messagedestiny= WhatsApp(token,idphonenumber)
    phonenumberdestiny=phonenumberdestiny.replace("521","52")
    return messagedestiny.send_message(response,phonenumberdestiny)
    

@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    
    if request.method == "GET":
        if request.args.get("hub.verify_token") == "TokenToken":
            return request.args.get('hub.challenge')
        else:
            return "Error de autentificación", 403
    
    if request.method == "POST":
        data = request.get_json()
        
        try:
            telefonoCliente = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            idWA = data['entry'][0]['changes'][0]['value']['messages'][0]['id']
            timestamp = data['entry'][0]['changes'][0]['value']['messages'][0]['timestamp']
        
        except KeyError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        
        if mensaje:
            try:
                completion = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    temperature=0.7,
                    messages=[
                        {'role': 'system', 'content': 'Soy un asistente virtual que brinda información adecuada'},
                        {"role": "user", "content": mensaje}
                    ]
                )
                response_message = completion.choices[0].message.content.strip()
                
                # Save the response in the database
                save_response_to_db(telefonoCliente, mensaje, response_message)
                sendmessage(telefonoCliente,response_message)
                # Optionally write to a file (if still needed)
                #with open("texto.txt", "w") as f:
                #   f.write(response_message)
                
                return jsonify({"status": "success", "message": response_message}), 200
            
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        return jsonify({"status": "no_message_found"}), 400
    
if __name__ == "__main__":
    create_db()  # Ensure the database and table are created
    app.run(debug=True)
