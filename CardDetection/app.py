from chalice import Chalice, Response, CORSConfig
import boto3
from chalicelib import storage_service
from chalicelib import recognition_service
from chalicelib import translation_service
from chalicelib import dynamodb_service
from chalicelib import comprehend_service
import uuid

from datetime import datetime, timedelta
from jose import jwt
import base64
import json
app = Chalice(app_name='CardDetection')
app.debug = True


#####
# services initialization
#####
storage_location = 'contentcen301232187.aws.ai'
storage_service = storage_service.StorageService(storage_location)
recognition_service = recognition_service.RecognitionService(storage_service)
translation_service = translation_service.TranslationService()

comprehend_service = comprehend_service.ComprehendService()
dynamodb_service = dynamodb_service.DynamoService()
SECRET_KEY = 'lkjhgfdsa'


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#


app = Chalice(app_name='card-detection')
ddb = boto3.resource('dynamodb')
user_table = ddb.Table('UserTable')
TABLE_NAME_CARD_DETAILS = ddb.Table('CardDetails')

#Salina's Endpoints(Registration)
@app.route('/signup', methods=['POST'], cors=True)
def signup():
    request = app.current_request
    data = request.json_body

    email = data.get('email') 
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    usertype = data.get('usertype')

    if not email or not password or not first_name or not last_name or not usertype:
        return Response(body={'message': 'Please enter all the details.'}, status_code=400)

    if usertype not in ['admin', 'user']:
        return Response(body={'message': 'Invalid user type. Please select either "admin" or "user".'}, status_code=400)

    try:
        #Checks if user already exists
        user_item = user_table.get_item(Key={'email': email}).get('Item')
        if user_item:
            return Response(body={'message': 'User already exists.'}, status_code=400)

        #Creates new user
        user_table.put_item(Item={'email': email, 'password': password, 'first_name': first_name, 'last_name': last_name, 'usertype': usertype})
        return Response(body={'message': 'User signed up successfully.'}, status_code=200)
    except Exception as e:
        return Response(body={'message': str(e)}, status_code=500)

