from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()

def init_mongo(app: Flask):
    app.config["MONGO_URI"] = "mongodb+srv://Anh:Anh2142003@cluster0.iyqpdy4.mongodb.net/OCR?retryWrites=true&w=majority"

    mongo.init_app(app)
