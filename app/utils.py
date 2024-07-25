from . import database_dynamo
import click
from flask.cli import with_appcontext
import os 
from flask_mail import Message
from .database_dynamo import create_table,table_schema,append_image
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import functools
from flask import g,redirect,url_for

def init_command_line(app):
    app.cli.add_command(create_dynamodb)
    app.cli.add_command(add_table_dynamo)
    app.cli.add_command(update_table_dynamo)

@click.command('create-db')
@with_appcontext
def create_dynamodb():
    create_table(**table_schema)
 

@click.command('add-db')
@click.argument('email')
@click.argument('password')
@with_appcontext
def add_table_dynamo(email,password):
    item={'email':email,'password':password,'is_verified':False,'created_at':str(datetime.now())}
    database_dynamo.add_user(**item)
 

@click.command('update-db')
@with_appcontext
def update_table_dynamo():
    mail="g@g.com"
    
    box_coordinates_list = [
    {'x1': 10, 'y1': 20, 'x2': 30, 'y2': 40,'label':'dog'},
   
    ]
    new_image_data = {
        'url': 'example-image-id-2',
        'box_coordinates': box_coordinates_list
    }
    res=append_image(mail,new_image_data)
    print (res)
    if res:
        click.echo('Successfully updated')
    else:
        click.echo('Update failed')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

    