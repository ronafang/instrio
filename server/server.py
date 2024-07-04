from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')

s3_client = boto3.client('s3', region_name=AWS_REGION)


@app.post("/upload-audio-url/")
def generate_signed_url():
    try:
        task_id = uuid.uuid4()
        input_file_name = f"input/{task_id}.wav"
        input_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': S3_BUCKET, 'Key': input_file_name, 'ContentType': "audio/wav"},
            ExpiresIn=3600
        )
        output_file_name = f"output/{task_id}.wav"
        output_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': output_file_name},
            ExpiresIn=3600
        )
        return {"input_url": input_url, "output_url": output_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
