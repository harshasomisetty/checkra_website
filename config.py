import urllib.parse
from dotenv import load_dotenv
import os

load_dotenv()

class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
    MONGO_URI = "mongodb+srv://"+os.getenv("USERNAME")+":"+urllib.parse.quote(str(os.getenv("PASSWORD")))+"@cluster0.4pec2.mongodb.net/development?retryWrites=true&w=majority"

