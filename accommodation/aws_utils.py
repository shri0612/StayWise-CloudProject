import boto3
import json
from decimal import Decimal


# Inserting the booking data to the DynamoDB table named Bookings
def insert_booking_to_dynamodb(booking_data):
    """Insert booking into DynamoDB, trigger SNS, and send to SQS."""
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Bookings')

    # Creating proper fields to store booking data in the DynamoDB table name "Bookings"
    # All the booking details will stored in the dynamoDB table named Bookings
    item = {
        'booking_id': str(booking_data.get('booking_id')),
        'room_id': str(booking_data.get('room_id')),
        'room_name': booking_data.get('room_name', 'Unknown Room'),  # ✅ Added line
        'name': booking_data.get('name'),
        'email': booking_data.get('email'),
        'days': int(booking_data.get('days', 1)),
        'people': int(booking_data.get('people', 1)),
        'price_before_discount': Decimal(str(booking_data.get('price_before_discount', 0))),
        'final_price': Decimal(str(booking_data.get('final_price', 0))),
        'payment_method': booking_data.get('payment_method', 'Cash on Arrival'),
        'payment_status': booking_data.get('payment_status', 'Unpaid'),
        'booked_on': str(booking_data.get('booked_on', '')),
        'discount_percent': Decimal(str(booking_data.get('discount_percent', 0))),
        'discount_amount': Decimal(str(booking_data.get('discount_amount', 0))),
        'discount_reason': booking_data.get('discount_reason', '-'),
        'booked_by_email': booking_data.get('booked_by_email'),
    }

    # The below code helps to insert the booking details in to the DynamoDB table
    table.put_item(Item=item)

    try:
        send_to_sqs(item)
    except Exception as e:
        print("could not send booking to SQS:", e)

    return True


# Sending the booking message to the SQS to queue the booking details
def send_to_sqs(booking_data):
    """Sending booking data to SQS queue for asyncronous processing."""
    sqs = boto3.client('sqs', region_name='us-east-1')

    queue_url = "https://sqs.us-east-1.amazonaws.com/746813293947/StayWiseBookingQueue"  

    try:
        message_body = json.dumps(booking_data, default=str)
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )

        # print("booking message sent to SQS successfully!")
        # print("queue URL:", queue_url)
        # print("Message ID:", response.get("MessageId"))
        return True

    except Exception as e:
        print("error sending message to SQS:", e)
        return False
