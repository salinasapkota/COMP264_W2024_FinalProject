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
        
    def get_user(self, user_id):
        response = self.user_table.get_item(
            Key={
                'userId': user_id
            }
        )

        return response
        

   

    