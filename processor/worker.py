import boto3
import json
import os
import time
from process import process
from dotenv import load_dotenv

AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')
SQS_URL = os.getenv('SQS_URL')
s3 = boto3.client('s3', region_name=AWS_REGION)

download_dir = 'input'

def fetch_s3_object(bucket_name, object_key):
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    data = response['Body'].read()
    return data

def process_message(message_body):
    message = json.loads(message_body)
    print(message)
    if "Records" in message:
        for record in message['Records']:
            try:
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']
                data = fetch_s3_object(bucket_name, object_key)        
                process(data, object_key)
            except Exception as e:
                print(e)

def poll_sqs():
    while True:

        response = sqs.receive_message(
            QueueUrl=SQS_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5
        )

        messages = response.get('Messages', [])

        for message in messages:
            message_body = message['Body']

            process_message(message_body)

            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(
                QueueUrl=SQS_URL,
                ReceiptHandle=receipt_handle
            )

        time.sleep(1)

if __name__ == '__main__':
    poll_sqs()