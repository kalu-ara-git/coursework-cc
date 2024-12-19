from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory database for simplicity
patients = {}


@app.route('/patients', methods=['POST'])
def create_patient():
    data = request.json
    patient_id = data.get('id')
    if patient_id in patients:
        return jsonify({"error": "Patient already exists"}), 400
    patients[patient_id] = data
    return jsonify({"message": "Patient created successfully"}), 201

@app.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = patients.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify(patient), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
