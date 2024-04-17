import boto3
import botocore.exceptions


# Initialize AWS client
dynamodb = boto3.client('dynamodb')

# Constants
TABLE_NAME_CARD_DETAILS = 'CardDetails'

def create_card_details(card_number, cardholder_name, expiry_date):
    dynamodb.put_item(
        TableName=TABLE_NAME_CARD_DETAILS,
        Item={
            'CardNumber': {'S': card_number},
            'CardholderName': {'S': cardholder_name},
            'ExpiryDate': {'S': expiry_date}
        }
    )

def get_card_details(card_number):
    response = dynamodb.get_item(TableName=TABLE_NAME_CARD_DETAILS, Key={'CardNumber': {'S': card_number}})
    return response.get('Item')
def update_card_details(card_number, updated_details):
    try:
        # Check if 'CardholderName' key exists in the updated_details dictionary
        if 'CardholderName' not in updated_details:
            raise ValueError("Missing 'CardholderName' key in updated_details dictionary")
        
        # Get the expiry date from updated_details, handle if missing
        expiry_date = updated_details.get('ExpiryDate', '')

        dynamodb.update_item(
            TableName=TABLE_NAME_CARD_DETAILS,
            Key={'CardNumber': {'S': card_number}},
            UpdateExpression='SET CardholderName = :name, ExpiryDate = :expiry',
            ExpressionAttributeValues={
                ':name': {'S': updated_details['CardholderName']},
                ':expiry': {'S': expiry_date}  # Use the provided expiry date or an empty string if missing
            }
        )
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except KeyError as ke:
        print(f"KeyError: {ke}")
    except botocore.exceptions.ClientError as ce:
        print(f"ClientError: {ce}")
    except Exception as e:
        print(f"Error updating card details: {e}")


def delete_card_details(card_number):
    dynamodb.delete_item(TableName=TABLE_NAME_CARD_DETAILS, Key={'CardNumber': {'S': card_number}})
