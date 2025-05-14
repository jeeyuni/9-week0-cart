from flask import Flask, render_template, request, jsonify, redirect, url_for, g, abort
from flask.json.provider import JSONProvider
from bson import ObjectId
from flask_bcrypt import Bcrypt
import datetime
import json
import jwt
from pymongo import MongoClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://test:test@localhost',27017)
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

def format_time(dt_str):
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
    formatted = dt.strftime(f"%Y.%m.%d({weekday_kor[dt.weekday()]}) %H:%M")
    return formatted

def format_phoneno(phoneno_str):
    formatted = f"{phoneno_str[:3]}-{phoneno_str[3:7]}-{phoneno_str[7:]}"
    return formatted

def get_rooms_set_confirmed(confirmed, rooms_id= None, user_check=False, time="future", time_sort=1):
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    print(now)
    if time == "past":
        time_expr = {"$lte": ["$time", now]}
    elif time == "future":
        time_expr = {"$gt": ["$time", now]}
    elif time == "both":
        time_expr = None
        
    pipeline = [
        # confirmed의 True/False 여부 설정
        {
            "$match": {
                "confirmed": confirmed,
                **({"$expr": time_expr} if time_expr else {})
            }
        },
        # join_user 콜렉션과 조인, 사용자 정보를 가져옴
        {
            "$lookup": {
                "from": "join_user",
                "localField": "_id",
                "foreignField": "room_id",
                "as": "users_list"
            }
        },
        {
            "$match": {
                "users_list.user_id": ObjectId(g.user["_id"]) if user_check else {"$exists": True}
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "host",
                "foreignField": "_id",
                "as": "host_id"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "users_list.user_id",
                "foreignField": "_id",
                "as": "user_details"
            }
        },
        # 하단 필드 선택
        {
            "$project": {
                "title": 1,
                "category": 1,
                "user_count": 1,
                "max_count": 1,
                "location": 1,
                "time": 1,
                "host_id": {
                    "$arrayElemAt": ["$host_id._id", 0]
                },
                "user_details": 1,
                "host_name": {
                    "$arrayElemAt": ["$host_id.name", 0]
                },
                "user_in_room": {
                "$cond": {
                    "if": {
                        "$in": [ObjectId(g.user["_id"]), "$users_list.user_id"]
                    },
                    "then": True,
                    "else": False
                }
            }
            }
        },
        {
        "$sort": { "time": time_sort }
    }
    ]
    
    # id로 1개만 return
    if rooms_id is not None:
        pipeline[0]["$match"]["_id"] = ObjectId(rooms_id)
        result = list(db.rooms.aggregate(pipeline))
        return result[0] 
    # 리스트를 return
    else:
        result = list(db.rooms.aggregate(pipeline))
        return result
        
# 쿠키 확인해 JWT토큰 확인
@app.before_request
def check_jwt():
    if request.path.startswith('/static'):
        return
    
    public_paths = ['/users/login', '/users/register', '/signup']
    
    for p in public_paths:
        if request.path == p:
            return  # 로그인 안 해도 접근 허용
    
    # 쿠키에서 JWT 토큰 가져오기
    token = request.cookies.get('token')
    
    if token:
        try:
            # JWT 토큰을 디코딩하고 유효성을 검사
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # 유효한 토큰이면 request.user에 저장 (사용자 정보로 활용 가능)
            user = db.users.find_one({'_id': ObjectId(payload["_id"])})
            g.user = user
        except jwt.ExpiredSignatureError:
            g.user = None
        except jwt.InvalidTokenError:
            g.user = None

    else:
        g.user = None
        
    if g.user is None:
        return redirect(url_for('get_login'))


# 미로그인시 로그인 화면, 로그인시 파티 찾기 화면
@app.route("/")
def home():
    if g.user:
        return redirect(url_for('get_rooms'))
    else:
        return redirect(url_for('get_login'))

@app.route("/users/login")
def get_login():
    return render_template("logIn.html")

# 파티 찾기 (GET)
@app.route("/rooms", methods=["GET"])
def get_rooms():
    not_confirmed = get_rooms_set_confirmed(False)
    return render_template("show_room_list.html", not_confirmed=not_confirmed, user=g.user, format_time=format_time)

# 신청한 파티 확인하기 (GET)
@app.route("/users/rooms", methods=["GET"])
def get_user_rooms():
    confirmed = get_rooms_set_confirmed(True, user_check=True)
    not_confirmed = get_rooms_set_confirmed(False, user_check=True)
    past = get_rooms_set_confirmed(True, user_check=True, time="past", time_sort=-1)
    return render_template("joined_room_list.html", confirmed=confirmed, not_confirmed=not_confirmed, past=past, user=g.user, format_time=format_time)

