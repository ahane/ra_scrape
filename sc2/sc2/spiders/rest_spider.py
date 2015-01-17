import scrapy
from scrapy import log
from sc2.items import ArtistLink
#from collections import defaultdict
import urllib
import json

JSON_HEADERS = {'Accept': 'application/json', 'content-type': 'application/json'}

with open('sc_cl_id.secret', 'r') as f:
    SC_CLIENT_ID = f.read().rstrip()
    client_id_str = urllib.urlencode({"client_id": SC_CLIENT_ID})
TRACKS_URL = "http://api.soundcloud.com/users/%s/tracks.json?" + client_id_str

class RESTSpider(scrapy.Spider):
	name = 'rest_spider'

	def __init__(self, *args, **kwargs):
		super(RESTSpider, self).__init__(*args, **kwargs)
		#elf.start_urls = ['http://localhost:8000/api/artists/links/no-samples/?third_party=2']

	def start_requests(self):
		
		query = {'url': 'https://soundcloud.com/'}
		query_str = urllib.urlencode(query)
		return [scrapy.Request('http://localhost:8000/api/thirdparties/?'+query_str,
									headers=JSON_HEADERS,
									method='GET',
									callback=self.parse_third_party
									)]

	def parse_third_party(self, response):
		
		thirdparties = json.loads(response.body)
		if len(thirdparties) != 1:
			raise ValueError('Got more than one third party')
	 	tp = thirdparties[0]
	
		query = {'third_party': tp['id']}
		query_str = urllib.urlencode(query)
	
		url = 'http://localhost:8000/api/artists/links/no-samples/?' + query_str
		yield scrapy.Request(url, headers=JSON_HEADERS, method='GET',
							callback=self.parse_artist_links
							)

	def parse_artist_links(self, response):
		links = json.loads(response.body)
		for link in links:
			meta = {'third_party': link['third_party'],
					'artist': link['artist']}
			url = TRACKS_URL % link['identifier']
			log.msg(url)
			yield scrapy.Request(url, headers=JSON_HEADERS, method='GET',
							meta=meta, callback=self.parse_sc_tracklist,
							)

	def parse_sc_tracklist(self, response):
		tracks = json.loads(response.body)
		
		if tracks:	
			embeddable = (t for t in tracks if t['embeddable_by'] == 'all')
			sorted_by_plays = sorted(embeddable, key=lambda t: t.get('playback_count', 0))
			best_track = sorted_by_plays[-1]

			track_link = ArtistLink()
			track_link['url'] = best_track['uri']
			track_link['identifier'] = best_track['id']
			track_link['artist'] = response.meta['artist']
			track_link['third_party'] = response.meta['third_party']
			track_link['category'] = 'SMPL'
			
			# We could yield the track to the pipeline here
			# yield track_link
			# But instead we will POST the artists to our DB
			
			data = json.dumps(dict(track_link))
			log.msg(data)
			url = 'http://localhost:8000/api/artists/links/'
			yield scrapy.Request(url, headers=JSON_HEADERS, method='POST', body=data, callback=self.no_op)

	def no_op(self, response):
		pass


		


