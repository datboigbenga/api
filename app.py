from encodings import utf_8
import json
from turtle import update
import uuid
import jwt
# import tkinter as TK
# import _tkinter
import pymongo
from flask import Flask, request, jsonify, Response
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps
from bson.objectid import ObjectId


app = Flask(__name__)
app.config['SECRET_KEY'] = "gbenga"
try:
    # myclient = pymongo.MongoClient(
    #     host="mongodb+srv://gbenga1998:gbenga@cluster0.bdkpoct.mongodb.net/?retryWrites=true&w=majority",
    #     # host="localhost", 
    #     # port=27017, 
    #     serverSelectionTimeoutMS= 1000)

    myclient = pymongo.MongoClient("mongodb+srv://gbenga:gbenga@cluster0.bdkpoct.mongodb.net/?retryWrites=true&w=majority",serverSelectionTimeoutMS= 3000)
    db = myclient.test
    # db = myclient
    print(myclient.list_database_names())
    myclient.server_info()
    
    # mydb = myclient.flask_db
    # todos = mydb.todos
    # print(myclient.list_database_names())
except Exception as Ex:
    print(Ex)
    print("Error detected, Server cannot connect to db")

def token_required(f):
    @wraps(f)
    def decorate(*args, **kwargs):
        token = None
        if 'x-access-token'in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message':'token  required'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.users.find({'public_id': data['public_id']})

        except Exception as Ex:
            print(Ex)
            return jsonify({'message':'token is invalid'})

        return f(current_user, *args, **kwargs)

    return decorate
    
@app.route('/register', methods=['POST'])
def register_user():
    try:
        user = request.get_json()
        hash_pass = generate_password_hash(user["password"], method="sha256")
        pub_id = str(uuid.uuid1())
        user_input= {
                "public_id":pub_id,
                "first_name" : user["first_name"],
                "last_name" : user["last_name"],
                "email" : user["email"],
                "password" : hash_pass
              }
        dbResponse = db.users.insert_one(user_input)
        # for data in dir(dbResponse):
        # print(data)
        #     jsonify({"data"})
        # print(dbResponse)
        # return jsonify({"message":"user created"})
        return Response(
            response=json.dumps({"message":"user created"}),
            status= 200,
            mimetype= "application/json"
        )
        
    except Exception as Ex:
        print("error")
        print(Ex)
    # return "he"

@app.route('/login', methods=['POST'])
def login_user():
    try:
        auth = request.authorization
        print(auth)
        if not auth or not auth.username or not auth.password:
            return Response("could not verify", 401, {'www-authenticate': 'Basic-realm="login required"'})
        query1 = {"email":auth.username}
        user = db.users.find(query1)
        # if not user:
        #     return jsonify({"message":"error"})
            # Response("could not verify", 401, {'www-authenticate': 'Basic-realm="login required"'})
        for user_det in user:
                # print(pl)
            print(user_det)
            if not user_det:
                return Response("could not verify", 401, {'www-authenticate': 'Basic-realm="login required"'})
            if check_password_hash(user_det['password'], auth.password):
                token = jwt.encode({'public_id':user_det['public_id'],  'exp':datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                # token_d = token.decode("UTF-8")
                return jsonify({'token': token})

            return Response("could not verify", 401, {'www-authenticate': 'Basic-realm="login required"'})

    except Exception as ex:
        print(ex)
        print("unable to login")
        return Response("could not verify", 401, {'www-authenticate': 'Basic-realm="login required"'})

    # return ""

@app.route('/template', methods=['POST'])
@token_required
def temp(current_user):
    try:
        template = request.get_json()
        dbResponse = db.templates.insert_one(template)
        return jsonify({'message':'template added'})

    except Exception as Ex:
        print(Ex)
        return jsonify({'message':'template not added'})


@app.route('/template', methods=['GET'])
@token_required
def temp_get_all(current_user):
    # print("Gbemga")
    try:
        # template = request.get_json()
        dbResponse = db.templates.find()
        temps = list(dbResponse)
        for temp in temps:
            temp['_id'] = str(temp['_id'])
            print(temp)
        return json.dumps({'templates':temps})

    except Exception as Ex:
        print(Ex)
        return jsonify({'message':'templates not retrieved'})
    # return ""


@app.route('/template/<template_id>', methods=['GET'])
@token_required
def temp_get_one_temp(current_user, template_id):
# def temp_get_one_temp(template_id):

    try:
        query = {"_id":ObjectId(template_id)}
        dbResponse = db.templates.find(query)
        temps = list(dbResponse)
        print(temps)
        for temp in temps:
            temp['_id'] = str(temp['_id'])
        # return json.dumps({'template':temps})
        return jsonify({'template':temps})
            
    except Exception as Ex:
        print(Ex)
        return jsonify({'message':'template not retrieved'})
   


@app.route('/template/<template_id>', methods=['PUT'])
@token_required
def temp_update(current_user, template_id):
    try:
        updater = request.get_json()
        query = {"_id":ObjectId(template_id)}
        # Update_query = {"$set": {"template_name":request.form['template_name'], "subject":request.form['subject'], "body":request.form['body']}}
        print(updater)
        Update_query = {"$set": updater}
        dbResponse = db.templates.update_one(query, Update_query)
        # dbResponse = db.templates.find_one_and_update(query, Update_query)


        if dbResponse.modified_count == 1:
            return jsonify({"message":"template updated"})
        
        return jsonify({"message":"nothing to update"})
    except Exception as Ex:
        print(Ex)
        print("unable to update")
        return jsonify({"message":"unable to update"})


    # return template_id

@app.route('/template/<template_id>', methods=['DELETE'])
@token_required
def temp_del(current_user, template_id):
    try:
        query = {"_id":ObjectId(template_id)}
        dbResponse = db.templates.delete_one(query)
        if dbResponse.deleted_count == 1:
            return jsonify({"message":"template deleted", "id":template_id})
        
        return jsonify({"message":"nothing to delete"})

    except Exception as Ex:
        print(Ex)
        print("unable to delete")
        return jsonify({"message":"unable to delete"})

    return ""

if __name__ == '__main__':
    app.run(debug= True)
    # app.run(port=8000, debug=True)
