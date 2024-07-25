## Full-stack Flask application to label objects from images to create datasets



#### Technologies used

#### Backend: 
- Flask for web development
- Amazon DynamoDB for storing users' email addresses, passwords and images uploaded with bounding boxes of each labels 
- Amazon S3 bucket for storing images uploaded by users
- Celery for uploading images asynchronously
- Redis as Celery backend
- Docker to start each services easily

#### Frontend:
- JavaScript for drawing boxes on a canvas 

