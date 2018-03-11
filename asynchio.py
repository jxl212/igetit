from aiohttp import web
import sys
import asyncio
import aiohttp
import time,datetime
from shapely.geometry import  Point
from pokemon import Pokemon
from pprint import pprint
from utils.utils import get_hoods_to_listen_for, process_message_for_groupme, point_is_in_manhattan,send_groupme
from collections import Counter

async def read_website(app):
    print("~~~starting~~~~")
    the_time=int(time.time()) - 10*5 # seconds
    mons=",".join([str(x) for x in range(1,386)])
    headers = {'accept': '*/*',
        'accept-encoding': 'gzip,deflate,br',
        'accept-language': 'en-US,en;q=0.9',
        'authority': 'nycpokemap.com',
        'dnt': '1',
        'referer': 'https://nycpokemap.com/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'}
    url="https://nycpokemap.com/query2.php"

    # in_counter=Counter()
    # out_counter=Counter()
    while True:
        print("it's true...")
        async with aiohttp.ClientSession(headers=headers,auto_decompress=True) as session:
            print(f"session: {session}")
            async with session.get(url,params={"since":the_time, "mons":mons}) as response:
                print(f"response: {response}")
                data  = await response.json()

        if data:
            hoods_we_listen_for = get_hoods_to_listen_for()
            pokemons_list = [x for x in data.get('pokemons')]
            meta_data = data['meta']
            the_time=meta_data['inserted']

            pokemons=pokemons_list
            # t_start=time_now = int(time.time())

            print(len(pokemons_list))

            for p in sorted(pokemons,key=lambda k: int(k['cp']),reverse=True ):
                # loc = Point(float(p.get('lng')),float(p.get('lat')))
                # in_manhattan, distance = point_is_in_manhattan(loc)
                pokemon=Pokemon(p)
                # in_manhattan, distance = point_is_in_manhattan(pokemon.loc)
                # pokemon.is_in_manhattan=in_manhattan
                # pokemon.distance=distance

                # out_counter.update(Counter({pokemon.name}))
                if pokemon.hood in hoods_we_listen_for:
                    # in_manhattan = point_is_in_manhattan(pokemon.loc)
                    process_message_for_groupme(pokemon)
                    # in_counter.update(Counter({pokemon.name}))

        print("...")
        sys.stdout.flush()
        await asyncio.sleep(10)

async def start_background_tasks(app):
    app['pogo_fetch'] = app.loop.create_task(read_website(app))

async def cleanup_background_tasks(app):
    app['pogo_fetch'].cancel()
    await app['redis_listener']


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

app = web.Application()
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

app.router.add_get('/', handle)
app.router.add_get('/{name}', handle)

web.run_app(app)
