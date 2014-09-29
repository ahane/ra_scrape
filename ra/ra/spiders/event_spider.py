import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
scrapy.contrib.linkextractors.lxmlhtml.LxmlLinkExtractor
from ra.items import Event, Club, Performance, Artist
import urllib
import datetime
import re
import json
import geocoder
from collections import defaultdict
BASE_URL = 'http://www.residentadvisor.net'
LISTINGS_EXT = '/events.aspx?'
BERLIN_AI = 34
#TODAY = datetime.date.today()
TODAY = datetime.date(2014, 9, 27)
with open('sc_cl_id.txt', 'r') as f:
    SC_CLIENT_ID = f.read().rstrip()
    sc_client_id = urllib.urlencode({"client_id": SC_CLIENT_ID})
listing_params = {'ai': BERLIN_AI,
                  'v': 'day',
                  'mn': TODAY.month,
                  'yr': TODAY.year,
                  'dy': TODAY.day}
today_events_url = BASE_URL + LISTINGS_EXT + urllib.urlencode(listing_params)

class RAEventSpider(CrawlSpider):
    name = 'event_spider'
    allowed_domains = [BASE_URL, 'www.residentadvisor.net', 'api.soundcloud.com']
    start_urls = [today_events_url]
    
    rules = (
        Rule(LinkExtractor(allow=(r'\/event\.aspx\?',), canonicalize=False), callback='parse_event'),
    )

    extract_digits = re.compile(r'(\d+)')
    
    def take_first(list_or_elem):
        if hasattr(list_or_elem, '__iter__'):
            return list_or_elemp[0]
        else:
            return list_or_elem
    
    def parse_event(self, response):
        
        #url 
        #ra_event_id 
        #name    
        #date 
        #ra_club_id
        event = Event()
        event['url'] = response.url    
        event['ra_event_id'] = self.extract_digits.search(event['url']).group(1)
        event['name'] = response.xpath("//div[@id = 'sectionHead']/h1/text()").extract()[0]
        event['date'] = TODAY.isoformat()
        event['artists'] = []
        
        
        #ra_club_id 
        #url 
        #name 
        #adress 
        #ra_locale_id
        club_link = response.xpath("//a[contains(@title, 'Club profile')]")
        if club_link:
            club = Club()
            club['url'] = BASE_URL + '/' + club_link.xpath("@href").extract()[0]
            club['name'] = club_link.xpath("text()").extract()[0]
            id_match = self.extract_digits.search(club['url'])
            self.log(type(id_match))
            club['ra_club_id'] = id_match.group(1)
            club['adress'] = club_link.xpath("../text()").extract()[0]
            
            geocode = geocoder.google(club['adress'])
            if geocode.status_description == 'OK':
                club['latlon'] = geocode.latlng
            event['ra_club_id'] = club['ra_club_id']
            event['club'] = club
            
        
        lineup_selector = response.css(".lineup").xpath("a")
        if lineup_selector:
            num_artists = len(lineup_selector)
            for link_sel in lineup_selector:
                artist = Artist()
                url_ext = link_sel.xpath("@href").extract()[0]
                if url_ext[:4] == "/dj/":
                    artist['url'] = BASE_URL + url_ext
                    artist['name'] = link_sel.xpath("text()").extract()[0]
                    artist['ra_artist_id'] = url_ext.split("/")[2]
                    request = scrapy.Request(artist['url'], callback=self.parse_dj)
                    request.meta['event'] = event
                    request.meta['artist'] = artist
                    request.meta['num_artists'] = num_artists
                    yield request
        #yield event
    
    def parse_dj(self, response):
        #ra_artist_id *
        #url *
        #name *
        #sc_user
        #sc_link
        #sc_track_permalink
        #sc_value #arbitray number for ranking artists
        
        artist = response.meta['artist']
        sc_link_sel = response.xpath("//a[contains(@href, 'http://www.soundcloud.com')][contains(text(), 'SoundCloud')]/@href")
        if sc_link_sel:
            artist['sc_link'] = sc_link_sel.extract()[0]
            artist['sc_user'] = artist['sc_link'].split('/')[-1]
            
            sc_tracks_url = "http://api.soundcloud.com/users/" + artist['sc_user'] + "/tracks.json?" + sc_client_id
            request = scrapy.Request(sc_tracks_url, callback=self.parse_tracks)
            request.meta['artist'] = artist
            request.meta['event'] = response.meta['event']
            request.meta['num_artists'] = response.meta['num_artists']
            yield request
    
    def parse_tracks(self, response):
        
        artist = response.meta['artist']
        event = response.meta['event']
        tracks = json.loads(response.body)
        if tracks:
            tracks = [defaultdict(int, t) for t in tracks] #some tracks miss fields
            permalinks_plays = [(t['id'], t['playback_count']) for t in tracks]
            permalinks_plays.sort(key=lambda x: x[1], reverse=True)
            
            artist['sc_track_id'] = permalinks_plays[0][0]
            artist
            artist['sc_value'] = sum((p for l, p in permalinks_plays))
            
            event['artists'] = event['artists'] + [artist]
            if len(event['artists']) == response.meta['num_artists']: #very hacky take this out!
                yield event
        #yield event
#        yield club
    #    yield performance