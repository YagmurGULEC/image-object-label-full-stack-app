from flask import Flask, render_template, request, redirect, url_for,session,g,flash
from app.auth.views import bp
from flask_wtf.csrf import CSRFProtect
import os
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer
from .utils_celery import make_celery


app = Flask(__name__,static_url_path='/static')
app.config['CELERY_CONFIG'] ={"broker_url": "redis://redis", "result_backend": "redis://redis"}
celery = make_celery(app)
celery.set_default()
app.register_blueprint(bp)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
mail_username=os.environ.get('MAIL_USERNAME')
mail_password=os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password
app.config['UPLOAD_FOLDER'] = './uploads'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.secret_key = os.urandom(12).hex()

mail = Mail(app)
csrf = CSRFProtect(app)
from . import utils
utils.init_command_line(app)

def send_mail(subject,sender,recipient,msg):
    message = Message(subject=subject, sender=sender, recipients=[recipient])
    message.body = msg
    mail.send(message)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            max_age=expiration
        )
    except:
        return False
    return email

@app.route('/')
def index():
    return render_template('index.html')




