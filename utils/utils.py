import os, time,json

from pymongo import MongoClient
from termcolor import cprint, colored
from collections import Counter, defaultdict
from pyproj import Proj
from shapely.geometry import shape, Point
import requests


mongodb_user=os.environ.get('MONGO_USER')
mongodb_pass=os.environ.get('MONGO_PASS')
mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
db = mongo_client.get_database()

def post_groupme(bot_id,content,attachments=[]):
    """ post and message (content) to GroupMe from bot_id
    Arguments:
    ----------
    bot_id: the string id of the bot

    content : the string to send

    attachments : array of attachment with location.
        for attaching a location:
        attachments = [{
            "type": "location",
            "lat": 0.00,
            "lng": 0.00,
            "name": "home"
        }]
    """

    url="https://api.groupme.com/v3/bots/post"

    payload={"bot_id":bot_id, "text":content, "attachments": attachments}

    r = requests.post(url, json=payload)
    if r == None or r.ok == False:
        print(f"ERROR: posting to groupme for {bot_id} {content}, {attachments}, {r.status_code}")
    return r

def send_groupme(bot_id,pokemon):
    if not bot_id:
        print(f"ERROR:invalid bot_id (None)")
        return False

    content = pokemon.format_for_groupme()
    loc =  [{
        "type": "location",
        "lat": pokemon.lat,
        "lng": pokemon.lng,
        "name": pokemon.hood if pokemon.hood else ""
      }]
    # payload={"bot_id":bot_id, "text":content, "attachments": loc}
    r = post_groupme(bot_id,content,loc)
    if not r.ok:
        print(f"ERROR: posting to groupme for {bot_id} {content} {loc}, {r.status_code}")
    return r

def get_minIV_distance_for(bot_id,pokemon_name,pokemon_lvl):
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
    d=None
    if match and len(match)>0:
        m=match[0]
        if "min_lvl_iv" in m.keys():
            m=m['min_lvl_iv']
            if 'iv' in m.keys():
                # iv should be between 0 and 100
                iv=max(0,min(100,int(m['iv'])))
            if 'distance' in m.keys():
                d=m['distance']
    return iv,d

def get_hoods_to_listen_for():
    # mongodb_user=os.environ.get('MONGO_USER')
    # mongodb_pass=os.environ.get('MONGO_PASS')
    hoods=[]
    # with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
        # db = mongo_client.get_database()
    hoods = [x.get('_id') for x in db.iControlIt.aggregate([    {"$unwind" : "$hoods"},{"$group" : {"_id" : "$hoods"}}])]
    return hoods

def process_message_for_groupme(pokemon):
    # mongodb_user=os.environ.get('MONGO_USER')
    # mongodb_pass=os.environ.get('MONGO_PASS')
    # with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
    #   db = mongo_client.get_database()

    c=Counter({'FAIL':0,'PASS':0})
    dc=Counter({'d':[]})
    for doc in db.iControlIt.find({"iSawIt_id":{"$exists":True}},{"iSawIt_id":True,"loc":True,"distance":True,"_id":False}):
        # print("process_message_for_groupme {}".format(doc['iSawIt_id']))
        # print(doc['iSawIt_id'], pokemon.name, pokemon.level)
        prefix="FAIL"
        max_distance=int(doc['distance'])
        p1=pokemon.loc
        p2=Point(doc['loc']['lat'],doc['loc']['lng'])
        d=distance_between(p1,p2)
        dc.update({"d":[d]})
        min_iv, distance = get_minIV_distance_for(doc['iSawIt_id'], pokemon.name, pokemon.level)
        if not distance: 
            distance=max_distance
        if d <= max_distance:            
            if type(min_iv) is int and \
                (min_iv == 0 or (pokemon.iv >= min_iv)):
                prefix="PASS"
                bot_id=doc['iSawIt_id']
                send_groupme(bot_id,pokemon)
        c.update({prefix})
    if c['PASS'] > 0:
        print(f"{c['FAIL']}/{c['PASS']} {dc['d']} {pokemon}")
    

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
