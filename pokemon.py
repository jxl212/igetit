import os
import json
import datetime, time, re
from shapely.geometry import shape, Point
from pymongo import MongoClient
# from termcolor import colored


pokemons_id2name=[]
geometries=[]

def build_pokemon_data():
	global pokemons_id2name
	pokemons_id2name.clear()
	pokemons=[]
	with open("json/pokemons.json",encoding="utf-8") as file:
		pokemons=json.load(file)
	for pokemon in pokemons:
		pokemons_id2name.append(pokemon['name'])
	pokemons_id2name.insert(0,"")

build_pokemon_data()
assert pokemons_id2name[384] == "Rayquaza"

manhattan_shape=None
def get_manhattan():
	global manhattan_shape
	if manhattan_shape != None: return manhattan_shape
	with open("json/boros.json",encoding="utf-8") as file:
		m=json.load(file)
		manhattan_shape=shape(m['geometry'])
	return manhattan_shape
manhattan_shape=get_manhattan()

def get_geom():
	global geometries
	if geometries != []: return geometries

	geometries.clear()
	mongodb_user=os.environ.get('MONGO_USER')
	mongodb_pass=os.environ.get('MONGO_PASS')
	with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
		db = mongo_client.get_database()
		hoods = [x for x in db.neighborhoods.aggregate([
				{"$addFields":{"_id":"$name2","propreties.name":"$name2","coordinates":"$geometry.coordinates","type":"$geometry.type"}},
				{"$project":{"_id":1,"coordinates":1,"type":1,"propreties":1}}])]
		for hood in hoods:
			s=shape(hood)
			geometries.append({"name":hood['_id'],"shape":s})
	return geometries
geometries=get_geom()
def get_neighborhood_from(point):
	for shape_dic in get_geom():
		s=shape_dic['shape']
		if s.contains(point):
			return shape_dic['name']
	return "??"

def build_pokemon_moves_dict():
	pokemon_moves = {}
	with open("json/moves.json",encoding="utf-8") as file:
		pokemon_moves=json.load(file)
	return pokemon_moves


weatherStringDic = ("None","Clear","Rainy","Partly Cloudy","Cloudy","Windy","Snow","Fog")
movesDict = build_pokemon_moves_dict()

class Pokemon:
	def __init__(self,data):
		if data is None or data == {}:
			return
		self.pokemon_id = int(data.get('pokemon_id'))
		self.lat = float(data.get('lat'))
		self.lng = float(data.get('lng'))
		self.level = int(data.get('level'))
		self.cp = int(data.get('cp'))
		self.costume = int(data.get('costume'))
		self.shiny = int(data.get('shiny'))
		self.costume = int(data.get('costume'))
		self.gender = ""
		if int(data.get('gender')) == "1":
			self.gender = "Male"
		elif int(data.get('gender')) == '2':
			self.gender = "Female"
		self.attack = int(data.get('attack'))
		self.move1 = movesDict.get(data.get('move1')) if data.get('move1') != None else ""
		self.move2 = movesDict.get(data.get('move2')) if data.get('move2') != None else ""
		self.stamina = int(data.get('stamina'))
		self.defence = int(data.get('defence'))
		self.weather = int(data.get('weather'))
		self.despawn = int(data.get('despawn'))
		self.nycpokemap_url=f"https://nycpokemap.com/#{self.lat},{self.lng}"
		self.name=pokemons_id2name[self.pokemon_id]
		self.loc = Point(self.lng,self.lat)
		self.hood=get_neighborhood_from(self.loc)
		self.distance=None
		if "distance" in data.keys():
			self.distance=int(data['distance'])


	@property
	def weatherString(self):
		if self.weather in range(len(weatherStringDic)):
			return weatherStringDic[self.weather]
		return ""

	@property
	def iv(self):
		theSum = self.attack + self.defence + self.stamina
		if theSum < 0:
			return -1
		theIV = theSum * 100 / (3*15)
		return round(theIV)

	@property
	def moveSet(self):
		if self.move1 != "":
			return f"{self.move1} | {self.move2}"
		return ""

	def __str__(self):
		# txt_color=None
		# if self.cp < 0:
		# 	txt_color="white"

		# txt=colored("{: <10s} (CP: {:5d})".format(self.name,self.cp).ljust(20), color=txt_color,attrs=['bold'] if self.iv > 90 and self.attack==15 else []).rjust(15)
		txt=f"{self.name: <10s} (CP: {self.cp:5})".ljust(20)

		# txt+=" "+colored("{}%".format(self.iv).rjust(5), color=txt_color,attrs=['bold'] if self.iv > 90 else [])
		txt+="{}%".format(self.iv).rjust(5)
		# txt_attrs = []
		# if self.attack == 15:
		# 	txt_attrs=['bold']

		# txt+=" "+colored("({: >2}/{: >2}/{: >2})".format(self.attack,self.defence,self.stamina), color=txt_color,attrs=txt_attrs)
		txt+="({: >2}/{: >2}/{: >2})".format(self.attack,self.defence,self.stamina)
		# txt+=" "+colored(" L{}".format(self.level).ljust(3),color=txt_color,attrs=['bold'] if self.level > 30 else [])
		txt+=" L{}".format(self.level).ljust(3)
		if self.distance :
			txt+=" {:10}".format(self.distance)
		time_now = int(time.time())
		seconds_left=int(self.despawn)-time_now
		until=datetime.datetime.fromtimestamp(int(self.despawn)).strftime('%H:%M:%S')
		time_left="{:2d}:{:02d}".format(seconds_left//60,seconds_left % 60)
		txt+= f" Until: {until} ({time_left})"

		# txt+=f" gender:{self.gender: <4}" if self.gender != "" else ""
		txt+=" {:10.10}".format(self.moveSet)
		txt+=" {:20.20}".format(self.hood)
		
		# txt+=" "+colored("{:<15}".format(self.weatherString), "blue" if self.weather not in [None,"None",""] else None)
		txt+=" {}".format(self.nycpokemap_url)
		# if self.iv > 90 and self.attack == 15 and self.level > 30:
		# 	txt = colored(re.sub(r"\x1b\[\d+m","",txt),"yellow",attrs=['bold','reverse'])
		# elif self.iv == 100:
		# 	txt = colored(re.sub(r"\x1b\[\d+m","",txt),"green",attrs=['bold','reverse'])
		# txt=re.sub(r"\x1b\[\d+m","",txt)
		return txt

	def format_for_groupme(self):
		txt=[]
		txt.append(f"{self.name} {self.iv}% ({self.attack:02d}-{self.defence:02d}-{self.stamina:02d}) - Level: {self.level} - (CP: {self.cp})")
		# Kadabra (95%) - (CP: 1583) - (Level: 30)
		# Until: 09:37:34PM (29:31 left)
		time_now = int(time.time())
		seconds_left=int(self.despawn)-time_now
		until=datetime.datetime.fromtimestamp(int(self.despawn)).strftime('%H:%M:%S')
		time_left="{:2d}:{:02d}".format(seconds_left//60,seconds_left % 60)
		txt.append( f"Until: {until} ({time_left})")
		# Weather boosted: None
		txt.append(f"Weather boosted: {self.weatherString} ")
		# IV: 15 - 13 - 15 (95%)
		txt.append(f"Attack: {self.attack:02d} - Defence: {self.defence:02d} - HP: {self.stamina:02d}")
		# Moveset: Confusion - Shadow Ball
		txt.append(f"Moveset: {self.moveSet}")
		# https://nycpokemap.com#40.85207264,-73.94016119
		txt.append(self.nycpokemap_url)
		return "\n".join(txt)