@app.route('/login', methods=['POST'],cors=True)
def login():
    request = app.current_request
    data = request.json_body
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response(body={'message': 'Email and password are required.'}, status_code=400)

    try:
        #Checks if user exists and password matches
        user_item = user_table.get_item(Key={'email': email}).get('Item')
        if user_item and user_item['password'] == password:
            #Generate JWT token
            token = jwt.encode({'email': email, 'exp': datetime.utcnow() + timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
            return Response(body={'token': token}, status_code=200)
        else:
            return Response(body={'message': 'Invalid email or password.'}, status_code=401)
    except Exception as e:
        return Response(body={'message': str(e)}, status_code=500)

def authenticate(func):
    def wrapper(*args, **kwargs):
        token = app.current_request.headers.get('Authorization')
        if not token:
            return Response(body={'message': 'Missing token'}, status_code=401)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return func(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return Response(body={'message': 'Token has expired'}, status_code=401)
        except jwt.InvalidTokenError:
            return Response(body={'message': 'Invalid token'}, status_code=401)
    return wrapper

    
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

@app.route('/forgot-password', methods=['POST'], cors=True)
def forgot_password():
    request = app.current_request
    data = request.json_body

    if not data:
        return Response(body={'message': 'Request body is missing.'}, status_code=400)

    email = data.get('email')

    if not email:
        return Response(body={'message': 'Email is required.'}, status_code=400)

    #Check if user exists
    user_item = user_table.get_item(Key={'email': email}).get('Item')
    if not user_item:
        return Response(body={'message': 'User does not exist.'}, status_code=404)

    #Redirect user to reset password page
    return Response(status_code=302, headers={'Location': '/reset-password?email=' + email}, body='')

@app.route('/reset-password', methods=['GET', 'POST'], cors=True)
def reset_password():
    request = app.current_request
    query_params = request.query_params
    email = query_params.get('email')

    if app.current_request.method == 'GET':
        #Handle GET request to display password reset page
        if not email:
            return Response(body={'message': 'Email is required.'}, status_code=400)

        return Response(body={'message': 'Please enter your new password.'}, status_code=200)

    elif app.current_request.method == 'POST':
        #Handle POST request to update password
        data = request.json_body
        new_password = data.get('new_password')
        input_email = data.get('email')#gets email from the reset password form


        if not new_password:
            return Response(body={'message': 'New password is required.'}, status_code=400)

        if not input_email:
            return Response(body={'message': 'Email is required.'}, status_code=400)

        if input_email != email:  #Checks if the emails matches
            return Response(body={'message': 'Invalid email.'}, status_code=400)

        #Continues with updating the password only if the emails match
        return handle_reset_password(email, new_password)
    
@app.route('/logout', methods=['POST'])
def logout():
    return Response(body={'message': 'Logged out successfully.'}, status_code=200)

#####
# RESTful endpoints
#####
@app.route('/images', methods = ['POST'], cors = True)
def upload_image():
    """processes file upload and saves file to storage service"""
    request_data = json.loads(app.current_request.raw_body)
    file_name = request_data['filename']
    file_bytes = base64.b64decode(request_data['filebytes'])

    image_info = storage_service.upload_file(file_bytes, file_name)

    return image_info



@app.route('/images/{image_id}/translate-text', methods = ['POST'], cors = True)
def translate_image_text(image_id):
    """detects then translates text in the specified image"""
    request_data = json.loads(app.current_request.raw_body)
    from_lang = request_data['fromLang']
    to_lang = request_data['toLang']

    MIN_CONFIDENCE = 80.0

    text_lines = recognition_service.detect_text(image_id)

    translated_lines = []
    for line in text_lines:
        # check confidence
        if float(line['confidence']) >= MIN_CONFIDENCE:
            translated_line = translation_service.translate_text(line['text'], from_lang, to_lang)

            translated_lines.append({
                'text': line['text'],
                'translation': translated_line,
                'boundingBox': line['boundingBox']
            })

    return translated_lines

@app.route('/images/{image_id}/analyze-entities', methods=['POST'], cors=True)
def analyze_entities(image_id):
    """Detects entities in the text of the specified image"""
    request_data = json.loads(app.current_request.raw_body)
    text = request_data['text']

    # Analyze entities using Comprehend
    entities = comprehend_service.detect_entities(text)
    return {'entities': entities}


####################
from chalicelib import database
@app.route('/card/type/{card_type}', methods=['GET'])
def get_card_type(card_type):
    return database.get_card_type(card_type)


@app.route('/card/details/{card_number}', methods=['GET'])
def get_card_details(card_number):
    return database.get_card_details(card_number)

@app.route('/card/details', methods=['POST'])
def create_card_details():
    request = app.current_request
    data = request.json_body
    card_number = data.get('card_number')
    
    cardholder_name = data.get('cardholder_name')
    expiry_date = data.get('expiry_date')
    if card_number and cardholder_name and expiry_date:
        database.create_card_details(card_number, cardholder_name, expiry_date)
        return {'message': 'Card details created successfully'}
    else:
        return {'error': 'Card details not provided'}, 400

@app.route('/card/details/{card_number}', methods=['PUT'])
def update_card_details(card_number):
version1
    request = app.current_request
    data = request.json_body
    updated_details = {
        'CardholderName': data.get('cardholder_name'),
        'expiry_date': data.get('expiry_date')
    }
    try:
        database.update_card_details(card_number, updated_details)
    except Exception as e:
        print(e)
        return {'message': 'Card details  not updated successfully'}
    
    return {'message': 'Card details updated successfully'}
=======
    try:
        request = app.current_request
        data = request.json_body
        updated_details = {
            'CardholderName': data.get('cardholder_name'),
            'ExpiryDate': data.get('expiry_date')
        }
        database.update_card_details(card_number, updated_details)
        return {'message': 'Card details updated successfully'}
    except Exception as e:
        return {'error': str(e)}, 500

 Arun

@app.route('/card/details/{card_number}', methods=['DELETE'])
def delete_card_details(card_number):
    database.delete_card_details(card_number)
    return {'message': 'Card details deleted successfully'}


########Ariya############

@app.route('/text/comprehend', methods=['POST'], cors=True)
def comprehend_text():
    """Comprehends what is each element in the given translations"""
    # try:
    request_data = json.loads(app.current_request.raw_body)
    joined_text = ' '.join([line['translation']['translatedText'] for line in request_data])

    name_position = joined_text.find("NOM") + 3
    joined_text = joined_text[name_position:]
    print("#############################Ariya:",joined_text)

   
    
    print(joined_text) #DEBUG
    tags = comprehend_service.detect_medical_entities(joined_text)
    print("---------------------------------------------------------")
    print(tags)

    return tags



# Assuming DynamoService is imported and configured properly




@app.route('/users', methods=['POST'], cors=True)
def create_user():
    try:
        # Parse the request body
        request_data = json.loads(app.current_request.raw_body)

        # Generate a unique user ID
        user_id = str(uuid.uuid4())
        name = request_data.get('name')
        
        if not name:  # Check if the name is provided
            return Response(body={'message': 'Name is required'}, status_code=400)

        # Call DynamoService to create a new user entry
        response = dynamodb_service.create_user(user_id, request_data)

        # Return a success response with the new user_id
        return {'message': 'User created successfully', 'userId': user_id}

    except Exception as e:
        return Response(body={'message': str(e)}, status_code=400)

    
@app.route('/users/{user_id}', methods=['GET'], cors=True)
def get_user_details(user_id):
    try:
        # Retrieve user details from DynamoDB using the provided user_id
        user_data = dynamodb_service.get_user(user_id)
        
        # Check if user_data has content
        if user_data and 'Item' in user_data:
            # Return the user details
            return user_data['Item']
        else:
            # User not found
            return Response(body={'message': 'User not found'}, status_code=404)
    
    except Exception as e:
        # Log the exception and return a 500 error
        app.log.error(f"Error retrieving user details: {str(e)}")
        return Response(body={'message': 'Internal Server Error'}, status_code=500)

@app.route('/users/{user_id}', methods=['PUT'])
def update_user(user_id):
    request = app.current_request
    request_data = request.json_body

    try:
        response = dynamodb_service.update_user(user_id, request_data)
        # Check if the update was acknowledged with any returned attributes
        if 'Attributes' in response:
            return {'message': 'User details updated successfully'}
        else:
            # Log or handle the case where no attributes are returned
            app.log.info('Update executed but no attributes were returned.')
            return {'message': 'Update executed, no attributes to return'}, 200

    except Exception as e:
        # Log the error and return a more generic server error message
        app.log.error(f'Failed to update user details: {e}')
        return Response(body={'error': 'Failed to update user details due to an internal error'}, status_code=500)


@app.route('/users/{user_id}', methods=['DELETE'])
def delete_user(user_id):
    response = dynamodb_service.delete_user(user_id)
    if 'ResponseMetadata' in response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return {'message': 'User deleted successfully'}
    else:
        return {'error': 'Failed to delete user'}, 400
    

