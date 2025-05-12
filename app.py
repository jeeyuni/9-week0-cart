from flask import Flask, render_template, request, jsonify
from flask.json.provider import JSONProvider
from bson import ObjectId
import json
import sys
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client.jungle

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
    return render_template("index.html")
    
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)