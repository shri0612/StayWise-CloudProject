import boto3
import botocore
from dynamodb_helper import ensure_all_tables
from lambda_setup import setup_lambda,create_lambda_if_missing

REGION = "us-east-1"
BUCKET_NAME = "studentaccommodation-media-shridharan"
QUEUE_NAME = "StayWiseBookingQueue"
TOPIC_NAME = "staywise-bookings"


# --------- S3 Bucket ---------
def ensure_s3_bucket():
    s3 = boto3.client('s3', region_name=REGION)

    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ S3 bucket '{BUCKET_NAME}' already exists.")
        return
    except botocore.exceptions.ClientError:
        print(f"🪄 Creating S3 bucket '{BUCKET_NAME}'...")

        # us-east-1 special rule
        try:
            if REGION == "us-east-1":
                s3.create_bucket(Bucket=BUCKET_NAME)
            else:
                s3.create_bucket(
                    Bucket=BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': REGION}
                )
            print("🎉 S3 bucket created!")

        except Exception as e:
            print(f"❌ Failed to create S3 bucket: {e}")


# --------- SQS Queue ---------
def ensure_sqs_queue():
    sqs = boto3.client('sqs', region_name=REGION)

    try:
        queues = sqs.list_queues().get('QueueUrls', [])
    except Exception:
        queues = []

    # Check if exists
    for q in queues:
        if q.endswith(f"/{QUEUE_NAME}"):
            print(f"✅ SQS queue '{QUEUE_NAME}' already exists.")
            return q

    # Create new queue
    print(f"🪄 Creating SQS queue '{QUEUE_NAME}'...")
    try:
        response = sqs.create_queue(QueueName=QUEUE_NAME)
        print("🎉 SQS queue created!")
        return response['QueueUrl']
    except Exception as e:
        print(f"❌ Failed to create SQS queue: {e}")


# --------- SNS Topic (Create if missing) ---------
def ensure_sns_topic():
    sns = boto3.client('sns', region_name=REGION)

    # Check existing topics
    try:
        topics = sns.list_topics().get("Topics", [])
    except Exception:
        topics = []

    for t in topics:
        if t["TopicArn"].endswith(f":{TOPIC_NAME}"):
            print(f"✅ SNS topic '{TOPIC_NAME}' already exists.")
            return t["TopicArn"]

    # Create topic
    print(f"🪄 Creating SNS topic '{TOPIC_NAME}'...")
    try:
        response = sns.create_topic(Name=TOPIC_NAME)
        new_arn = response["TopicArn"]
        print(f"🎉 SNS topic created! ARN: {new_arn}")
        return new_arn
    except Exception as e:
        print(f"❌ Failed to create SNS topic: {e}")


# --------- Main Driver ---------
if __name__ == "__main__":
    print("🚀 Setting up AWS resources...\n")

    # 1️⃣ Create DynamoDB tables
    ensure_all_tables()

    # 2️⃣ Create S3
    ensure_s3_bucket()

    # 3️⃣ Create SQS queue
    queue_url = ensure_sqs_queue()

    # 4️⃣ Create SNS topic
    new_topic_arn = ensure_sns_topic()

    # 5️⃣ Create Lambda if missing
    from lambda_setup import create_lambda_if_missing, setup_lambda

    # Get AWS account ID for building role ARN
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    role_arn = f"arn:aws:iam::{account_id}:role/LabRole"

    # Path to ZIP file
    zip_path = "../lambda_functions/staywiseSQSProcessor/staywiseSQSProcessor.zip"

    print("\n🔍 Checking Lambda...")
    created = create_lambda_if_missing(zip_path, role_arn)

    if created:
        # 6️⃣ Configure Lambda (trigger, environment, IAM)
        setup_lambda(queue_url, new_topic_arn, BUCKET_NAME)

    print("\n🎉 AWS setup complete!")
    print("==================================================")
    print(f"📌 S3 Bucket      : {BUCKET_NAME}")
    print(f"📌 SQS Queue URL  : {queue_url}")
    print(f"📌 SNS Topic ARN  : {new_topic_arn}")
    print(f"📌 Lambda Name    : staywiseSQSProcessor")
    print("==================================================")

