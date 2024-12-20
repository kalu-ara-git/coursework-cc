import pymysql
from flask import Flask, request, jsonify
from werkzeug.exceptions import InternalServerError
from datetime import datetime, time, date, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# MySQL credentials (hardcoded for debugging purposes)
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

# Route to fetch all data for a given patient_id
@app.route('/patients/<patient_id>/records', methods=['GET'])
def get_patient_records(patient_id):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
            records = cursor.fetchall()

            if not records:
                return jsonify({"error": "No records found for the given patient_id"}), 404

            serialized_records = [
                {
                    key: (custom_serializer(value) if isinstance(value, (datetime, date, time, timedelta)) else value)
                    for key, value in record.items()
                }
                for record in records
            ]
            return jsonify(serialized_records), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching patient records: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Route to update doctor recommendation for a given patient_id and date
@app.route('/patients/<patient_id>/recommendation', methods=['PUT'])
def update_doctor_recommendation(patient_id):
    data = request.json
    appointment_date = data.get('appointment_date')
    doctor_recommendation = data.get('doctor_recommendation')

    if not appointment_date or not doctor_recommendation:
        return jsonify({"error": "Missing required fields: appointment_date or doctor_recommendation"}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE patient 
                SET doctor_recommendation = %s 
                WHERE patient_id = %s AND appointment_date = %s
                """,
                (doctor_recommendation, patient_id, appointment_date)
            )
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "No matching record found to update"}), 404

        return jsonify({"message": "Doctor recommendation updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error updating doctor recommendation: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
