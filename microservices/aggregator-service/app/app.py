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

# Route to insert aggregated data into tables
@app.route('/aggregate', methods=['POST'])
def aggregate_data():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Define the current week range
            def get_week_range():
                today = date.today()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                return start_of_week, end_of_week

            start_of_week, end_of_week = get_week_range()

            # Appointments per Doctor
            cursor.execute(
                """
                INSERT INTO appointments_per_doctor (doctor_id, appointment_date, total_appointments)
                SELECT d.doctor_id, p.appointment_date, COUNT(*)
                FROM doctor d
                JOIN patient p ON d.name = p.requested_doctor
                WHERE p.appointment_date BETWEEN %s AND %s
                GROUP BY d.doctor_id, p.appointment_date
                ON DUPLICATE KEY UPDATE total_appointments = VALUES(total_appointments)
                """,
                (start_of_week, end_of_week)
            )

            # Appointment Trends
            cursor.execute(
                """
                INSERT INTO appointment_trends (period_start_date, period_end_date, total_appointments)
                SELECT %s, %s, COUNT(*)
                FROM patient p
                WHERE p.appointment_date BETWEEN %s AND %s
                """,
                (start_of_week, end_of_week, start_of_week, end_of_week)
            )

            # Symptoms by Specialty
            cursor.execute(
                """
                INSERT INTO symptoms_by_specialty (specialization, symptom, frequency)
                SELECT d.specialization, p.doctor_recommendation, COUNT(*)
                FROM doctor d
                JOIN patient p ON d.name = p.requested_doctor
                WHERE p.appointment_date BETWEEN %s AND %s
                GROUP BY d.specialization, p.doctor_recommendation
                ON DUPLICATE KEY UPDATE frequency = VALUES(frequency)
                """,
                (start_of_week, end_of_week)
            )

            connection.commit()
        return jsonify({"message": "Data aggregation and insertion completed successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Error aggregating data: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
