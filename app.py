from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask.json.provider import JSONProvider
from bson import ObjectId
from flask_bcrypt import Bcrypt
import json
import jwt
import datetime
from pymongo import MongoClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
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

def get_rooms_set_confirmed(confirmed, rooms_id= None):
        pipeline = [
            # confirmed가 False인 도큐먼트만
            {
                "$match": {
                    "confirmed": confirmed,
                }
            },
            # join_user 콜렉션과 조인, 사용자 정보를 가져옴
            {
                "$lookup": {
                    "from": "join_user",
                    "localField": "_id",
                    "foreignField": "room_id",
                    "as": "users"
                }
            },
            # 하단 필드 선택
            {
                "$project": {
                    "title": 1,
                    "category": 1,
                    "max_count": 1,
                    "user_count": {"$size": "$users"}
                }
            }
        ]
        
        # id로 1개만 return
        if rooms_id is not None:
            pipeline[0]["$match"]["_id"] = ObjectId(rooms_id)
            result = list(db.rooms.aggregate(pipeline))
            return result[0] 
        # 리스트를 return
        else:
            return list(db.rooms.aggregate(pipeline))

@app.route("/")
def home():
    return render_template("login.html")

# 파티 찾기 (GET) - 유저 빼고 완성
@app.route("/rooms", methods=["GET"])
def get_rooms():
    not_confirmed = get_rooms_set_confirmed(False)
    return render_template("show_room_list.html", not_confirmed=not_confirmed)

# 신청한 파티 확인하기 (GET) - 유저 빼고 완성
@app.route("/users/rooms", methods=["GET"])
def get_user_rooms():
    confirmed = get_rooms_set_confirmed(True)
    not_confirmed = get_rooms_set_confirmed(False)
    return render_template("joined_room_list.html", confirmed=confirmed, not_confirmed=not_confirmed)

# 파티 세부정보 확인하기 (GET)
@app.route("/rooms/<rooms_id>", methods=["GET"])
def get_room_detail(rooms_id):
    room = get_rooms_set_confirmed(True, rooms_id=rooms_id)
    return render_template("room_details.html", room=room)

# 파티 만들기 화면 띄우기 (GET)
@app.route("/rooms/create", methods=["GET"])
def get_create():
    return render_template("create_room.html")

# 파티 수정하기 화면 띄우기 (GET)
@app.route("/rooms/<rooms_id>/modify", methods=["GET"])
def get_modify(rooms_id):
    categories = ["운동", "음식", "공동 구매", "외출", "기타"]
    room = db.rooms.find_one({"_id": ObjectId(rooms_id)})
    return render_template("modify_room.html", room=room, categories=categories)


# 파티 수정하기 (POST)
@app.route("/rooms/<rooms_id>/modify", methods=["POST"])
def post_modify(rooms_id):
    title = request.form.get("title")
    max_count = int(request.form.get("max_count"))
    category = request.form.get("category")
    
    db.rooms.update_one(
        {"_id": ObjectId(rooms_id)},
        {"$set": {
            "title": title,
            "max_count": max_count,
            "category": category
        }}
    )
    
    return redirect(url_for("get_user_rooms"))

# 파티 만들기 (POST) - 유저 빼고 완성
@app.route("/rooms/create", methods=["POST"])
def post_create():
    title = request.form.get("title")
    max_count = int(request.form.get("max_count"))
    category = request.form.get("category")
    
    # rooms 콜렉션에 도큐먼트 추가
    new_room = {
        'title': title,
        'category': category,
        'max_count': max_count,
        'host': 'temp',
        'confirmed': False
    }
    result = db.rooms.insert_one(new_room)
    
    # 중간 콜렉션에 도큐먼트 추가
    new_room_id = result.inserted_id
    new_join = {
        'user_id': 'temp',
        'room_id': ObjectId(new_room_id)
    }
    db.join_user.insert_one(new_join)
    return redirect(url_for('get_user_rooms'))

# 파티 삭제하기 (POST)
@app.route("/rooms/<rooms_id>/delete", methods=["POST"])
def post_delete(rooms_id):
    db.rooms.delete_one({"_id": ObjectId(rooms_id)})
    db.join_user.delete_many({"_id": ObjectId(rooms_id)})
    return redirect(url_for('get_user_rooms'))

# 파티 확정하기
@app.route("/rooms/<rooms_id>/confirm", methods=["POST"])
def post_confirm(rooms_id):
    db.rooms.update_one({"_id": ObjectId(rooms_id)}, 
                        {"$set": {'confirmed': True}})
    return redirect(url_for('get_user_rooms'))

    return render_template("logIn.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/testpage")
def testpage():
    return render_template("show_room_list.html")

@app.route("/users/register", methods=['POST'])
def register():
    name = request.json.get('name')
    email = request.json.get('email')
    phonenumber = request.json.get('phonenumber')
    password = request.json.get('password')
    confirm_password = request.json.get('confirm_password')
    
    if not name or len(name) < 2:
        return jsonify({'message': '이름은 두 글자 이상이어야 합니다.'}), 400

    if not email or '@' not in email or '.' not in email:
        return jsonify({'message': '올바른 이메일 형식이 아닙니다.'}), 400

    if len(phonenumber) not in [10, 11]:
        return jsonify({'message': '휴대폰 번호는 10자리 또는 11자리여야 합니다.'}), 400

    if not password or len(password) < 6:
        return jsonify({'message': '비밀번호는 6자 이상이어야 합니다.'}), 400

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
        'password' : hashed_password,
        'phonenumber' : phonenumber
    }
    users_collection.insert_one(new_user)

    return jsonify({'message' : '회원가입에 성공하셨습니다.'}), 201

@app.route("/users/login", methods=['POST'])
def login():
    # 로그인시 토큰 발급
    email = request.json.get('email')
    password = request.json.get('password')

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
    else:
        return jsonify({'message': '비밀번호가 잘못되었습니다.'}), 400

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)