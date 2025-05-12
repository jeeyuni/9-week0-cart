from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask.json.provider import JSONProvider
from bson import ObjectId
import json
import sys
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client.dbroom

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
    return redirect(url_for('get_rooms'))

# 파티 찾기 (GET) - 유저 빼고 완성
@app.route("/rooms", methods=["GET"])
def get_rooms():
    
    pipeline = [
        # confirmed가 False인 도큐먼트만
        {
            "$match": {
                "confirmed": False
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
    
    rooms = list(db.rooms.aggregate(pipeline))
    return render_template("room_list.html", rooms=rooms)

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
    max_count = request.form.get("max_count")
    category = request.form.get("category")
    
    db.rooms.update_one(
        {"_id": ObjectId(rooms_id)},
        {"$set": {
            "title": title,
            "max_count": max_count,
            "category": category
        }}
    )
    
    return redirect(url_for("get_rooms"))

# 파티 만들기 (POST) - 유저 빼고 완성
@app.route("/rooms/create", methods=["POST"])
def post_create():
    title = request.form.get("title")
    max_count = request.form.get("max_count")
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
    return redirect(url_for('get_rooms'))

# 파티 삭제하기 (POST)
@app.route("/rooms/<rooms_id>/delete", methods=["POST"])
def post_delete(rooms_id):
    db.rooms.delete_one({"_id": ObjectId(rooms_id)})
    db.join_user.delete_many({"_id": ObjectId(rooms_id)})
    return redirect(url_for('get_rooms'))

if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)