import boto3
import json
from decimal import Decimal


# ======================================================
# ✅ INSERT BOOKING INTO DYNAMODB + SNS + SQS
# ======================================================
def insert_booking_to_dynamodb(booking_data):
    """Insert booking into DynamoDB, trigger SNS, and send to SQS."""
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Bookings')

    # 🧩 Prepare the item for DynamoDB
    item = {
        'booking_id': str(booking_data.get('booking_id')),
        'room_id': str(booking_data.get('room_id')),
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
    }

    # ✅ Save booking to DynamoDB
    table.put_item(Item=item)
    print("\n✅ Booking inserted into DynamoDB:")
    print("🆔 Booking ID:", item["booking_id"])
    print("🏠 Room:", item["room_id"])
    print("💰 Final Price: €", item["final_price"])
    print("🎁 Discount Applied:", item["discount_percent"], "% -", item["discount_reason"])

   
    try:
        print("\n📦 Sending booking details to SQS...")
        send_to_sqs(item)
    except Exception as e:
        print("⚠️ Could not send booking to SQS:", e)

    return True


# ======================================================
# 📦 SEND BOOKING MESSAGE TO SQS
# ======================================================
def send_to_sqs(booking_data):
    """Send booking data to SQS queue for async processing."""
    sqs = boto3.client('sqs', region_name='us-east-1')

    queue_url = "https://sqs.us-east-1.amazonaws.com/746813293947/StayWiseBookingQueue"  

    try:
        message_body = json.dumps(booking_data, default=str)
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )

        print("✅ Booking message sent to SQS successfully!")
        print("📦 Queue URL:", queue_url)
        print("📨 Message ID:", response.get("MessageId"))
        return True

    except Exception as e:
        print("❌ Error sending message to SQS:", e)
        return False
