"""
import boto3
import hashlib

dynamodb = boto3.client('dynamodb')

# DynamoDB table name for storing user credentials
TABLE_NAME = 'Users'

def user_exists(email):
    # Checks if user exists in DynamoDB
    response = dynamodb.get_item(TableName=TABLE_NAME, Key={'email': {'S': email}})
    return 'Item' in response

def store_user(email, hashed_password):
    # Stores user credentials in DynamoDB
    dynamodb.put_item(TableName=TABLE_NAME, Item={'email': {'S': email}, 'password': {'S': hashed_password}})

def authenticate_user(email, password):
    #Authenticates user as per credentials stored in DynamoDB
    response = dynamodb.get_item(TableName=TABLE_NAME, Key={'email': {'S': email}})
    if 'Item' in response:
        stored_password = response['Item']['password']['S']
        return verify_password(password, stored_password)
    else:
        return False

def reset_user_password(email, hashed_password):
    # Reset users password in DynamoDB
    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={'email': {'S': email}},
        UpdateExpression='SET password = :password',
        ExpressionAttributeValues={':password': {'S': hashed_password}}
    )

def hash_password(password):
    # Hash password
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    # Verify password by comparing hashed passwords
    return hashed_password == hash_password(password)
"""