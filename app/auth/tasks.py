from celery import shared_task
from celery.contrib.abortable import AbortableTask
import time
from werkzeug.datastructures import FileStorage
import base64
from werkzeug.utils import secure_filename
import io
from flask import current_app
import os






@shared_task(bind=True,base=AbortableTask)
def add(self,x,y):
    time.sleep(10)
    return x+y

# @shared_task(bind=True,base=AbortableTask)
# def upload_task(self,filestream,directory):
#     file_url = upload_file_from_stream(filestream,directory)
#     return file_url