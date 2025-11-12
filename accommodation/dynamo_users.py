import boto3
import uuid

from django.conf import settings
from botocore.exceptions import ClientError
from django.contrib.auth.hashers import check_password  # for verifying Django-style hashes

# DnamoDB setup to handle user login data
# There is a seperate helper function(dynamodb_helper.py) created which helps to create the table Users if it doesnot exist
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'Users'
table = dynamodb.Table(table_name)

"""Fetching the user records by username or email from DynamoDB."""
def get_user_from_dynamo(username_or_email):
    
    try:
        response = table.scan(
            FilterExpression="username = :u or email = :e",
            ExpressionAttributeValues={
                ":u": username_or_email,
                ":e": username_or_email
            }
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except ClientError as e:
        # print("Error fetching user:", e)
        return None

""" verifying the user credentials with the password hash stored in the DynamoDB use table """
def verify_user_credentials(username_or_email, password):
    
    user = get_user_from_dynamo(username_or_email)
    if user:
        # print(f"User found in DynamoDB: {user.get('username')} ({user.get('email')})")
        stored_password = user.get('password')
        # print(f" Stored password hash: {stored_password}")

        if not stored_password:
            # print(f" User {username_or_email} has no password stored in DynamoDB.")
            return None

        if check_password(password, stored_password):  
            # print("Password matched successfully (from DynamoDB)")
            return user
        else:
            print("Password mismatch — DynamoDB verification failed.")
    else:
        print(f"No user record found in DynamoDB for: {username_or_email}")

    return None


# Inserting user details to the dynamo DB
def add_user_to_dynamo(user, role):
    
    try:
        user_id = str(uuid.uuid4())  # adding unique ID for DynamoDB key
        table.put_item(
            Item={
                "user_id": user_id,  # using user_id has the primary key
                "username": user.username,
                "email": user.email,
                "password": user.password,  
                "role": role
            }
        )
        # print(f"Added user {user.username} to DynamoDB.")
    except ClientError as e:
        print("Error adding user to DynamoDB:", e)