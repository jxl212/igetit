import sys
import asyncio
import aiohttp
import time,datetime
from shapely.geometry import Point
from pokemon import Pokemon
from pprint import pprint                   
from utils.utils import get_hoods_to_listen_for, process_message_for_groupme, point_is_in_manhattan,send_groupme
from collections import Counter

loop = asyncio.get_event_loop( )

async def read_website(url):
	print("starting")
	old_data=[]
	the_time=int(time.time()) #- 60*5 # seconds
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

		async with aiohttp.ClientSession(headers=headers,auto_decompress=True) as session:
			async with session.get(url,params={"since":the_time, "mons":mons}) as response:
				data = await response.json()
				meta_data = data.get('meta') if data else None
				pokemon_data = data.get('pokemons') if data else None
				the_time = meta_data.get('inserted') if meta_data else now

		# pokemons is list of all new data, remove entries if it's a duplicated (in old_data)
		pokemons = [x for x in pokemon_data if x not in old_data] if pokemon_data else []
		print(f"got {len(pokemons)} pokemons")
		# hoods_we_listen_for = get_hoods_to_listen_for()

		for raw_p in sorted(pokemons,key=lambda k: int(k['cp']),reverse=True ):
			loc = Point(float(raw_p.get('lng')),float(raw_p.get('lat')))
			in_manhattan = point_is_in_manhattan(loc)
			if  in_manhattan:
				# print("in manhattan")
				pokemon=Pokemon(raw_p)
			
				process_message_for_groupme(pokemon)
				old_data.append(raw_p)
		print("...")
		sys.stdout.flush()
		await asyncio.sleep(60)

try:
	loop.run_until_complete(read_website(url="https://nycpokemap.com/query2.php"))
except KeyboardInterrupt:
	print("interrupted")
except Exception as e:
	print("error:",e)
	pprint(e)
finally:
	print("bye!")
	# Zero-sleep to allow underlying connections to close
	loop.run_until_complete(asyncio.sleep(0))
	loop.close()
