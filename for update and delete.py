from chalice import Chalice
import uuid

app = Chalice(app_name='data-api')

# Dummy database for users and data
users = {}
data_store = {}

# Function to generate unique data ID
def generate_data_id():
    return str(uuid.uuid4())

# Endpoint for updating data
@app.route('/update-data/{data_id}', methods=['PUT'])
def update_data(data_id):
    request_data = app.current_request.json_body
    if data_id not in data_store:
        return {"message": "Data not found"}, 404
    data_store[data_id].update(request_data)
    return {"message": "Data updated successfully"}

# Endpoint for deleting data
@app.route('/delete-data/{data_id}', methods=['DELETE'])
def delete_data(data_id):
    if data_id not in data_store:
        return {"message": "Data not found"}, 404
    del data_store[data_id]
    return {"message": "Data deleted successfully"}

# Route to create sample data for testing
@app.route('/create-sample-data', methods=['POST'])
def create_sample_data():
    request_data = app.current_request.json_body
    data_id = generate_data_id()
    data_store[data_id] = request_data
    return {"message": "Sample data created successfully", "data_id": data_id}, 201

# Route to display content
@app.route('/display-content', methods=['GET'])
def display_content():
    return data_store

