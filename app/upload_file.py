import boto3
import os 
from botocore.exceptions import NoCredentialsError
from botocore.client import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from os  import listdir
import shutil
import aioboto3
import asyncio
from dotenv import load_dotenv
import time
from celery import shared_task
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import base64
import io
import os
from celery.contrib.abortable import AbortableTask

def process_file_to_stream(file: FileStorage, to_utf8: bool = False) -> dict:
    """
    Notice that since celery serializer (json) can't take bytes datatype,
    so, we need to convert it from base64 bytes to utf-8 format.
    But we don't need to do that when using threading
    """
    stream = base64.b64encode(file.stream.read())
    result = {
        "stream": stream if not to_utf8 else stream.decode("utf-8"),
        "name": file.name,
        "filename": secure_filename(file.filename),
        "content_type": file.content_type,
        "content_length": file.content_length,
        "headers": {header[0]: header[1] for header in file.headers},
    }

    return result

def upload_file_from_stream(data: dict,directory) -> str:
    """
    Upload file to S3 by first converting back from base64 encoded bytes/utf-8 to file
    """
    data["stream"] = base64.b64decode(data["stream"])
    data["stream"] = io.BytesIO(data["stream"])
    file = FileStorage(**data)
    file.save(os.path.join(directory, data["filename"]))
    return f"{os.path.join(directory, data["filename"])}"

@shared_task(bind=True,base=AbortableTask)
def upload_task(self,filestream,directory):
    file_url = upload_file_from_stream(filestream,directory)
    return file_url

# Load environment variables from .env file
load_dotenv()
s3client=boto3.client('s3',config=Config(signature_version='s3v4'),aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                      aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                      region_name='us-east-2'  )

def generate_presigned_url(bucket_name, s3_key, expiration=3600):
   
    try:
        response = s3client.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket_name, 'Key': s3_key},
                                             ExpiresIn=expiration)
        return response
    except NoCredentialsError:
        print("Credentials not available")
        return None


def upload_file_sync(file_path,s3_key,bucket_name=os.environ['AWS_BUCKET_NAME']):
    try:
        s3client.upload_file(file_path, bucket_name, s3_key)
        print(f"Uploaded {file_path} to {bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload {file_path}: {e}")

def list_files(path):
  response = s3client.list_objects_v2(Bucket=os.environ['AWS_BUCKET_NAME'], Prefix=path)
  if 'Contents' in response:
    return response['Contents']
  else:
     return None

# Function to upload a single file asynchronously
async def upload_file(s3_client, file_path, bucket_name, s3_key):
    try:
        await s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f"Uploaded {file_path} to {bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload {file_path}: {e}")


def create_copies(file_path, num_copies, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    
    for i in range(num_copies):
        new_file_path = os.path.join(dest_dir, f"{name}_copy{i+1}{ext}")
        shutil.copyfile(file_path, new_file_path)
        print(f"Created copy: {new_file_path}")

# Function to handle uploading multiple files using asyncio
async def upload_files_parallel(file_paths, directory='temp_async',max_workers=10,bucket_name=os.environ['AWS_BUCKET_NAME']):
    semaphore = asyncio.Semaphore(max_workers)
    
    async with aioboto3.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ['AWS_BUCKET_REGION']
        ).client('s3') as s3_client:
        tasks = []
        for file_path in file_paths:
            s3_key ='temp_'+str(max_workers)+'/'+os.path.basename(file_path)
            task = upload_file_with_semaphore(semaphore, s3_client, file_path, bucket_name, s3_key)
            tasks.append(task)
        await asyncio.gather(*tasks)

# Helper function to use semaphore for limiting the number of concurrent uploads
async def upload_file_with_semaphore(semaphore, s3_client, file_path, bucket_name, s3_key):
    async with semaphore:
        await upload_file(s3_client, file_path, bucket_name, s3_key)

if __name__=="__main__":
    directory = "temp"
    files_to_upload = [os.path.join(directory,f) for f in listdir(directory)]
    start_time = time.time()
    for f in files_to_upload:
        upload_file_sync(f,'temp_syncronous/'+os.path.basename(f))
      
    end_time = time.time()
    print(f"Time taken to upload files syncronously: {end_time - start_time:.2f} seconds")
    # start_time = time.time()
    # asyncio.run(upload_files_parallel(files_to_upload,10))
    # end_time = time.time()
    # print(f"Time taken to upload files asyncronously: {end_time - start_time:.2f} seconds")
    
    