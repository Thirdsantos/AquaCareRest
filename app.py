from flask import Flask, jsonify, request
from flask_cors import CORS  # Import Flask-CORS
import os
import json
import firebase_admin
from firebase_admin import credentials, db, messaging
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
refPh = db.reference("Notification/PH")
refTemp = db.reference("Notification/Temperature")
refTurb = db.reference("Notification/Turbidity")
ref = db.reference("Sensors")

# Route to receive sensor data and compare with thresholds
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
        
        # Fetch thresholds from Firebase
        ph_threshold = refPh.get()
        temp_threshold = refTemp.get()
        turb_threshold = refTurb.get()

        # Check thresholds and send notifications if breached
        if ph_threshold["Min"] > ph_value or ph_threshold["Max"] < ph_value:
            send_fcm_notification("PH Alert", "PH value is out of range!", "ph_alerts")
        
        if temp_threshold["Min"] > temp_value or temp_threshold["Max"] < temp_value:
            send_fcm_notification("Temperature Alert", "Temperature value is out of range!", "temperature_alerts")
        
        if turb_threshold["Min"] > turb_value or turb_threshold["Max"] < turb_value:
            send_fcm_notification("Turbidity Alert", "Turbidity value is out of range!", "turbidity_alerts")

        # Update the Firebase database with the sensor data
        ref.update({
            "PH": ph_value,
            "Temperature": temp_value,
            "Turbidity": turb_value
        })

        return jsonify({"status": "Data processed successfully."}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process data."}), 500

if __name__ == "__main__":
    print("Server is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
