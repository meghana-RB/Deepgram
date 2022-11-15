from flask import Flask, request, jsonify, make_response
import wave
import contextlib
import json
import speech_recognition as sr
from os import path
import os
import utils as ut
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
import user_auth
from functools import wraps
import uuid # for public id
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import config
# TO DO:
# 1. User Auth
# 2. Store Dates
# 3. Different language transcription
#json db server - use it as a database
#json line format -
# 
# 

pwd = os.getcwd()
upload_folder = os.path.join(pwd, 'Audio Database')
if not os.path.exists(upload_folder):
   os.makedirs(upload_folder)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder

app.config['SECRET_KEY'] = config.config['secret_key']
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# creates SQLALCHEMY object
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS']
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	public_id = db.Column(db.String(50), unique = True)
	name = db.Column(db.String(100))
	email = db.Column(db.String(70))
	password = db.Column(db.String(80))



def create_dummy_db(db):
    db.create_all()

    user1 = User(
        public_id = str(uuid.uuid4()),
        name = 'Meghana',
        email = 'meghanab@umich.edu',
        password = generate_password_hash('somestring1234')
    )

    db.session.add(user1)
    db.session.commit()

    user2 = User(
        public_id = str(uuid.uuid4()),
        name = 'cliff',
        email = 'cliff@deepgram.com',
        password = generate_password_hash('somestring1234')
    )

    db.session.add(user2)
    db.session.commit()

    user3 = User(
        public_id = str(uuid.uuid4()),
        name = 'preston',
        email = 'preston@deepgram.com',
        password = generate_password_hash('somestring1234')
    )

    db.session.add(user3)
    db.session.commit()
    return db

db = create_dummy_db(db)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'wav'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
		# jwt is passed in the request header
        print("request.headers: ", request.headers)
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            print(data)
            current_user = User.query\
				.filter_by(public_id = data['public_id'])\
				.first()
        except:
            return jsonify({
				'message' : 'Token is invalid !!'
			}), 401
        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/login', methods =['POST'])
def login():
    # print(request)
    auth = request.args
    # print((auth))
    if not auth or not auth.get('email') or not auth.get('password'):
        print(auth.file)
        print("first if")
        return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
		)
    user = User.query\
		.filter_by(email = auth.get('email'))\
		.first()
    if not user:
        print("second if")
        return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
		)
    
    if check_password_hash(user.password, auth.get('password')):
        token = jwt.encode({
			'public_id': user.public_id,
			'exp' : datetime.utcnow() + timedelta(minutes = 60)
		}, app.config['SECRET_KEY'])
        return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
	
    return make_response(
		'Could not verify',
		403,
		{'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
	)


@app.route('/home', methods=['GET', 'POST'])
@token_required
def welcome(current_user):
    if 'file' not in request.files:
        print('No file part')
        return "Welcome to Deep Gram"

    file = request.files.get('file', None)
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ut.convert_wav_to_jsons(os.path.join(upload_folder, filename))
        return "Welcome to Deep Gram. We recieved your Audio File {0}".format(file.filename)
 
@app.route('/list', methods=['GET'])
@token_required
def lists(current_user)->json:
    filters = []
    args = (request.args).to_dict()
    audio_repo = os.path.join(pwd, 'audio_data_repo.json')
    if os.path.isfile(audio_repo):
        with open(audio_repo,'r+') as outfile:
            aud = json.load(outfile)
    df = pd.DataFrame(aud)
    if not set(args.keys()).issubset(set(df.columns)):
        return "Invalid Query"
    filtered_df = df
    for arg in list(args.keys()):
        print(args[arg], arg)
        filtered_df = df[df[arg]==float(args[arg])]
    json_df = filtered_df.to_json()
    return jsonify(json_df)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105)