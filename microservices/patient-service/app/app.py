import pymysql
from flask import Flask, request, jsonify
from werkzeug.exceptions import InternalServerError
from datetime import datetime, time, date, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# MySQL credentials (hardcoded for debugging purposes)
# db_username =  'admin'
# db_password = 'pw-healthsync321'
db_username = os.getenv("DB_USERNAME")  # MySQL username from secrets
db_password = os.getenv("DB_PASSWORD")  # MySQL password from secrets
db_host = 'healthsync-db.c5u0mm4k6d06.us-east-1.rds.amazonaws.com'
db_name = 'healthsync'
db_port = 3306  # Default MySQL port

# Function to create DB connection
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_username,
            password=db_password,
            db=db_name,
            port=db_port,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        raise InternalServerError(f"Error connecting to the database: {str(e)}")

# Helper function to serialize datetime, timedelta, and other objects
def custom_serializer(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    raise TypeError(f"Type {type(obj)} not serializable")

# Route to test RDS connection
@app.route('/test', methods=['GET'])
def test_connection():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM patient LIMIT 10")
            results = cursor.fetchall()
            # Serialize results to handle datetime and timedelta objects
            serialized_results = [
                {key: (custom_serializer(value) if isinstance(value, (datetime, date, time, timedelta)) else value) for key, value in row.items()} 
                for row in results
            ]
            return jsonify(serialized_results), 200
    except Exception as e:
        return jsonify({"error": f"Error testing RDS connection: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Route to create a patient
@app.route('/patients', methods=['POST'])
def create_patient():
    data = request.json
    patient_id = data.get('id')
    name = data.get('name')
    requested_doctor = data.get('requested_doctor')
    appointment_time = data.get('appointment_time')
    appointment_date = data.get('appointment_date')
    # doctor_recommendation = data.get('doctor_recommendation')

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
                return jsonify({"error": "Duplicate appointment request: Patient has already requested this doctor on the same day"}), 400

            cursor.execute(
                """
                INSERT INTO patient (patient_id, name, requested_doctor, appointment_time, appointment_date, created_at)
                VALUES (%s, %s, %s, %s, %s,  NOW())
                """,
                (patient_id, name, requested_doctor, appointment_time, appointment_date)
            )
            connection.commit()

        return jsonify({"message": "Patient appointment created successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Error creating patient appointment: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Route to get a patient by ID
@app.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
            patient = cursor.fetchone()

            if not patient:
                return jsonify({"error": "Patient not found"}), 404

            serialized_patient = {
                key: (custom_serializer(value) if isinstance(value, (datetime, date, time, timedelta)) else value)
                for key, value in patient.items()
            }
            return jsonify(serialized_patient), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching patient: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)