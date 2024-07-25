
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.database_dynamo import add_user,get_user,update_email_confirmation
from app.utils import login_required
from werkzeug.utils import secure_filename
import os
from app.upload_file import upload_files_parallel
import asyncio
from .tasks import add
bp=Blueprint('auth',__name__,url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
    user_mail= session.get('user_mail')

    if user_mail is None:
        g.user = None
    else:
        g.user=get_user(user_mail)
        


@bp.route('/register',methods=('GET','POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        isExistNonVerified=get_user(email)
        from app import send_mail,generate_confirmation_token
        if isExistNonVerified is None:
            if password==confirm_password:
                add_user(email,generate_password_hash(password))
                token = generate_confirmation_token(email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                message = 'Your confirmation link is {}. Please click on the link'.format(confirm_url)
                _=send_mail('Confirm Email',current_app.config['MAIL_USERNAME'],email,message)
                flash('User {} is successfully registered. Please confirm your email'.format(email))
            else:
                flash('Passwords do not match.')
            
        else:
            if (isExistNonVerified['email_confirmed']==False) and (check_password_hash(isExistNonVerified['password'],password)) and password==confirm_password:
                token = generate_confirmation_token(email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                message = 'Your confirmation link is {}. Please click on the link'.format(confirm_url)
                _=send_mail('Confirm Email',current_app.config['MAIL_USERNAME'],email,message)
                flash('The confirmation link for email is sent again to your email'.format(email))
            else:
                flash('User {} already exists'.format(email))
    return render_template('auth/register.html')

@bp.route('/login',methods=('GET','POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user=get_user(email)
        if user is None:
            flash('Incorrect email.')
        elif not check_password_hash(user['password'],password):
            flash('Incorrect password.')
        elif user['email_confirmed']==False:
            flash('Please confirm your email')
        else:
            session.clear()
            session['user_mail']=email
            return redirect(url_for('index'))
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/confirm_email/<token>')
def confirm_email(token):
    
    from app import confirm_token
    email_decoded=confirm_token(token)

    if email_decoded is not False:
        user_mail=get_user(email_decoded)
    
        if user_mail is not None:
            update_email_confirmation(email_decoded)
            flash('You have confirmed your email. Thanks!')
        return redirect(url_for('auth.login'))
    else:
        flash('The confirmation link is invalid or has expired. You need to register again')
        return redirect(url_for('auth.register'))

@bp.route('/upload',methods=['POST','GET'])
@login_required
def upload():
    bucket_name = os.environ['AWS_BUCKET_NAME']
    if request.method == 'POST':
        files = request.files.getlist('upload-file')
        
        secure_filenames=[]
        path = g.user['email'] + '/'
        for f in files:
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'],filename))
            secure_filenames.append(os.path.join(current_app.config['UPLOAD_FOLDER'],filename))
        asyncio.run(upload_files_parallel(secure_filenames,path))
        flash('Files are being uploaded')
        return render_template('/auth/upload.html')
    # response=upload_file.list_files(g.user['email'] + '/')
    # if response is not None:
        
    #     for file in response:
    #         file['url'] = upload_file.generate_presigned_url(bucket_name, file['Key'])
    #     print (response)
    #     return render_template('/auth/upload.html',files=response)
    flash('No files uploaded yet')
    return render_template('/auth/upload.html')
    
@bp.route('/add/<int:x>/<int:y>')
def add_link(x,y):
    task=add.delay(x,y)
    return redirect(url_for('auth.status',task_id=task.id))

@bp.route('/status/<task_id>')
def status(task_id):
    task=add.AsyncResult(task_id)
    return task.state
    