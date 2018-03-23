import os
from itertools import filterfalse
import pokemon
from utils.utils import Point, distance_between, point_is_in_manhattan,send_groupme

from . import logger

def process_one(control_info, pokemon_reqs, raw_p):
    # logger.info(f"processing {pprint.pformat(raw_p)}")
    # logger.debug(p)

    try:
        raw_p['encounter_id'] != None
        
    except Exception as e:
        p=pokemon.Pokemon(raw_p)
        logger.error(e)
        raise e  
        
    p=None
    for min_req in pokemon_reqs: 
        lvl_req      = min_req['lvl']
        iv_req       = min_req['iv']
        distance_req = min_req.get('distance') if min_req.get('distance') else int(control_info['distance'])
        
        if  raw_p['level'] >= lvl_req:
            iv=(raw_p['individual_attack']+raw_p['individual_stamina']+raw_p['individual_defense'])/0.45
            if iv >= iv_req:
                if p == None:
                    p=pokemon.PoGoAlertPokemon(raw_p)

                    if p.is_in_manhattan:
                        p.distance = distance_between(p.loc,control_info['ref_loc'])

                if p.is_in_manhattan and p.distance <= distance_req: 
                    # logger.debug(f"distance: {distance_req} > {p.distance}")
                    send_groupme(control_info['iSawIt_id'],p)
                    logger.info(f"[{control_info['iSawIt_id']}] - {p}")
                    return
            
    
        
def process_pokemons(control_info,requirements,pokemon_raw):
    # logger.info(f"[{os.getpid()}]: processing {len(pokemon_raw)}")
    control_info["ref_loc"]=Point(control_info['loc']['lng'],control_info['loc']['lat'])
    for raw_p in pokemon_raw:
        pokemon_id=raw_p['pokemon_id']        
        pokemon_reqs = []
        for p_req in filterfalse(lambda x: x["_id"] != pokemon_id,requirements):
            for req in p_req['min_lvl_iv']:
                pokemon_reqs.append(req) 
        process_one(control_info,pokemon_reqs,raw_p)
    return