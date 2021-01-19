import urllib.parse

class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
    MONGO_URI = "mongodb+srv://***REMOVED***:"+urllib.parse.quote("***REMOVED***")+"@cluster0.4pec2.mongodb.net/production?retryWrites=true&w=majority"
    DEBUG = True # Turns on debugging features in Flask

class DevelopmentConfig(Config):
    FLASK_ENV="development"
    DEBUG = True # Turns on debugging features in Flask
    MONGO_URI = "mongodb+srv://***REMOVED***:"+urllib.parse.quote("***REMOVED***")+"@cluster0.4pec2.mongodb.net/development?retryWrites=true&w=majority"