# 파티 참여 (POST)
@app.route("/rooms/join", methods=["POST"])
def join():
    user_id = ObjectId(g.user["_id"])
    room_id = ObjectId(request.form.get("room_id"))
    result = db.join_user.find_one({"user_id": user_id, "room_id": room_id})
    
    if result is not None:
        return jsonify({'result': 'failure', 'message': '이미 참여한 파티입니다.'})
    
    room = db.rooms.find_one({"_id": room_id})
    
    if room["confirmed"]:
        return jsonify({"result": "failure", "message": "확정된 파티엔 추가로 참여할 수 없습니다."})
    

    
    room = db.rooms.find_one_and_update({
        "_id": room_id,
        "$expr": {"$lt": ["$user_count", "$max_count"]}
    },
    {
        "$inc": {"user_count": 1}
    })
    
    print(room)
    
    if room is None:
        return jsonify({'result': 'failure', 'message': '정원이 초과되었습니다.'})
    
    db.join_user.insert_one({"user_id": user_id, "room_id": room_id})
    return jsonify({'result': 'success', 'message': '신청되었습니다.'})
        
# 파티 퇴장 (POST)
@app.route("/rooms/exit", methods=["POST"])
def exit():
    user_id = ObjectId(g.user["_id"])
    room_id = ObjectId(request.form.get("room_id"))
    db.join_user.delete_one({"user_id": user_id, "room_id": room_id})
    db.rooms.update_one({"_id": room_id}, {"$inc": {"user_count": -1}})
    return jsonify({"result": "success", "message": "퇴장하셨습니다."})

# 파티 세부정보 확인하기 (GET)
@app.route("/rooms/<rooms_id>", methods=["GET"])
def get_room_detail(rooms_id):
    
    room = get_rooms_set_confirmed(True, rooms_id=rooms_id, time="both")
    return render_template("room_details.html", room=room, user=g.user, format_time=format_time, format_phoneno=format_phoneno)

# 파티 만들기 화면 띄우기 (GET)
@app.route("/rooms/create", methods=["GET"])
def get_create():
    return render_template("create_room.html", user=g.user)

# 파티 수정하기 화면 띄우기 (GET)
@app.route("/rooms/<rooms_id>/modify", methods=["GET"])
def get_modify(rooms_id):
    room = db.rooms.find_one({"_id": ObjectId(rooms_id)})
    if g.user is None or g.user["_id"] != room["host"]:
        return render_template("error.html")
    
    categories = ["운동", "음식", "공동 구매", "외출", "기타"]
    room = db.rooms.find_one({"_id": ObjectId(rooms_id)})
    return render_template("modify_room.html", room=room, categories=categories, user=g.user)


# 파티 수정하기 (POST)
@app.route("/rooms/<rooms_id>/modify", methods=["POST"])
def post_modify(rooms_id):
    room = db.rooms.find_one({"_id": ObjectId(rooms_id)})
    if g.user is None or g.user["_id"] != room["host"]:
        return render_template("error.html")
    title = request.form.get("title")
    max_count = int(request.form.get("max_count"))
    category = request.form.get("category")
    time = request.form.get("time")
    location = request.form.get("location")
    
    db.rooms.update_one(
        {"_id": ObjectId(rooms_id)},
        {"$set": {
            "title": title,
            "max_count": max_count,
            "category": category,
            "time": time,
            "location": location
        }}
    )
    
    return redirect(url_for("get_user_rooms"))

# 파티 만들기 (POST) - 유저 빼고 완성
@app.route("/rooms/create", methods=["POST"])
def post_create():
    title = request.form.get("title")
    max_count = int(request.form.get("max_count"))
    category = request.form.get("category")
    time = request.form.get("time")
    location = request.form.get("location")
    
    # rooms 콜렉션에 도큐먼트 추가
    new_room = {
        'title': title,
        'category': category,
        'user_count': 1,
        'max_count': max_count,
        'host': ObjectId(g.user["_id"]),
        'time': time,
        'location': location,
        'confirmed': False
    }
    result = db.rooms.insert_one(new_room)
    
    # 중간 콜렉션에 도큐먼트 추가
    new_room_id = result.inserted_id
    new_join = {
        'user_id': ObjectId(g.user["_id"]),
        'room_id': ObjectId(new_room_id)
    }
    db.join_user.insert_one(new_join)
    return redirect(url_for('get_user_rooms'))

# 파티 삭제하기 (POST)
@app.route("/rooms/<rooms_id>/delete", methods=["POST"])
def post_delete(rooms_id):
    db.rooms.delete_one({"_id": ObjectId(rooms_id)})
    db.join_user.delete_many({"room_id": ObjectId(rooms_id)})
    return redirect(url_for('get_user_rooms'))

# 파티 확정하기
@app.route("/rooms/<rooms_id>/confirm", methods=["POST"])
def post_confirm(rooms_id):
    db.rooms.update_one({"_id": ObjectId(rooms_id)}, 
                        {"$set": {'confirmed': True}})
    return redirect(url_for('get_user_rooms'))

# 회원가입 화면 (GET)
@app.route("/signup")
def signup():
    return render_template("signup.html")

# 로그인 성공 (GET)
@app.route("/testpage")
def testpage():
    return redirect(url_for("get_rooms"))

# 회원가입 (POST)
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

# 로그인 (POST)
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
            '_id': str(user["_id"]),
            'email': email,
            # 토큰 유효 시간 = 현재시간을 가지고 옴 + 1시간 
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'message': '로그인 성공', 'token': token}), 200
    else:
        return jsonify({'message': '비밀번호가 잘못되었습니다.'}), 400
    
# 로그아웃 (POST)
@app.route("/users/logout", methods=["POST"])
def logout():
    return jsonify({"message": "로그아웃 성공"})
            
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)