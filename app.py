import sys
import asyncio
import aiohttp
import time,datetime
from shapely.geometry import  Point
from pokemon import Pokemon
from pprint import pprint
from utils import get_hoods_to_listen_for, process_message_for_groupme, point_is_in_manhattan,send_groupme
from collections import Counter

loop = asyncio.get_event_loop()

async def read_website(url):
	print("starting")
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
	in_counter=Counter()
	out_counter=Counter()
	while True:
		async with aiohttp.ClientSession(headers=headers,auto_decompress=True) as session:
			async with session.get(url,params={"since":the_time, "mons":mons}) as response:
				data = await response.json()
				meta_data = data.get('meta') if data else None
				pokemon_data = data.get('pokemons') if data else None
				the_time = meta_data.get('inserted') if meta_data else int(time.time())

		if pokemon_data:
			pokemons = [x for x in pokemon_data]
			hoods_we_listen_for = get_hoods_to_listen_for()

			for p in sorted(pokemons,key=lambda k: int(k['cp']),reverse=True ):
				loc = Point(float(p.get('lng')),float(p.get('lat')))
				# in_manhattan, distance = point_is_in_manhattan(loc)
				pokemon=Pokemon(p)
				# in_manhattan, distance = point_is_in_manhattan(pokemon.loc)
				# pokemon.is_in_manhattan=in_manhattan
				# pokemon.distance=distance


				if pokemon.hood in hoods_we_listen_for:
					in_manhattan, distance = point_is_in_manhattan(pokemon.loc)
					process_message_for_groupme(pokemon)

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
