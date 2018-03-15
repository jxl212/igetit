import os, time,json

from pymongo import MongoClient
from termcolor import cprint, colored
import pprint
from collections import Counter, defaultdict
from pyproj import Proj
from shapely.geometry import shape, Point
import requests
import pokemon

import logging
import threading
logger = logging.getLogger()

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
        logger.error(f"failed posting to groupme for {bot_id} {content}, {attachments}, {r.status_code}")
    return r

def send_groupme(bot_id,pokemon):
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
        logger.error(f"failed posting to groupme for {bot_id} {content} {loc}, {r.status_code}")
    return r

# def check_pokemon(bot_id, pokemon_id=0, pokemon_lvl=0, pokemon_iv=0, distance=2500, max_distance=2500):
#     resutls=[]

#     col = db.get_collection('iSawIt_{}'.format(bot_id))
#     resutls=[x for x  in col.col.find(
#         {"$and" : [
#                     {"_id": {"$eq" : int(pokemon_id)}},
#                     {"min_lvl_iv":
#                         {
#                             "$elemMatch" : 
#                             {
#                                 "distance": { "$gte": distance     },
#                                 "iv":       { "$lte": pokemon_iv   },
#                                 "lvl":      { "$lte": pokemon_lvl  }
#                             }
#                         }
#                     }
#                 ]
#         })]

#     return bool(resutls and len(resutls) > 0)
    
# def get_minIV_distance_for(bot_id,pokemon_name,pokemon_lvl):
#     # mongodb_user=os.environ.get('MONGO_USER')
#     # mongodb_pass=os.environ.get('MONGO_PASS')
#     # with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
#     col = db.get_collection('iSawIt_{}'.format(bot_id))
#     match=list(col.aggregate([
#         { "$match" :{"name":pokemon_name}},
#         {"$unwind": "$min_lvl_iv"} ,
#         {"$match":{"min_lvl_iv.lvl":{"$lte":pokemon_lvl}}},
#         {"$sort":{"min_lvl_iv.lvl":-1}},
#         {"$limit":1}]))
#     iv=100
#     d=None
#     if match and len(match)>0:
#         m=match[0]
#         if "min_lvl_iv" in m.keys():
#             m=m['min_lvl_iv']
#             if 'iv' in m.keys():
#                 # iv should be between 0 and 100
#                 iv=max(0,min(100,int(m['iv'])))
#             if 'distance' in m.keys():
#                 d=m['distance']
#     return iv,d

# def get_hoods_to_listen_for():
#     # mongodb_user=os.environ.get('MONGO_USER')
#     # mongodb_pass=os.environ.get('MONGO_PASS')
#     hoods=[]
#     # with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
#         # db = mongo_client.get_database()
#     hoods = [x.get('_id') for x in db.iControlIt.aggregate([    {"$unwind" : "$hoods"},{"$group" : {"_id" : "$hoods"}}])]
#     return hoods

# def process_message_for_groupme(raw_p):
#     logger.debug(f"processing {pprint.pformat(raw_p)} messages")
#     c=Counter({'FAIL':0,'PASS':0})
#     distances_log=[]
#     p=None
#     for doc in list(db.iControlIt.find({})):
#         prefix="FAIL"
#         max_distance=int(doc['distance'])
#         iSawIt_id=doc['iSawIt_id']
#         p1=Point(float(raw_p.get('lng')),float(raw_p.get('lat')))
#         p2=Point(doc['loc']['lng'],doc['loc']['lat'])
#         pokemon_distance=distance_between(p1,p2)
#         distances_log.append(pokemon_distance)
#         is_good=check_pokemon(iSawIt_id, 
#             pokemon_id=int(raw_p.get('pokemon_id')), 
#             pokemon_lvl=int(raw_p.get('level')),
#             pokemon_iv=round((int(raw_p.get('attack'))+int(raw_p.get('stamina'))+int(raw_p.get('defence')) * 100)/(3*15)),
#             distance=int(pokemon_distance),
#             max_distance=int(max_distance))

#         if is_good:
#             prefix="PASS"
#             p=pokemon.Pokemon(raw_p)    
#             # send_groupme(iSawIt_id,p)
#             print(f"{pokemon_distance:4d} {p}")
#         c.update({prefix:1})
        
#     if c.get('PASS') > 0:
#         p= p if p else pokemon.Pokemon(raw_p)    
#         print(f"{c['FAIL']}F/{c['PASS']}P {p}")


nys = Proj(proj="lcc", lat_1=41.03333333333333, lat_2=40.66666666666666, lat_0=40.16666666666666 ,lon_0=-74 ,x_0=300000 ,y_0=0 ,ellps="GRS80" ,datum="NAD83" , units="m")
def distance_between(p1,p2):
    p1_proj = nys(p1.x, p1.y)
    p2_proj = nys(p2.x, p2.y)
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

def point_is_in_manhattan(point):
    s=get_manhattan()
    is_in_shape=s.contains(point)
    return is_in_shape


def process_one(control_info,requirements,raw_p):
    p1=Point(float(raw_p.get('lng')),float(raw_p.get('lat')))
    p2=control_info['ref_loc']
    
    pokemon_distance=distance_between(p1,p2)
    pokemon_id=int(raw_p['pokemon_id'])
    pokemon_lvl=int(raw_p['level'])
    pokemon_iv=-1
    if pokemon_lvl > -1:
        attack=int(raw_p['attack'])
        stamina=int(raw_p['stamina'])
        defence=int(raw_p['defence'])
        pokemon_iv= (attack+defence+stamina) / (3*15)
        pokemon_iv=round(pokemon_iv*100)

    pokemon_reqs = [p_req for p_req in requirements if p_req["_id"] == pokemon_id ]
    for pokemon_req in pokemon_reqs: 
        for min_req in pokemon_req['min_lvl_iv']:
            lvl_req      = min_req['lvl']
            if lvl_req > pokemon_lvl: 
                logger.debug(f"lvl: {lvl_req} > {pokemon_lvl}")
                continue
            iv_req       = min_req['iv']
            if iv_req > pokemon_iv: 
                logger.debug(f"iv: {iv_req} > {pokemon_iv}")
                continue
            distance_req = min_req.get('distance') if min_req.get('distance') else int(control_info['distance'])
            if distance_req < pokemon_distance: 
                logger.debug(f"distance: {distance_req} > {pokemon_distance}")
                continue
            # pokemon checks out
            p=pokemon.Pokemon(raw_p)    
            send_groupme(control_info['iSawIt_id'],p)
            logger.info(f"{int(pokemon_distance):4d} - {p}")
            return
            
def process_pokemons(control_info,requirements,pokemon_raw):
    logger.debug(f"[{threading.get_ident()}]: processing {len(pokemon_raw)}")
    control_info.update({"ref_loc":Point(control_info['loc']['lng'],control_info['loc']['lat'])})
    for raw_p in pokemon_raw:
        process_one(control_info,requirements,raw_p)
        
            