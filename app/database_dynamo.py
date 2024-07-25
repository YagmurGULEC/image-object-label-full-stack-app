"Database layer - the dynamo version"
import os
import boto3
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_DEFAULT_REGION'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'])
table = dynamodb.Table('Users')
# Define the table schema
table_schema = {
    "TableName": "Users",
    "AttributeDefinitions": [
        {
            "AttributeName": "email",
            "AttributeType": "S"
        }
    ],
    "KeySchema": [
        {
            "AttributeName": "email",
            "KeyType": "HASH"
        },
       
    ],
    "ProvisionedThroughput": {
        "ReadCapacityUnits": 5,
        "WriteCapacityUnits": 5
    }
}
    

def create_table(**table_schema):
    try:
        dynamodb.create_table(**table_schema)
    except Exception as e:
        print(e)


def dynamo_to_python(dynamo_object: dict) -> dict:
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v) 
        for k, v in dynamo_object.items()
    }  
  
def python_to_dynamo(python_object: dict) -> dict:
    serializer = TypeSerializer()
    return {
        k: serializer.serialize(v)
        for k, v in python_object.items()
    }
def list_users():
    "Select all the users from the database"
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('users')
        return table.scan()["Items"]
    except:
        return 0



def add_user(email, password, email_confirmed=False):
    try:
        table.put_item(
            Item={
                'email': email,
                'password': password,
                'email_confirmed': email_confirmed
            }
        )
        print(f"User with email {email} added successfully.")
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")

def update_email_confirmation(email, email_confirmed=True):
    try:
        response = table.update_item(
            Key={'email': email},
            UpdateExpression='SET email_confirmed = :val',
            ExpressionAttributeValues={':val': email_confirmed},
            ReturnValues='UPDATED_NEW'
        )
        print(f"Email confirmation updated successfully: {response['Attributes']}")
        return response['Attributes']
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")

def get_user(email):
    try:
        response = table.get_item(
            Key={'email': email}
        )
        if 'Item' in response:
            # print(f"User retrieved successfully: {response['Item']}")
            return response['Item']
        else:
            print(f"User with email {email} not found.")
            return None
    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None

    
def append_image(user_mail, new_image_data):
    
    response = table.get_item(Key={'email': "g@g.com"})
    if 'Item' not in response:
        print ("Item not found")
        return None
    item = response['Item']
    current_image_data = item.get('image_data', [])
    current_image_data.append(new_image_data)
    response = table.update_item(
        Key={'email': user_mail},
        UpdateExpression="set image_data = :data",
        ExpressionAttributeValues={':data': current_image_data},
        ReturnValues="UPDATED_NEW"
    )
    return response



   