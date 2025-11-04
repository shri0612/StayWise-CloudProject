#!/bin/bash
echo "🚀 Packaging and deploying Lambda function to AWS..."

cd lambda_functions/staywiseSQSProcessor || exit
zip -r ../staywiseSQSProcessor.zip . > /dev/null

aws lambda update-function-code \
  --function-name staywiseSQSProcessor \
  --zip-file fileb://../staywiseSQSProcessor.zip \
  --region us-east-1

echo "✅ Lambda code updated successfully!"

