from urllib import request, parse
import json
import concurrent.futures
import time
import pprint

from . import logger

def load_url(url, params={}):
    data = parse.urlencode(params).encode()
    req =  request.Request(url, data=data) 
    with request.urlopen(req) as resp:
        try:
            res_data=json.load(resp)
        except Exception as e:
            res_data=[]
            logger.error(e)
            raise e
        
        return res_data


def read_website(url,the_time=0,old_data=[]):
    logger.info(f"read_website(the_time:{the_time},old_data:{len(old_data)})")
    mons=",".join([str(x) for x in range(1,386)])
    now=int(time.time())
    # prune data for pokemoon that have despawned 
    old_data=[x for x in old_data if int(x.get('despawn')) > now]

    # POST REQUEST
    data=load_url(url,params={"since":the_time, "mons":mons})

    # # get the_time and pokemon data from responce
    # meta_data = data.get('meta') if data else None
    # pokemon_data = data.get('pokemons') if data else None
    # the_time = meta_data.get('inserted') if meta_data else int(time.time())
    # logging.debug(f"===got {len(pokemon_data)}===")

    # old_data
    
    # pokemons is list of all new data, remove entries if it's a duplicated (in old_data)
    return data, old_data


    


def read_nymetro_website(params=None,
                        url='https://ny-metro.pogoalerts.net/raw_data'):



    return load_url(url,params=params)

def fetch_data():
    logger.info("fetch_data")
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        url='https://ny-metro.pogoalerts.net/raw_data'
        f = executor.submit(fetch_data, data=(),url=url)

        try:
            logger.info("waiting for data ...")
            data=f.result()
            if type(data) == type(dict):
                logger.info(f"result returned with data length: {len(data)}")
                logger.info(f"result returned with data keys: {[k for k in data.keys()]}")
            else:
                logger.error(f"got unexpected data format of type {type(data)}")    
            
        except Exception as exc:
            logger.error('%r generated an exception: %s' % (url, exc))
            
    
    logger.info("done")
