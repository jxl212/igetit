import sys,requests,json
import time,datetime
from shapely.geometry import Point
from pokemon import Pokemon
from pprint import pprint
from utils.utils import get_hoods_to_listen_for, process_message_for_groupme, point_is_in_manhattan,send_groupme
from collections import Counter



def read_website(url="http://nycpokemap.com/query2.php"):
    print("starting")
    old_data=[]
    the_time=int(time.time()) #- 60*60 # seconds
    mons=",".join([str(x) for x in range(1,386)])
    headers = {'accept': '*/*',
		'accept-encoding': 'gzip,deflate,br',
		'accept-language': 'en-US,en;q=0.9',
		'authority': 'nycpokemap.com',
		'dnt': '1',
		'referer': 'https://nycpokemap.com/',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
		'x-requested-with': 'XMLHttpRequest'}

    while True:
            now=int(time.time())
            # prune data for pokemoon that have despawned 
            old_data=[x for x in old_data if int(x.get('despawn')) > now]

            with requests.Session() as s:                
                r=s.get(url,headers=headers,params={"since":the_time, "mons":mons})
                data = r.json()

            meta_data = data.get('meta') if data else None
            pokemon_data = data.get('pokemons') if data else None
            the_time = meta_data.get('inserted') if meta_data else now

            # pokemons is list of all new data, remove entries if it's a duplicated (in old_data)
            pokemons = [x for x in pokemon_data if x not in old_data] if pokemon_data else []
            
            # reference_loc_list = get_reference_locations()

            # for raw_p in sorted(pokemons,key=lambda k: int(k['cp']),reverse=True ):
            pokemons = [x for x in pokemons if point_is_in_manhattan(Point(float(x.get('lng')),float(x.get('lat'))))]
            for raw_p in sorted(pokemons,key=lambda k: (int(k['attack']),int(k['stamina']),int(k['defence']),int(k['level'])), reverse=True ):
                
                process_message_for_groupme(raw_p)
                old_data.append(raw_p)
            # print(f"~~~(ZZZZ)~~~~")
            time.sleep(60)

try:
	read_website()
except KeyboardInterrupt:
	print("interrupted")
except Exception as e:
	print(f"error:{e}")
	raise e
	
finally:
	print("bye!")
	# Zero-sleep to allow underlying connections to close
