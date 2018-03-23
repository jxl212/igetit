import os
import json
import datetime, time, re

from utils import db
from utils.utils import shape, Point, distance_between, point_is_in_manhattan
from utils.cached_property import cached_property
# from termcolor import colored
import logging

logger = logging.getLogger(__name__)

logger.info("LOADING, PLEASE WAIT....")

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
	# with MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass)) as mongo_client:
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
		
		self.pokemon_id=None
		self.lat = None
		self.lng = None
		self.level = None
		self.cp = None
		self._gender = None
			
		self.attack = None
		self.stamina = None
		self.defense = None
		self._move1=None
		self._move2=None
		self._loc=None
		self._weather = None
		self._despawn = None
		
		self._name=None
		self._hood=None
		self._ref_locs={}
		
	
	
	def distance_form(self,ref_loc):
		if ref_loc not in self._ref_locs:
			self._ref_locs[ref_loc]=distance_between(self.loc,ref_loc)
		self.distance=self._ref_locs[ref_loc]	
		return self.distance
		
	
	@cached_property
	def despawn(self):
		return self._despawn
	
		
	@cached_property
	def name(self):
		if not self._name :
			self._name=pokemons_id2name[int(self.pokemon_id) if self.pokemon_id else 0]
		return self._name
	@cached_property
	def hood(self):
		if not self._hood:
			self._hood = get_neighborhood_from(self.loc)
		return self._hood
	@cached_property
	def loc(self):
		if not self._loc: 
			self._loc=Point(self.lng,self.lat)
		return self._loc
	@cached_property
	def move1(self):
		return movesDict.get(self._move1)
	@cached_property
	def move2(self):
		return movesDict.get(self._move2)
	@cached_property
	def gender(self):
		if int(self._gender) == 0:
			return  "Female"
		elif int(self._gender) == 1:
			return  "Male"
		return "None"
		
	@cached_property
	def weather(self):
		if self._weather and self._weather in range(len(weatherStringDic)):
			return weatherStringDic[int(self._weather)]
		return ""

	@cached_property
	def iv(self):
		theSum = self.attack + self.defense + self.stamina
		if theSum < 0:
			return -1
		theIV = theSum / 0.45
		return round(theIV)

	@cached_property
	def moveSet(self):
		if self.move1 != "":
			return f"{self._move1} | {self._move2}"
		return ""

	@cached_property
	def map_url(self):
		return f"https://nycpokemap.com/#{self.lat},{self.lng}"

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

		# txt+=" "+colored("({: >2}/{: >2}/{: >2})".format(self.attack,self.defense,self.stamina), color=txt_color,attrs=txt_attrs)
		txt+="({: >2}/{: >2}/{: >2})".format(self.attack,self.defense,self.stamina)
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
		txt+=" {}".format(self.map_url)
		# if self.iv > 90 and self.attack == 15 and self.level > 30:
		# 	txt = colored(re.sub(r"\x1b\[\d+m","",txt),"yellow",attrs=['bold','reverse'])
		# elif self.iv == 100:
		# 	txt = colored(re.sub(r"\x1b\[\d+m","",txt),"green",attrs=['bold','reverse'])
		# txt=re.sub(r"\x1b\[\d+m","",txt)
		return txt

	def format_for_groupme(self):
		txt=[]
		txt.append(f"{self.name} {self.iv}% ({self.attack:02d}-{self.defense:02d}-{self.stamina:02d}) - Level: {self.level} - (CP: {self.cp})")
		# Kadabra (95%) - (CP: 1583) - (Level: 30)
		# Until: 09:37:34PM (29:31 left)
		time_now = int(time.time())
		seconds_left=int(self.despawn)-time_now
		until=datetime.datetime.fromtimestamp(int(self.despawn)).strftime('%H:%M:%S')
		time_left="{:2d}:{:02d}".format(seconds_left//60,seconds_left % 60)
		txt.append( f"Until: {until} ({time_left})")
		# Weather boosted: None
		txt.append(f"Weather boosted: {self.weather} ")
		# IV: 15 - 13 - 15 (95%)
		txt.append(f"Attack: {self.attack:02d} - defense: {self.defense:02d} - HP: {self.stamina:02d}")
		# Moveset: Confusion - Shadow Ball
		txt.append(f"Moveset: {self.moveSet}")
		# https://nycpokemap.com#40.85207264,-73.94016119
		txt.append(self.map_url)
		return "\n".join(txt)


class PoGoAlertPokemon(Pokemon):
	def __init__(self,data):
		Pokemon.__init__(self,data)
		self.pokemon_id = int(data.get('pokemon_id'))
		self.lat = float(data.get('latitude'))
		self.lng = float(data.get('longitude'))
		self.level = int(data.get('level'))
		self.cp = int(data.get('cp'))
			
		self.attack = int(data.get('individual_attack')) 
		self.stamina = int(data.get('individual_stamina')) 
		self.defense = int(data.get('individual_defense')) 
		self._move1=data.get('move_1')
		self._move2=data.get('move_2')
		self._weather = int(data.get('weather_boosted_condition')) 
		self._despawn = data.get('disappear_time') // 1000
		
		self._name=data['pokemon_name']
		self._hood=None
		self._in_manhattan=None
		self.distance=None
		if "distance" in data.keys():
			self.distance=int(data['distance'])

		self.encounter_id=int(data['encounter_id'])
		self.default_map_zoom=18
	
	@cached_property
	def map_url(self):
		url=f"https://ny-metro.pogoalerts.net/?lat={self.lat}&lon={self.lng}&encId={self.encounter_id}&zoom={self.default_map_zoom}"
		return url
	@cached_property
	def is_in_manhattan(self):
		if not self._in_manhattan:
			self._in_manhattan = point_is_in_manhattan(self.loc)
		return self._in_manhattan
