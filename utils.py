import os, time,json

from pymongo import MongoClient
from termcolor import cprint, colored

from pyproj import Proj
from shapely.geometry import shape, Point
import requests
requests.adapters.DEFAULT_RETRIES=3

mongodb_user=os.environ.get('MONGO_USER')
mongodb_pass=os.environ.get('MONGO_PASS')
mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
db = mongo_client.get_database()

def send_groupme(bot_id,pokemon):
	content = pokemon.format_for_groupme()
	loc =  [{
	    "type": "location",
	    "lat": f"{pokemon.lat}",
	    "lng": f"{pokemon.lng}",
	    "name": f"{pokemon.hood}"
	  }]
	payload={"bot_id":bot_id, "text":content, "attachments": loc}
	r = requests.post("https://api.groupme.com/v3/bots/post", json=payload)
	if not r.ok:
		print(f"ERROR: posting to groupme for {bot_id} {pokemon},{r.status_code}")
	return r.ok

def get_minIV_for(bot_id,pokemon_name,pokemon_lvl):
	# mongodb_user=os.environ.get('MONGO_USER')
	# mongodb_pass=os.environ.get('MONGO_PASS')
	# with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
	col = db.get_collection('iSawIt_{}'.format(bot_id))
	match=list(col.aggregate([
		{ "$match" :{"name":pokemon_name}},
		{"$unwind": "$min_lvl_iv"} ,
		{"$match":{"min_lvl_iv.lvl":{"$lte":pokemon_lvl}}},
		{"$sort":{"min_lvl_iv.lvl":-1}},
		{"$limit":1}]))
	iv=100
	if match and len(match)>0:
		m=match[0]
		if "min_lvl_iv" in m.keys():
			m=m['min_lvl_iv']
			if 'iv' in m.keys():
				# iv should be between 0 and 100
				iv=max(0,min(100,int(m['iv'])))
	return iv

def get_hoods_to_listen_for():
	# mongodb_user=os.environ.get('MONGO_USER')
	# mongodb_pass=os.environ.get('MONGO_PASS')
	hoods=[]
	# with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
		# db = mongo_client.get_database()
	hoods = [x.get('_id') for x in db.iControlIt.aggregate([    {"$unwind" : "$hoods"},{"$group" : {"_id" : "$hoods"}}])]
	return hoods

def process_message_for_groupme(data):
	# mongodb_user=os.environ.get('MONGO_USER')
	# mongodb_pass=os.environ.get('MONGO_PASS')
	# with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
	# 	db = mongo_client.get_database()

	for doc in db.iControlIt.find({"iSawIt_id":{"$exists":True}},{"iSawIt_id":True,"_id":False}):
		# print("process_message_for_groupme {}".format(doc['iSawIt_id']))
		# print(doc['iSawIt_id'], data.name, data.level)
		prefix="FAIL"
		# if True or data.hood in doc['hoods']:
		min_iv = get_minIV_for(doc['iSawIt_id'], data.name, data.level)
		# print(min_iv)
		if type(min_iv) is int and \
			(min_iv == 0 or (data.iv >= min_iv)):
			prefix="PASS"

			bot_id=doc['iSawIt_id']
			# send_groupme(bot_id,data)
	print(data)
	# bot_id = "1413a583e8a010356a96336656"
	# send_groupme(bot_id,data)

nys = Proj(init='EPSG:32118')
def distance_between(p1,p2):
	p1_proj = nys(p1.x, p1.y)
	p2_proj = nys(p2.y, p2.x)
	d = Point(p1_proj).distance(Point(p2_proj))
	d = float(int(d * 100) / 100)
	return d

manhattan_shape=None
def get_manhattan():
	global manhattan_shape
	if manhattan_shape != None: return manhattan_shape
	with open("json/boros.json",encoding="utf-8") as file:
		m=json.load(file)
		manhattan_shape=shape(m['geometry'])
	return manhattan_shape

def point_is_in_manhattan(point,refPoint=Point(40.84635921,-73.94062042)):
	s=get_manhattan()
	d=None
	is_in_shape=s.contains(point)
	if is_in_shape:
		d=distance_between(point,refPoint)
	return is_in_shape, d
