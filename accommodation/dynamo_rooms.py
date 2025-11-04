import boto3
from decimal import Decimal
import uuid

# ✅ Initialize DynamoDB connection
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# ✅ Reference your DynamoDB table
rooms_table = dynamodb.Table('Rooms')  # change name if your table is different


# ✅ Fetch all rooms
def get_all_rooms():
    """Fetch all rooms from DynamoDB"""
    response = rooms_table.scan()
    return response.get('Items', [])


# ✅ Fetch a single room
def get_room_from_dynamo(room_id):
    """Fetch a specific room by ID"""
    response = rooms_table.get_item(Key={'room_id': room_id})
    return response.get('Item')


# ✅ Add a new room (supports S3 images)
def add_room_to_dynamo(name, capacity, price, image_urls=None):
    """Add a new room record to DynamoDB with optional S3 image URLs"""
    from decimal import Decimal, InvalidOperation

    room_id = str(uuid.uuid4())

    # ✅ Handle empty or invalid price safely
    try:
        price_value = Decimal(str(price)) if str(price).strip() != '' else Decimal('0.00')
    except (InvalidOperation, TypeError, ValueError):
        price_value = Decimal('0.00')

    # ✅ Handle missing or invalid capacity safely
    try:
        capacity_value = int(capacity)
    except (TypeError, ValueError):
        capacity_value = 0

    item = {
        'room_id': room_id,
        'name': name or "Unnamed Room",
        'capacity': capacity_value,
        'price': Decimal(str(price)),
        'available': True,
        'images': image_urls or []
    }

    rooms_table.put_item(Item=item)
    print("✅ Room added successfully to DynamoDB:", item)
    return room_id



# ✅ Update room details
def update_room_in_dynamo(room_id, name, capacity, price):
    """Update room details (name, capacity, price, availability)"""
    capacity = int(capacity)
    price = Decimal(str(price))
    available = capacity > 0

    response = rooms_table.update_item(
        Key={'room_id': room_id},
        UpdateExpression="SET #n = :name, #c = :capacity, price = :price, available = :available",
        ExpressionAttributeNames={
            '#n': 'name',
            '#c': 'capacity'
        },
        ExpressionAttributeValues={
            ':name': name,
            ':capacity': capacity,
            ':price': price,
            ':available': available
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


# ✅ Update or remove image URLs
def update_room_images_in_dynamo(room_id, image_urls=None, remove=False):
    """
    Add or remove S3 image URLs from a room's 'images' list.

    remove=True → deletes image URLs
    remove=False → appends new image URLs
    """
    if remove:
        # When removing, replace the full list with remaining URLs
        existing = get_room_from_dynamo(room_id)
        if not existing or 'images' not in existing:
            return None

        remaining = [url for url in existing['images'] if url not in (image_urls or [])]

        response = rooms_table.update_item(
            Key={'room_id': room_id},
            UpdateExpression="SET images = :remaining",
            ExpressionAttributeValues={':remaining': remaining},
            ReturnValues="UPDATED_NEW"
        )
        return response

    # When adding new images
    if not image_urls:
        return None

    response = rooms_table.update_item(
        Key={'room_id': room_id},
        UpdateExpression="SET images = list_append(if_not_exists(images, :empty), :new_images)",
        ExpressionAttributeValues={
            ':new_images': image_urls,
            ':empty': []
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


# ✅ Delete a room
def delete_room_from_dynamo(room_id):
    """Delete a room record from DynamoDB"""
    response = rooms_table.delete_item(Key={'room_id': room_id})
    return response
