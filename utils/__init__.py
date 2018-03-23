import logging, os, pymongo

mongodb_user=os.environ.get('MONGO_USER')
mongodb_pass=os.environ.get('MONGO_PASS')
mongo_client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
db = mongo_client.nyc

logger=logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

