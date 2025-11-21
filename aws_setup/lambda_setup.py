import boto3
import json

REGION = "us-east-1"
LAMBDA_NAME = "staywiseSQSProcessor"
QUEUE_NAME = "StayWiseBookingQueue"

lambda_client = boto3.client('lambda', region_name=REGION)
sqs = boto3.client('sqs', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)
iam = boto3.client('iam')

def create_lambda_if_missing(zip_path, role_arn):
    print("🔍 Checking if Lambda function exists...")

    try:
        lambda_client.get_function(FunctionName=LAMBDA_NAME)
        print(f"✅ Lambda '{LAMBDA_NAME}' already exists.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"🪄 Lambda '{LAMBDA_NAME}' does NOT exist. Creating now...")

    # Create Lambda function
    try:
        with open(zip_path, "rb") as f:
            lambda_zip = f.read()

        lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.9",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": lambda_zip},
            Timeout=30,
            MemorySize=256,
            Publish=True,
        )

        print(f"🎉 Lambda '{LAMBDA_NAME}' created successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to create Lambda: {e}")
        return False



# --------- ATTACH SQS TRIGGER ---------
def attach_sqs_trigger(queue_url, sns_topic_arn):
    print(f"🔗 Attaching SQS trigger to Lambda '{LAMBDA_NAME}'...")

    # Get Lambda ARN
    lambda_arn = lambda_client.get_function(FunctionName=LAMBDA_NAME)["Configuration"]["FunctionArn"]

    # Add permission so SQS can invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId="SQSInvokePermission",
            Action="lambda:InvokeFunction",
            Principal="sqs.amazonaws.com",
            SourceArn=sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["QueueArn"]
            )["Attributes"]["QueueArn"]
        )
        print("✅ Added Lambda invoke permission for SQS.")
    except Exception:
        print("ℹ️ Permission already exists.")

    # Create Lambda Event Source Mapping
    try:
        lambda_client.create_event_source_mapping(
            EventSourceArn=sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["QueueArn"]
            )["Attributes"]["QueueArn"],
            FunctionName=LAMBDA_NAME,
            Enabled=True,
            BatchSize=1
        )
        print("🎉 SQS → Lambda trigger connected successfully!")
    except Exception as e:
        print("ℹ️ Trigger already exists.")


# --------- UPDATE LAMBDA ENVIRONMENT VARIABLES ---------
def update_lambda_env(bucket_name, sns_arn):
    print("🔧 Updating Lambda environment variables...")

    config = lambda_client.get_function_configuration(FunctionName=LAMBDA_NAME)
    env_section = config.get("Environment", {})
    env_vars = env_section.get("Variables", {})

    env_vars.update({
        "SNS_TOPIC_ARN": sns_arn,
        "S3_BUCKET_NAME": bucket_name,
        "REGION": REGION
    })

    lambda_client.update_function_configuration(
        FunctionName=LAMBDA_NAME,
        Environment={"Variables": env_vars}
    )
    print("🎉 Lambda environment variables updated!")


# --------- ATTACH IAM POLICY ---------
def attach_iam_permissions():
    print("🔐 Attaching Lambda permissions...")

    role_name = lambda_client.get_function(FunctionName=LAMBDA_NAME)["Configuration"]["Role"].split("/")[-1]

    # This policy includes SQS receive + SNS publish
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish"
                ],
                "Resource": "*"
            }
        ]
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="StayWiseLambdaSQSPolicy",
        PolicyDocument=json.dumps(policy_document)
    )

    print(f"🎉 IAM permissions attached to {role_name}!")


# --------- MAIN FUNCTION ---------
def setup_lambda(queue_url, sns_topic_arn, bucket_name):
    print("🚀 Running Lambda setup automation...\n")

    attach_sqs_trigger(queue_url, sns_topic_arn)
    update_lambda_env(bucket_name, sns_topic_arn)
    # attach_iam_permissions()

    print("\n🎉 Lambda setup completed successfully!")


# --------- IMPORT FROM MAIN SETUP SCRIPT ---------
if __name__ == "__main__":
    print("❌ This file is intended to be called from aws_resource_setup.py only.")
