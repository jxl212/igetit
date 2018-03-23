import os
import sys
import json
import time
import datetime
from shapely.geometry import Point
from pymongo import MongoClient
from utils.utils import  point_is_in_manhattan
from common.fetcher import read_nymetro_website
import concurrent.futures
from itertools import filterfalse
from common.process_data import process_pokemons
from concurrent.futures import ThreadPoolExecutor
from utils import db
import logging
logging.basicConfig(level=logging.ERROR)

logger=logging.getLogger()

def get_and_process_nymetro_data(db, params=[],old_data=[],control_settings=[],control_data={}):
    logger.debug("fetching...")
    results = read_nymetro_website(params=params)
    if results:
        len_pokemon = len( results.get('pokemons') ) if results and results.get('pokemons') else -1
        
        if 'pokemons' in results.keys():
            pokemon_data=results.get('pokemons')
            del results['pokemons']
            params.update(results)                                
        else:
            logger.error("no pokemons in results?")
            return (params,old_data)
        
        try:
            now=int(time.time())
            #filter out disaper_time older (>) then now
            old_data[:]=filterfalse(lambda t: now > t['disappear_time']//1000,old_data)
        except (TypeError) as e:
            raise e
        
        old_encounter_list=[x['encounter_id'] for x in old_data]
        # return pokemon_data whose encounter_id is not in old_data's encounter_id
        pokemon_data[:]=filterfalse(lambda x: x['encounter_id'] in old_encounter_list, pokemon_data)
        # pokemon_data = [x for x in pokemon_data if x['encounter_id'] not in [o['encounter_id'] for o in old_data]]
        logger.debug(f"read_nymetro_website returned {len(pokemon_data)}({len_pokemon}) pokemons (old:{len(old_data)})")
        old_data += pokemon_data

        
        control_settings=[x for x in db.iControlIt.find({},{'last_updated':True,'iSawIt_id':True,'_id':False})]
        for control_setting in control_settings:
            last_updated=control_setting['last_updated']
            iSawIt_id=control_setting['iSawIt_id']
            if iSawIt_id in control_data.keys():
                cached_last_updated=control_data[iSawIt_id]['control']['last_updated']
                if last_updated == cached_last_updated:
                    continue
            logger.info(f'getting settings for {iSawIt_id}')
            control_data[iSawIt_id]={
                'control':db.iControlIt.find_one( {'iSawIt_id':iSawIt_id} ),
                'pokemon_data': list(db.get_collection(f"iSawIt_{iSawIt_id}").find({}).sort("_id"))
                }

        #pull pokemon settings for all users
        # botid_to_collections={x['iSawIt_id'] : {'control':x,'pokemon_data': list(db.get_collection(f"iSawIt_{x['iSawIt_id'] }").find({}).sort("_id"))} for x  in control_data}                
        # for each user, process the data 
        # with  concurrent.futures.ThreadPoolExecutor(max_workers=len(control_data))  as executor: 
        #     futures = {
        #                 executor.submit(    
        #                                   process_pokemons, 
        #                                   info_dict['control'], 
        #                                   info_dict['poke_rules'], 
        #                                   pokemon_data
        #                                ) for info_dict in botid_to_collections.values()
        #                 }
        with  concurrent.futures.ThreadPoolExecutor()  as executor: 
            futures=[]
            for info_dict in control_data.values():
                control_info=info_dict['control']
                requirements=info_dict['pokemon_data']
                futures += [ executor.submit(process_pokemons, control_info, requirements, pokemon_data.copy()) ]
                
            try:
                concurrent.futures.wait(futures)
            except Exception as exc:
                logger.error(f"process_pokemon generated an exception: {exc}")
                raise exc


    # return (params, old_data)
    return params


def main():

   # get_data_once_and_print()
    logger.info("main()...")
    token='4ah+lvEDKrfzodM3psdg1P7jeIk3d2uRYK4dV+omN4o='
    
    params={
        'bigKarp': 'false',
        'eids': '0',
        'exEligible': 'false',
        'exMinIV': '0',
        'gyms': 'false',
        'lastgyms': 'false',
        'lastpokemon': 'true',
        'lastpokestops': 'false',
        'lastslocs': 'false',
        'lastspawns': 'false',
        'luredonly': 'false',
        'minIV': '0',
        'minLevel': '0',
        'neLat': '40.8968744414486',
        'neLng': '-73.84092242090662',
        'oNeLat': '40.8968744414486',
        'oNeLng': '-73.84092242090662',
        'oSwLat': '40.56699275763961',
        'oSwLng': '-74.13823992578943',
        'pokemon': 'true',
        'pokestops': 'false',
        'prevMinIV': '0',
        'prevMinLevel': '0',
        'reids': '0',
        'scanned': 'false',
        'spawnpoints': 'false',
        'swLat': '40.56699275763961',
        'swLng': '-74.13823992578943',
        'timestamp': f'{int(time.time())}',
        'tinyRat': 'false',
        'token': f'{token}'
    }

    

    while True:
        try:
            get_and_process_nymetro_data(db,params)

            # elapsed=time.time()-now
            # delay=10
            # remaining=10-elapsed
            # if remaining < 0:
            #     remaining=0
            # time.sleep(remaining)
        except KeyboardInterrupt:
            logger.info("User Interupted")
            break
        except Exception as e:
            logger.error(e)
            raise e

if __name__ == "__main__":
    logger.debug("main called")
    main()