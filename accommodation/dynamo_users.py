import boto3
import uuid

from django.conf import settings
from botocore.exceptions import ClientError
from django.contrib.auth.hashers import check_password  # ✅ for verifying Django-style hashes

# ✅ DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'Users'
table = dynamodb.Table(table_name)


def get_user_from_dynamo(username_or_email):
    """Fetch user record by username or email from DynamoDB."""
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
        print("❌ Error fetching user:", e)
        return None


def verify_user_credentials(username_or_email, password):
    """Check if user credentials match in DynamoDB."""
    print(f"🟢 Starting DynamoDB login check for: {username_or_email}")
    
    user = get_user_from_dynamo(username_or_email)
    if user:
        print(f"✅ User found in DynamoDB: {user.get('username')} ({user.get('email')})")
        stored_password = user.get('password')
        print(f"🔸 Stored password hash: {stored_password}")

        if not stored_password:
            print(f"⚠️ User {username_or_email} has no password stored in DynamoDB.")
            return None

        if check_password(password, stored_password):  # ✅ safe comparison
            print("✅ Password matched successfully (from DynamoDB)")
            return user
        else:
            print("❌ Password mismatch — DynamoDB verification failed.")
    else:
        print(f"❌ No user record found in DynamoDB for: {username_or_email}")

    return None



def add_user_to_dynamo(user, role):
    """Save a new user to DynamoDB with required primary key."""
    try:
        user_id = str(uuid.uuid4())  # ✅ Add unique ID for DynamoDB key
        table.put_item(
            Item={
                "user_id": user_id,  # ✅ Primary key
                "username": user.username,
                "email": user.email,
                "password": user.password,  # ⚠️ Plaintext for now
                "role": role
            }
        )
        print(f"✅ Added user {user.username} to DynamoDB.")
    except ClientError as e:
        print("❌ Error adding user to DynamoDB:", e)