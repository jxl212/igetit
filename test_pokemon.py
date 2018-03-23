from collections import defaultdict
import time,datetime
import concurrent.futures
from pymongo import MongoClient
from itertools import filterfalse

from common.fetcher import read_website
from common.fetcher import read_nymetro_website
from utils import db
from common.process_data import process_pokemons
# from utils.utils import mongodb_pass
# from utils.utils import mongodb_user
# from utils.utils import mongo_client

import logging
logger=logging.getLogger(__name__)


# mongo_client = MongoClient()

# from  pokemon import Pokemon

# logger.info("loading data....Done")
# def test1():
# 	pokemons=[]
# 	pokemon_data=[{"pokemon_id":"3","lat":"40.57747028","lng":"-73.97303952","despawn":"1520463317","disguise":"0","attack":"9","defense":"15","stamina":"10","move1":"215","move2":"90","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1124","level":"16","weather":"0"},{"pokemon_id":"3","lat":"40.71432286","lng":"-73.83487641","despawn":"1520462763","disguise":"0","attack":"14","defense":"4","stamina":"12","move1":"215","move2":"47","costume":"0","gender":"2","shiny":"0","form":"0","cp":"1762","level":"25","weather":"0"},{"pokemon_id":"3","lat":"40.79129628","lng":"-73.84976303","despawn":"1520462299","disguise":"0","attack":"9","defense":"0","stamina":"10","move1":"215","move2":"116","costume":"0","gender":"2","shiny":"0","form":"0","cp":"176","level":"3","weather":"0"},{"pokemon_id":"3","lat":"40.78218057","lng":"-73.82651368","despawn":"1520462102","disguise":"0","attack":"10","defense":"1","stamina":"5","move1":"215","move2":"90","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1210","level":"18","weather":"0"},{"pokemon_id":"3","lat":"40.5540584","lng":"-74.13863083","despawn":"1520461841","disguise":"0","attack":"12","defense":"10","stamina":"4","move1":"215","move2":"116","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1868","level":"27","weather":"0"},{"pokemon_id":"9","lat":"40.74039239","lng":"-73.99443497","despawn":"1520462283","disguise":"0","attack":"15","defense":"11","stamina":"15","move1":"202","move2":"36","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1882","level":"29","weather":"0"},{"pokemon_id":"9","lat":"40.58774901","lng":"-73.79296732","despawn":"1520462129","disguise":"0","attack":"7","defense":"6","stamina":"8","move1":"202","move2":"107","costume":"0","gender":"1","shiny":"0","form":"0","cp":"661","level":"11","weather":"0"},{"pokemon_id":"59","lat":"40.58938238","lng":"-73.89790709","despawn":"1520463704","disguise":"0","attack":"0","defense":"6","stamina":"7","move1":"240","move2":"103","costume":"0","gender":"1","shiny":"0","form":"0","cp":"871","level":"12","weather":"0"},{"pokemon_id":"103","lat":"40.63499436","lng":"-74.13431849","despawn":"1520462634","disguise":"0","attack":"8","defense":"13","stamina":"8","move1":"271","move2":"59","costume":"0","gender":"2","shiny":"0","form":"0","cp":"1899","level":"24","weather":"5"},{"pokemon_id":"103","lat":"40.55487363","lng":"-74.13450199","despawn":"1520462453","disguise":"0","attack":"0","defense":"15","stamina":"4","move1":"274","move2":"116","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1142","level":"15","weather":"0"},{"pokemon_id":"103","lat":"40.5918031","lng":"-73.92684295","despawn":"1520461949","disguise":"0","attack":"15","defense":"8","stamina":"8","move1":"271","move2":"59","costume":"0","gender":"1","shiny":"0","form":"0","cp":"2005","level":"25","weather":"0"},{"pokemon_id":"106","lat":"40.65395764","lng":"-74.09752191","despawn":"1520463772","disguise":"0","attack":"10","defense":"1","stamina":"3","move1":"241","move2":"56","costume":"0","gender":"1","shiny":"0","form":"0","cp":"987","level":"16","weather":"0"},{"pokemon_id":"107","lat":"40.59826583","lng":"-73.81989676","despawn":"1520462943","disguise":"0","attack":"13","defense":"3","stamina":"8","move1":"243","move2":"245","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1400","level":"25","weather":"0"},{"pokemon_id":"107","lat":"40.80869821","lng":"-73.8743878","despawn":"1520462176","disguise":"0","attack":"4","defense":"12","stamina":"11","move1":"243","move2":"115","costume":"0","gender":"1","shiny":"0","form":"0","cp":"203","level":"4","weather":"0"},{"pokemon_id":"113","lat":"40.81661704","lng":"-73.80059617","despawn":"1520462420","disguise":"0","attack":"13","defense":"2","stamina":"0","move1":"234","move2":"86","costume":"0","gender":"2","shiny":"0","form":"0","cp":"1010","level":"26","weather":"0"},{"pokemon_id":"131","lat":"40.58572346","lng":"-73.99957687","despawn":"1520463116","disguise":"0","attack":"13","defense":"12","stamina":"15","move1":"218","move2":"107","costume":"0","gender":"2","shiny":"0","form":"0","cp":"1167","level":"16","weather":"6"},{"pokemon_id":"131","lat":"40.64187824","lng":"-74.07109","despawn":"1520462002","disguise":"0","attack":"9","defense":"9","stamina":"7","move1":"218","move2":"40","costume":"0","gender":"1","shiny":"0","form":"0","cp":"2127","level":"31","weather":"6"},{"pokemon_id":"131","lat":"40.8052242","lng":"-73.88945517","despawn":"1520463304","disguise":"0","attack":"6","defense":"8","stamina":"11","move1":"230","move2":"284","costume":"0","gender":"1","shiny":"0","form":"0","cp":"397","level":"6","weather":"6"},{"pokemon_id":"134","lat":"40.60283637","lng":"-73.82210243","despawn":"1520463347","disguise":"0","attack":"3","defense":"10","stamina":"2","move1":"230","move2":"105","costume":"0","gender":"1","shiny":"0","form":"0","cp":"214","level":"3","weather":"0"},{"pokemon_id":"134","lat":"40.63438787","lng":"-74.17523584","despawn":"1520462918","disguise":"0","attack":"1","defense":"6","stamina":"6","move1":"230","move2":"58","costume":"0","gender":"1","shiny":"0","form":"0","cp":"811","level":"10","weather":"0"},{"pokemon_id":"137","lat":"40.60400628","lng":"-74.00187232","despawn":"1520465044","disguise":"0","attack":"9","defense":"5","stamina":"11","move1":"281","move2":"14","costume":"0","gender":"3","shiny":"0","form":"0","cp":"1112","level":"27","weather":"0"},{"pokemon_id":"137","lat":"40.6240571","lng":"-74.02161202","despawn":"1520464131","disguise":"0","attack":"8","defense":"2","stamina":"9","move1":"281","move2":"14","costume":"0","gender":"3","shiny":"0","form":"0","cp":"482","level":"12","weather":"0"},{"pokemon_id":"154","lat":"40.67362393","lng":"-73.79719539","despawn":"1520461813","disguise":"0","attack":"13","defense":"2","stamina":"7","move1":"215","move2":"31","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1430","level":"24","weather":"0"},{"pokemon_id":"232","lat":"40.81925769","lng":"-73.83294658","despawn":"1520462852","disguise":"0","attack":"9","defense":"0","stamina":"4","move1":"243","move2":"88","costume":"0","gender":"1","shiny":"0","form":"0","cp":"2211","level":"28","weather":"0"},{"pokemon_id":"232","lat":"40.59679554","lng":"-74.1180775","despawn":"1520461865","disguise":"0","attack":"10","defense":"4","stamina":"7","move1":"243","move2":"268","costume":"0","gender":"2","shiny":"0","form":"0","cp":"1533","level":"19","weather":"0"},{"pokemon_id":"297","lat":"40.90517956","lng":"-73.89193567","despawn":"1520464918","disguise":"0","attack":"3","defense":"8","stamina":"4","move1":"243","move2":"268","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1713","level":"24","weather":"0"},{"pokemon_id":"297","lat":"40.72365468","lng":"-73.82081579","despawn":"1520462575","disguise":"0","attack":"6","defense":"7","stamina":"4","move1":"229","move2":"268","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1298","level":"18","weather":"0"},{"pokemon_id":"297","lat":"40.78795484","lng":"-73.91324823","despawn":"1520464539","disguise":"0","attack":"7","defense":"0","stamina":"6","move1":"229","move2":"268","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1552","level":"22","weather":"0"},{"pokemon_id":"297","lat":"40.81009122","lng":"-73.91058428","despawn":"1520462703","disguise":"0","attack":"13","defense":"15","stamina":"15","move1":"229","move2":"246","costume":"0","gender":"1","shiny":"0","form":"0","cp":"2114","level":"27","weather":"0"},{"pokemon_id":"297","lat":"40.74545149","lng":"-73.71868573","despawn":"1520462229","disguise":"0","attack":"9","defense":"12","stamina":"3","move1":"243","move2":"245","costume":"0","gender":"2","shiny":"0","form":"0","cp":"194","level":"3","weather":"0"},{"pokemon_id":"297","lat":"40.84423042","lng":"-73.78368363","despawn":"1520462028","disguise":"0","attack":"7","defense":"15","stamina":"14","move1":"243","move2":"268","costume":"0","gender":"1","shiny":"0","form":"0","cp":"1217","level":"16","weather":"0"},{"pokemon_id":"297","lat":"40.58285287","lng":"-74.1655119","despawn":"1520461839","disguise":"0","attack":"9","defense":"3","stamina":"9","move1":"243","move2":"268","costume":"0","gender":"1","shiny":"0","form":"0","cp":"797","level":"11","weather":"0"}]
# 	old_data=[]
# 	now=int(time.time())


