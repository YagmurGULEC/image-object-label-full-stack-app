from celery import Celery
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import base64
import io
import os

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


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