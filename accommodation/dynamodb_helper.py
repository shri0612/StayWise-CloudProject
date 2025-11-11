import boto3

def ensure_table_exists(table_name, key_name, key_type='S'):
    """Create DynamoDB table if it doesn't exist."""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    try:
        tables = dynamodb.list_tables()['TableNames']
        if table_name in tables:
            print(f"✅ Table '{table_name}' already exists.")
            return

        print(f"🪄 Creating DynamoDB table '{table_name}'...")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': key_name, 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': key_name, 'AttributeType': key_type}],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Table '{table_name}' created successfully!\n")

    except Exception as e:
        print(f"⚠️ Could not create/check table '{table_name}':", e)


def ensure_all_tables():
    """Ensure all required DynamoDB tables exist for accommodation app."""
    ensure_table_exists('Users', 'user_id')
    ensure_table_exists('Bookings', 'booking_id')
    ensure_table_exists('Rooms', 'room_id')
