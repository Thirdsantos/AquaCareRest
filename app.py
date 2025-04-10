from flask import Flask, jsonify, request
from flask_cors import CORS  # Import Flask-CORS
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


firebase_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
CORS(app, resources={r"/sensors": {"origins": "*"}})  

if firebase_credentials:
    creds = json.loads(firebase_credentials)
    if not firebase_admin._apps:
        cred = credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://aquamans-47d16-default-rtdb.asia-southeast1.firebasedatabase.app/"
        })
        print("Firebase Connected Successfully!")
else:
    print("Error: GOOGLE_APPLICATION_CREDENTIALS_JSON not found in environment variables.")
    exit()


ref = db.reference("Sensors")
PhAlert = db.reference("Notifications/PH")
TempAlert = db.reference("Notifications/Temperature")
TurbAlert = db.reference("Notifications/Turbidity")


@app.route("/sensors", methods=["POST"])
def handle_sensors():
    try:
        data = request.json
        
      
        if "PH" not in data or "Temperature" not in data or "Turbidity" not in data:
            return jsonify({"error": "Missing required data fields"}), 400
        
       
        ph_value = data["PH"]
        temp_value = data["Temperature"]
        turb_value = data["Turbidity"]
        
       
        ref.update({
            "PH": ph_value,
            "Temperature": temp_value,
            "Turbidity": turb_value
        })

        return jsonify({TurbAlert : "Data processed and updated successfully."}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process and update data."}), 500

if __name__ == "__main__":
    print("Server is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
