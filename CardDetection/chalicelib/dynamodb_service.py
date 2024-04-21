import boto3
from botocore.exceptions import ClientError
import time as timestamp_logger
import uuid as unique_id_generator
from chalice import Chalice, Response  # Import Response


class DynamoService:
    def __init__(self):
        self.client = boto3.resource('dynamodb')
        self.user_table_name = 'users'
        self.user_table = self.client.Table(self.user_table_name)
        if not self._table_exists(self.user_table_name):
            self._create_table(self.user_table_name)

    def _table_exists(self, table_name):
        try:
            self.client.Table(table_name).load()
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise
        else:
            return True

    def _create_table(self, table_name):
        try:
            self.client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'userId',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'userId',
                        'AttributeType': 'S'  # String
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
        except ClientError as err:
            print(f"Error creating DynamoDB table: {err}")
            raise

    def create_user(self, user_id, request_data):
        # Log the incoming request data
        print(request_data)

        # Ensure the 'userId' is included in the request_data dictionary
        request_data['userId'] = user_id

        # Use the request_data dictionary directly as the item to be put in the DynamoDB table
        response = self.user_table.put_item(Item=request_data)

        # Print a separator for clarity in logs
        print("*" * 30)
        print('Response:', response)

        # Return a response or the response object itself depending on your application's needs
        return response
        
    #     return response
    def get_user(self, user_id):
        try:
            response = self.user_table.get_item(Key={'userId': user_id})
            return response
        except ClientError as err:
            app.log.error(f"Error retrieving user from DynamoDB: {err}")
            raise

    

    def get_user_attributes(self, user_id):
        try:
            response = self.user_table.get_item(
                Key={
                    'userId': user_id
                },
                ProjectionExpression='#n, location, DOB, IssuedDate, ExpiredDate',
                ExpressionAttributeNames={'#n': 'name'}  
            )
            return response['Item'] if 'Item' in response else None
        except ClientError as err:
            raise RuntimeError(f"Error getting user attributes: {err}")
        
    # def update_user(self, user_id, request_data):
    #     response = self.user_table.update_item(
    #         Key={'userId': user_id},
    #         UpdateExpression='SET name = :n, location = :l, DOB = :d, IssuedDate = :i, ExpiredDate = :e',
    #         ExpressionAttributeValues={
    #             ':n': request_data.get('name'),
    #             ':l': request_data.get('location'),
    #             ':d': request_data.get('DOB'),
    #             ':i': request_data.get('IssuedDate'),
    #             ':e': request_data.get('ExpiredDate')
    #         },
    #         ReturnValues='UPDATED_NEW'
    #     )

    #     return response



    def delete_user(self, user_id):
        response = self.user_table.delete_item(
            Key={'userId': user_id}
        )

        return response
    
    def update_user(self, user_id, request_data):
        try:
            # Prepare the update expression components
            update_expression = "SET "
            expression_attribute_names = {}
            expression_attribute_values = {}

            # Loop through the request data items
            for key, value in request_data.items():
                # Clean key to remove spaces and colons
                clean_key = key.replace(" ", "").replace(":", "")
                
                # Use a placeholder for the attribute name and value
                attribute_name_placeholder = f"#{clean_key}"
                attribute_value_placeholder = f":{clean_key}"

                # Add the placeholders to the respective dictionaries
                expression_attribute_names[attribute_name_placeholder] = key
                expression_attribute_values[attribute_value_placeholder] = value

                # Append the key-value pair to the update expression
                update_expression += f"{attribute_name_placeholder} = {attribute_value_placeholder}, "

            # Remove trailing comma and space from the update expression
            update_expression = update_expression.rstrip(", ")

            # Perform the update operation
            response = self.user_table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )
            return response
        except ClientError as err:
            # Handle any exceptions raised by the client
            print(f"Error updating user: {err}")
            raise

        

   

    
   

    