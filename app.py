from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import firebase_admin
from firebase_admin import credentials, db, messaging
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

# Firebase Refs
ref = db.reference("Sensors")
PhAlert = db.reference("Notifications/PH")
TempAlert = db.reference("Notifications/Temperature")
TurbAlert = db.reference("Notifications/Turbidity")
ph_tresh = db.reference("Treshold/PH")
temp_tresh = db.reference("Treshold/Temperature")
turb_tresh = db.reference("Treshold/Turbidity")

# Send FCM notification to topic
def send_fcm_notification(title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        topic="sensor_alerts"
    )
    try:
        response = messaging.send(message)
        print(f"FCM Notification sent: {response}")
    except Exception as e:
        print(f"Error sending FCM notification: {e}")

# Check thresholds and return alerts
def treshold_checker(data):
    ph_alert_value = PhAlert.get()
    temp_alert_value = TempAlert.get()
    turb_alert_value = TurbAlert.get()

    ph_value_tresh = ph_tresh.get()
    temp_value_tresh = temp_tresh.get()
    turb_value_tresh = turb_tresh.get()

    ph_value = data["PH"]
    temp_value = data["Temperature"]
    turb_value = data["Turbidity"]

    alert_messages = []

    if ph_alert_value == True:
        if ph_value < ph_value_tresh["MIN"] or ph_value > ph_value_tresh["MAX"]:
            alert_messages.append(f"PH level out of range: {ph_value}")

    if temp_alert_value == True:
        if temp_value < temp_value_tresh["MIN"] or temp_value > temp_value_tresh["MAX"]:
            alert_messages.append(f"Temperature out of range: {temp_value}°C")

    if turb_alert_value == True:
        if turb_value < turb_value_tresh["MIN"] or turb_value > turb_value_tresh["MAX"]:
            alert_messages.append(f"Turbidity out of range: {turb_value} NTU")

    # If alerts were triggered, send FCM notification
    if alert_messages:
        alert_body = "\n".join(alert_messages)
        send_fcm_notification("Sensor Alert", alert_body)

    return alert_messages

# Endpoint for sensor data
@app.route("/sensors", methods=["POST"])
def handle_sensors():
    try:
        data = request.json

        if "PH" not in data or "Temperature" not in data or "Turbidity" not in data:
            return jsonify({"error": "Missing required data fields"}), 400

        ph_value = data["PH"]
        temp_value = data["Temperature"]
        turb_value = data["Turbidity"]

        alerts = treshold_checker(data)

        ref.update({
            "PH": ph_value,
            "Temperature": temp_value,
            "Turbidity": turb_value
        })

        return jsonify({
            "Response": "Data processed and updated successfully.",
            "Alerts": alerts
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process and update data."}), 500

if __name__ == "__main__":
    print("Server is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
