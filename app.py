from flask import Flask, render_template, request, jsonify
from flask.json.provider import JSONProvider
from bson import ObjectId
from flask_bcrypt import Bcrypt
import json
import jwt
import datetime
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client.dbroom
users_collection = db.users
bcrypt = Bcrypt(app)

# ObjectID 타입 처리 -> string으로 변환
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

app.json = CustomJSONProvider(app)

@app.route("/")
def home():
    return render_template("logIn.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/users/register", methods=['POST'])
def register():
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
    confirm_password = request.json.get('confirm_password')
    
    if password != confirm_password:
        return jsonify({'message': '비밀번호가 일치하지 않습니다.'}), 400

    # 입력한 비밀번호를 해쉬로 저장 decode 바이트 데이터를 문자열로 변환
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    exiting_user = users_collection.find_one({'email' : email})
    if exiting_user:
        return jsonify({'message' : '이메일이 존재합니다.'}), 400

    new_user = {
        'name' : name,
        'email' : email,
        'password' : password
    }
    users_collection.insert_one(new_user)

    return jsonify({'message' : '회원가입에 성공하셨습니다.'}), 201

@app.route("/users/login", methods=['POST'])
def login():
    email = request.json.get['email']
    password = request.json.get['password']

    user = users_collection.find_one({'email': email})
    if not user:
        return jsonify({'message': '사용자를 찾을 수 없습니다.'}), 404
    
    if bcrypt.check_password_hash(user['password'], password):
        # JWT 토큰 발급
        token = jwt.encode({
            'email': email,
            # 토큰 유효 시간 = 현재시간을 가지고 옴 + 1시간 
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'message': '로그인 성공', 'token': token}), 200
    
    return jsonify({'messsage': '비밀번호가 잘못되었습니다.'}), 400

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)