# 	# data = [x for x in data if x not in old_data]
# 	pokemons = [x for x in pokemon_data if x not in old_data] if pokemon_data else []
# 	for raw_p in pokemons:
# 			t=int(raw_p.get('despawn')) > now
# 			print(t)
# 			p=Pokemon(raw_p)
# 			print(p)
# 			old_data.append(raw_p)
# 	# x=[i for i in old_data if ]

# 	print(f"---------{len(old_data)} {len(pokemon_data)} {len(pokemons)}")
# 	try:
# 		while len(old_data)>0:
# 			now=int(time.time())
# 			old_data=[x for x in old_data if int(x.get('despawn')) > now]
# 			for x in old_data:
# 				print(int(x.get('despawn')) - now)

# 			print(f"{len(old_data)} {len(pokemon_data)} {len(pokemons)}")

# 			time.sleep(10)
# 	except KeyboardInterrupt:
# 		print("bye")

# 	# for i in [x for x in data if x not in pokemons_processed]:
# 		# print(i)

# 	# pokemons = [x for x in pokemon_data] not in pokemons_processed


def get_data_once_and_print():
    logger.info("get_data_once_and_print")

    # s=requests.Session()
    url="http://nycpokemap.com/query2.php"

        
    raw_pokemon_data,old_data = read_website(url)
    # get the_time and pokemon data from responce
    meta_data = raw_pokemon_data.get('meta') if raw_pokemon_data else None
    pokemon_data = raw_pokemon_data.get('pokemons') if raw_pokemon_data else None
    the_time = meta_data.get('inserted') if meta_data else int(time.time())
    logger.info(f"===got {len(pokemon_data)}===")
    processed_pokemons=[]
    with MongoClient() as conn:
        try:
                ret=None
                # db=conn.get_database('nyc')
                col=db.spawns
                processed_poekmons=[]
                for raw_pokemon in pokemon_data:
                        # logger.info(raw_pokemon)
                        processed_poekmon=defaultdict()
                        for attr in raw_pokemon.keys():
                                if attr in ["lng","lat"]:
                                        processed_poekmon[attr]=float(raw_pokemon[attr])
                                else:
                                        processed_poekmon[attr]=int(raw_pokemon[attr])
                              
                        processed_poekmon['date']=datetime.datetime.fromtimestamp(int(raw_pokemon['despawn']))
                        # logger.info(processed_poekmon)
                        processed_poekmons.append(processed_poekmon)
                
                
                # ret=col.insert_many(processed_poekmons)
        except Exception as e:
                logger.error(e)
        # logger.info(f"inserted {len(ret.inserted_ids)}")
        
    return

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
        logging.basicConfig(    style="{",
                                format='{asctime} [{name:^10s}][{levelname:^6s}] {message}',
                                datefmt='%m/%d/%Y %H:%M:%S',
                                level=logging.INFO)
        main()

