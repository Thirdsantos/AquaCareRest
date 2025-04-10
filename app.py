from flask import Flask, jsonify, request
from flask_cors import CORS  # Import Flask-CORS
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes and all origins
CORS(app, resources={r"/sensors": {"origins": "*"}})  # Allow all origins for /sensors route

# Firebase credentials and initialization
firebase_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
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

# Firebase Realtime Database references
ref = db.reference("Sensors")

# Route to receive sensor data and update database without threshold checks
@app.route("/sensors", methods=["POST"])
def handle_sensors():
    try:
        data = request.json
        
        # Check if all required keys are present
        if "PH" not in data or "Temperature" not in data or "Turbidity" not in data:
            return jsonify({"error": "Missing required data fields"}), 400
        
        # Get the sensor values
        ph_value = data["PH"]
        temp_value = data["Temperature"]
        turb_value = data["Turbidity"]
        
        # Directly update the Firebase Realtime Database with received values
        ref.update({
            "PH": ph_value,
            "Temperature": temp_value,
            "Turbidity": turb_value
        })

        return jsonify({"status": "Data processed and updated successfully."}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process and update data."}), 500

if __name__ == "__main__":
    print("Server is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
