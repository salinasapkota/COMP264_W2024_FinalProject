"""
from chalice import Chalice, Response, BadRequestError, NotFoundError
from chalicelib.storageservice import user_exists, store_user, authenticate_user, reset_user_password, hash_password

app = Chalice(app_name='CardDetection')

@app.route('/signup', methods=['POST'])
def signup():
    request = app.current_request
    data = request.json_body
    email = data['email']
    password = data['password']
    
    # Hash the password securely
    hashed_password = hash_password(password)
    
    # Store the email and hashed password in DynamoDB
    store_user(email, hashed_password)
    
    return {'message': 'User signed up successfully'}

@app.route('/login', methods=['POST'])
def login():
    request = app.current_request
    data = request.json_body
    email = data['email']
    password = data['password']
    
    # Authenticate the user
    if authenticate_user(email, password):
        return {'message': 'Login successful'}
    else:
        raise BadRequestError('Invalid email or password')
    
"""

from chalice import Chalice, Response
import boto3

app = Chalice(app_name='card-detection')
ddb = boto3.resource('dynamodb')
user_table = ddb.Table('userTable')

TABLE_NAME_CARD_DETAILS = ddb.Table('CardDetails')

@app.route('/signup', methods=['POST'])
def signup():
    request = app.current_request
    data = request.json_body

    email = data.get('email') 
    password = data.get('password')
    first_name = data.get('first_name')  # New field
    last_name = data.get('last_name')    # New field

    if not email or not password or not first_name or not last_name:
        return Response(body={'message': 'Email, password, first name, and last name are required.'}, status_code=400)

    try:
        # Check if user already exists
        user_item = user_table.get_item(Key={'email': email}).get('Item')
        if user_item:
            return Response(body={'message': 'User already exists.'}, status_code=400)

        # Create new user
        user_table.put_item(Item={'email': email, 'password': password, 'first_name': first_name, 'last_name': last_name})
        return Response(body={'message': 'User signed up successfully.'}, status_code=200)
    except Exception as e:
        return Response(body={'message': str(e)}, status_code=500)

@app.route('/login', methods=['POST'])
def login():
    request = app.current_request
    data = request.json_body

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response(body={'message': 'Email and password are required.'}, status_code=400)

    try:
        #Check if user exists and password matches
        user_item = user_table.get_item(Key={'email': email}).get('Item')
        if user_item and user_item['password'] == password:
            return Response(body={'message': 'Login successful.'}, status_code=200)
        else:
            return Response(body={'message': 'Invalid email or password.'}, status_code=401)
    except Exception as e:
        return Response(body={'message': str(e)}, status_code=500)
    
def handle_reset_password(email, new_password):
    try:
        #Update user's password in DynamoDB
        user_table.update_item(
            Key={'email': email},
            UpdateExpression='SET password = :password',
            ExpressionAttributeValues={':password': new_password}
        )
        return {'message': 'Password reset successfully.'}, 200
    except Exception as e:
        return {'message': str(e)}, 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    request = app.current_request
    data = request.json_body

    if not data:
        return Response(body={'message': 'Request body is missing.'}, status_code=400)

    email = data.get('email')

    if not email:
        return Response(body={'message': 'Email is required.'}, status_code=400)

    # Check if user exists
    user_item = user_table.get_item(Key={'email': email}).get('Item')
    if not user_item:
        return Response(body={'message': 'User does not exist.'}, status_code=404)

    # Redirect user to reset password page
    return Response(status_code=302, headers={'Location': '/reset-password?email=' + email}, body='')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    request = app.current_request
    query_params = request.query_params
    email = query_params.get('email')

    if app.current_request.method == 'GET':
        # Handle GET request to display password reset page
        if not email:
            return Response(body={'message': 'Email is required.'}, status_code=400)

        # Render the password reset page
        # You can return an HTML page with a form for resetting the password
        return Response(body={'message': 'Please enter your new password.'}, status_code=200)

    elif app.current_request.method == 'POST':
        # Handle POST request to update password
        data = request.json_body
        new_password = data.get('new_password')

        if not new_password:
            return Response(body={'message': 'New password is required.'}, status_code=400)

        if not email:
            return Response(body={'message': 'Email is required.'}, status_code=400)

        return handle_reset_password(email, new_password)
    


    #update and delete endpoints
""""" 
from chalicelib import database
@app.route('/card/type/{card_type}', methods=['GET'])
def get_card_type(card_type):
    return database.get_card_type(card_type)

@app.route('/card/type', methods=['POST'])
def create_card_type():
    request = app.current_request
    data = request.json_body
    card_type = data.get('card_type')
    if card_type:
        database.create_card_type(card_type)
        return {'message': 'Card type created successfully'}
    else:
        return {'error': 'Card type not provided'}, 400
"""""

# Constants
def create_card_details(card_number, cardholder_name, expiry_date):
    table = ddb.Table(TABLE_NAME_CARD_DETAILS)  # Get the table resource
    table.put_item(
        Item={
            'CardNumber': card_number,
            'CardholderName': cardholder_name,
            'ExpiryDate': expiry_date
        }
    )

def get_card_details(card_number):
    response = ddb.get_item(TableName=TABLE_NAME_CARD_DETAILS, Key={'CardNumber': {'S': card_number}})
    return response.get('Item')

def update_card_details(card_number, updated_details):
    try:
        # Check if 'CardholderName' key exists in the updated_details dictionary
        if 'CardholderName' not in updated_details:
            raise ValueError("Missing 'CardholderName' key in updated_details dictionary")

        ddb.update_item(
            TableName=TABLE_NAME_CARD_DETAILS,
            Key={'CardNumber': {'S': card_number}},
            UpdateExpression='SET CardholderName = :name, ExpiryDate = :expiry',
            ExpressionAttributeValues={
                ':name': {'S': updated_details['CardholderName']},
                ':expiry': {'S': updated_details.get('ExpiryDate', '')}  # Get expiry date, handle if missing
            }
        )
        return True  # Update successful
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return False  # Update failed
    except Exception as e:
        print(f"Error updating card details: {e}")
        return False  # Update failed


def delete_card_details(card_number):
    ddb.delete_item(TableName=TABLE_NAME_CARD_DETAILS, Key={'CardNumber': {'S': card_number}})

@app.route('/card/details', methods=['POST'])
def post_card_details():  # Rename the endpoint function to avoid conflict
    request = app.current_request
    data = request.json_body
    card_number = data.get('card_number')
    cardholder_name = data.get('cardholder_name')
    expiry_date = data.get('expiry_date')
    if card_number and cardholder_name and expiry_date:
        create_card_details(card_number, cardholder_name, expiry_date)  # Call the function directly
        return {'message': 'Card details created successfully'}
    else:
        return {'error': 'Card details not provided'}, 400

@app.route('/card/details/{card_number}', methods=['PUT'])
def put_card_details(card_number):  # Adjust the endpoint function name accordingly
    request = app.current_request
    data = request.json_body
    updated_details = {
        'cardholder_name': data.get('cardholder_name'),
        'expiry_date': data.get('expiry_date')
    }
    update_card_details(card_number, updated_details)  # Call the function directly
    return {'message': 'Card details updated successfully'}

@app.route('/card/details/{card_number}', methods=['DELETE'])
def delete_card_details_endpoint(card_number):  # Adjust the endpoint function name accordingly
    delete_card_details(card_number)  # Call the function directly
    return {'message': 'Card details deleted successfully'}
