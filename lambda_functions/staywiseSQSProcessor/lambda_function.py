import json
import boto3

sns = boto3.client('sns')

def lambda_handler(event, context):
    print("📥 Received SQS Event:", json.dumps(event))

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            print("✅ Booking Message Parsed:", message)

            # Extract booking details
            name = message.get("name", "Customer")
            email = message.get("email", "N/A")
            room = message.get("room_name", "Unknown Room")
            base_price = message.get("price_before_discount", 0)
            final_price = message.get("final_price", 0)
            discount = message.get("discount_percent", 0)
            reason = message.get("discount_reason", "-")
            booked_on = message.get("booked_on", "N/A")

            # 📢 Manager Notification Message
            subject = f"📢 New Booking Alert - {room}"
            body = f"""
📢 NEW BOOKING ALERT

A customer named {name} ({email}) has made a booking through StayWise.

🏠 Room: {room}
💰 Base Price: €{base_price}
💸 Final Price: €{final_price}
🎁 Discount: {discount}% ({reason})
📅 Booked On: {booked_on}

Please check your StayWise Manager Dashboard for more details.
"""

            topic_arn = "arn:aws:sns:us-east-1:746813293947:staywise-bookings"  # ✅ Replace with your SNS ARN

            response = sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=body
            )

            print("✅ SNS Notification sent successfully!")
            print("📨 Message ID:", response['MessageId'])

        except Exception as e:
            print("❌ Error processing booking record:", e)

    return {"statusCode": 200, "body": "Processed SQS booking messages successfully."}
