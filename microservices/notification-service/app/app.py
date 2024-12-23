import pymysql
from flask import Flask, request, jsonify
from werkzeug.exceptions import InternalServerError
from datetime import datetime, timedelta
import os
import boto3
from botocore.exceptions import ClientError

# Initialize Flask app
app = Flask(__name__)

# MySQL credentials (hardcoded for debugging purposes)
db_username = os.getenv("DB_USERNAME")  # MySQL username from secrets
db_password = os.getenv("DB_PASSWORD")  # MySQL password from secrets
db_host = 'healthsync-db.c5u0mm4k6d06.us-east-1.rds.amazonaws.com'
db_name = 'healthsync'
db_port = 3306  # Default MySQL port

# Initialize SES client
ses_client = boto3.client('ses', region_name='us-east-1')

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

# Helper function to send email using SES
def send_email(to_email, name, doctor_name, appointment_date, appointment_time):
    try:
        subject = "HealthSync Appointment Reminder"
        body_text = (
            f"Dear {name},\n\n"
            f"This is a reminder about your scheduled appointment.\n"
            f"Doctor: {doctor_name}\n"
            f"Appointment Date: {appointment_date}\n"
            f"Appointment Time: {appointment_time}\n\n"
            f"Please contact us for any queries.\n\n"
            f"Thank you,\nHealthSync Team"
        )

        # Send the email using SES
        response = ses_client.send_email(
            Source='useramazonuser2@gmail.com',  # Your verified email address
            Destination={
                'ToAddresses': [to_email],
            },
            Message={
                'Subject': {
                    'Data': subject,
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                    },
                },
            },
        )
        print(f"Email sent successfully: {response['MessageId']}")
        return True
    except ClientError as e:
        print(f"Failed to send email: {e.response['Error']['Message']}")
        return False

# Route to send appointment reminder emails
@app.route('/send-appointment-reminders', methods=['GET'])
def send_appointment_reminders():
    # Get tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.date()

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch all patients with appointments for tomorrow
            cursor.execute(
                """
                SELECT patient_id, name, requested_doctor, appointment_time, appointment_date, email
                FROM patient
                WHERE appointment_date = %s
                """, (tomorrow_date,)
            )
            appointments = cursor.fetchall()

            if not appointments:
                return jsonify({"message": "No appointments found for tomorrow"}), 404

            # Send email to each patient
            for appointment in appointments:
                name = appointment['name']
                doctor_name = appointment['requested_doctor']
                appointment_time = appointment['appointment_time']
                email = appointment['email']

                # Send reminder email
                if send_email(email, name, doctor_name, tomorrow_date, appointment_time):
                    print(f"Reminder sent to {name} ({email})")
                else:
                    print(f"Failed to send reminder to {name} ({email})")

            return jsonify({"message": "Appointment reminders sent successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Error sending appointment reminders: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()

# Start the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
