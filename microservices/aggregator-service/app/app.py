import pymysql
from flask import Flask, request, jsonify
from werkzeug.exceptions import InternalServerError
from datetime import datetime, time, date, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# MySQL credentials
# Use environment variables for security
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = 'healthsync-db.c5u0mm4k6d06.us-east-1.rds.amazonaws.com'
DB_NAME = 'healthsync'
DB_PORT = 3306

# Function to create DB connection
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            db=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        raise InternalServerError(f"Error connecting to the database: {str(e)}")

# Helper function to serialize datetime and other objects
def custom_serializer(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    raise TypeError(f"Type {type(obj)} not serializable")

# Route: Number of appointments per doctor
@app.route('/aggregator/appointments-per-doctor', methods=['GET'])
def appointments_per_doctor():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT requested_doctor, COUNT(*) AS appointment_count FROM patient GROUP BY requested_doctor")
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Error aggregating data: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Route: Appointment frequency over time
@app.route('/aggregator/appointment-frequency', methods=['GET'])
def appointment_frequency():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT appointment_date, COUNT(*) AS appointment_count FROM patient GROUP BY appointment_date")
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching frequency data: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Route: Placeholder for common symptoms and conditions
@app.route('/aggregator/common-conditions', methods=['GET'])
def common_conditions():
    # This is a placeholder; actual implementation depends on schema updates for symptoms and conditions.
    return jsonify({"message": "Common conditions insights coming soon."}), 200

# Route: Create a patient appointment
@app.route('/patients', methods=['POST'])
def create_patient():
    data = request.json
    patient_id = data.get('patient_id')
    name = data.get('name')
    requested_doctor = data.get('requested_doctor')
    appointment_time = data.get('appointment_time')
    appointment_date = data.get('appointment_date')

    if not patient_id or not name or not requested_doctor or not appointment_time or not appointment_date:
        return jsonify({"error": "Missing required fields"}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM patient WHERE patient_id = %s AND requested_doctor = %s AND appointment_date = %s",
                (patient_id, requested_doctor, appointment_date)
            )
            if cursor.fetchone():
                return jsonify({"error": "Duplicate appointment"}), 400

            cursor.execute(
                """
                INSERT INTO patient (patient_id, name, requested_doctor, appointment_time, appointment_date, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (patient_id, name, requested_doctor, appointment_time, appointment_date)
            )
            connection.commit()

        return jsonify({"message": "Patient appointment created successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Error creating appointment: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
