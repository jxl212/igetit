import os
import sys
import json
import time
import datetime
from shapely.geometry import Point
from pymongo import MongoClient
from utils.utils import process_pokemons, point_is_in_manhattan
from concurrent.futures import ThreadPoolExecutor
import requests
import logging
logging.basicConfig(level=logging.ERROR)

logger=logging.getLogger()

def read_website(session,the_time=0,old_data=[]):
    logger.debug(read_website.__name__)
    mons=",".join([str(x) for x in range(1,386)])
    now=int(time.time())
    # prune data for pokemoon that have despawned 
    old_data=[x for x in old_data if int(x.get('despawn')) > now]

    # GET REQUEST
    r=session.get(url=session.url,params={"since":the_time, "mons":mons})
    data = r.json()

    # get the_time and pokemon data from responce
    meta_data = data.get('meta') if data else None
    pokemon_data = data.get('pokemons') if data else None
    the_time = meta_data.get('inserted') if meta_data else int(time.time())
    logger.debug(f"===got {len(pokemon_data)}===")
   
    # pokemons is list of all new data, remove entries if it's a duplicated (in old_data)
    pokemons_all = [x for x in pokemon_data if x not in old_data] if pokemon_data else []
    

    pokemons = [x for x in pokemons_all if point_is_in_manhattan(Point(float(x.get('lng')),float(x.get('lat'))))]
    pokemons=sorted(pokemons,key=lambda k: (int(k['attack']),int(k['stamina']),int(k['defence']),int(k['level'])), reverse=True )
    return the_time, pokemons, old_data


def main():
    url="http://nycpokemap.com/query2.php"
    headers = {'accept': '*/*',
        'accept-encoding': 'gzip,deflate,br',
        'accept-language': 'en-US,en;q=0.9',
        'authority': 'nycpokemap.com',
        'dnt': '1',
        'referer': 'https://nycpokemap.com/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'}
    mongodb_user=os.environ.get('MONGO_USER')
    mongodb_pass=os.environ.get('MONGO_PASS')
    
    logger.debug("logging into mongo")
    with requests.Session() as s, \
        MongoClient(f"mongodb+srv://{mongodb_user}:{mongodb_pass}@cluster0-m6kv9.mongodb.net/nyc") as conn:
        db = conn.get_database() 
        logger.debug("logging into mongo success")

        s.headers=headers
        s.url=url
        now=time.time()
        polling_interval=60.0
        old_data=[]
        the_time=int(now)
        last_query_ts=now
        now_pre_query=now
        
        while True:
            try:
                now=time.time()
                seconds_elapsed = now-now_pre_query
                if seconds_elapsed < polling_interval:
                    sleep_time=max(0.0,(polling_interval - seconds_elapsed - 2.0))
                    logger.debug(f"~~~(Z {sleep_time:3.2f} Z)~~~~")
                    time.sleep(sleep_time)
                the_time_old=the_time
                now_pre_query=time.time()
                #pull the data from www
                the_time, pokemon_data, old_data = read_website(s, the_time, old_data)
                server_interval = int(the_time-the_time_old)
                now_post_query=time.time()
                query_interval=int(now_post_query - last_query_ts)
                last_query_ts=now_post_query
                the_time_str=datetime.datetime.fromtimestamp(the_time).strftime('%H:%M:%S')
                logger.debug(f"~~~query interval: {query_interval:3d} ~~ {the_time_str} ~~ {server_interval:3d}s ~~ the_time interval: {the_time-the_time_old:3d}:s ~~~~")
                
                #read control data
                control_data=[x for x in db.iControlIt.find({})]
                #pull pokemon settings for all users
                botid_to_collections={x['iSawIt_id'] : {'control':x,'pokemon_data': list(db.get_collection(f"iSawIt_{x['iSawIt_id'] }").find({}).sort("_id"))} for x  in control_data}                
                # for each user, process the data 
                with  ThreadPoolExecutor(max_workers=len(control_data))  as executor: 
                    for info_dict in botid_to_collections.values():
                        control_info=info_dict['control']
                        requirements=info_dict['pokemon_data']
                        executor.submit(process_pokemons, control_info, requirements, pokemon_data)
                
                
            except KeyboardInterrupt:
                logger.info("interrupted")
                break
            except Exception as e:
                logger.error(e)
                pass

if __name__ == "__main__":
    logger.debug("main called")
    main()