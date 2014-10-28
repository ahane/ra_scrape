# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
from datetime import datetime
from scrapy.exceptions import DropItem
from hinterteil import Hinterteil
import settings

db = Hinterteil(settings.DATABASE_URL)

try:
    ra = db.get_single('third_party', 'Resident Advisor', 'name')
    
except IOError:
    ra = db.insert_dict('third_party', {'name': 'Resident Advisor', 'url': 'http://www.residentadvisor.net/'})

try:
    berlin = db.get_single('region', 'Berlin', 'name')
    
except IOError:
    berlin = db.insert_dict('region',
                         {'name': 'Berlin', 
                          'country': 'DE',
                          'lat': 52.498757, 
                          'lon': 13.418652})

ra_regions = {34: berlin}
    
try:
    techno = db.get_single('performance_kind', 'Electronic Music', 'name')
    
except:
    techno = db.insert_dict('performance_kind', {'name': 'Electronic Music'})
    
genres = {'Electronic Music': techno}

log.start()
class VenuePipeline(object):
    
    def __init__(self):
        pass
        
    def process_item(self, item, spider):
        
        try:
            club = item['club']
        except KeyError:
            raise DropItem('Event %s doesnt have a venue' % item['ra_url'])
        
        try:
            venue_page = db.get_single('venue_page', club['ra_url'], 'url')
            venue = venue_page['venue']
        
        # If venue and venue page dont exist yet:
        except IOError:
            
            region = ra_regions[club['ra_locale_id']]
            # Obligatory fields:
            try:
                new_venue = {
                'name': club['name'],
                'adress_string': club['adress'],
                'lat': club['lat'],
                'lon': club['lon'],
                'region_id': region['id'],
                'last_modified': datetime.today().isoformat(),
                'source_id': ra['id']}

                new_venue_page = {
                'url': club['ra_url'],
                'third_party_id': ra['id']}
                #'third_party': ra}
                
            except KeyError as key_error:
                key = key_error.message
                raise DropItem('Venue %s misses an obligatory field: %s' % (club['ra_url'], key))
                
            # Insert Venue
            venue = db.insert_dict('venue', new_venue)
            # Insert Venue Page
            new_venue_page['venue_id'] = venue['id']
            #new_venue_page['venue'] = venue
            
            #TODO figure out why we have to use ID instead of the objects..
            venue_page = db.insert_dict('venue_page', new_venue_page)
            
                   
        return item
    
class EventPipeline(object):
    
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        
        
        try:
            event_page = db.get_single('event_page', item['ra_url'], 'url')
            event = event_page['event']
            raise DropItem('Event %s already in database' % item['ra_url'])
        
        # If event and event page dont exist yet:
        except IOError:
            
            venue = db.get_single('venue_page', item['club']['ra_url'], 'url')['venue']
            
            # Obligatory fields:
            try:
                new_event = {
                'name': item['name'],
                'start_datetime': item['start_datetime'],
                'end_datetime': item['end_datetime'],
                'source_id': ra['id'],
                'venue_id': venue['id'],
                'last_modified': datetime.today().isoformat()}

                new_event_page = {
                'url': item['ra_url'],
                'third_party_id': ra['id'],}
                
            except KeyError as key_error:
                key = key_error.message
                raise DropItem('Event %s misses an obligatory field' % (item['ra_url'], key))
                
            # Insert Event
            event = db.insert_dict('event', new_event)
            # Insert Event Page
            new_event_page['event_id'] = event['id']
            event_page = db.insert_dict('event_page', new_event_page)
            #db.append_child('event', event, 'pages', new_event_page)
            
        #item['db_event'] = event        
        return item
    

class ArtistPipeline(object):
    
    def __init__(self):
        pass
       
    
    def process_item(self, item, spider):
        
        insert_artist = self.insert_artist
        insert_performance = self.insert_performance
        
        artists = item['artists']
        processed_artists = [insert_artist(a) for a in artists]
        db_artists = [a for a in processed_artists if a] #Filter possbile `None`s
        #item['db_artists'] = db_artists
        
        event = db.get_single('event_page', item['ra_url'], 'url')['event']
        db_performances = [insert_performance(a, event) for a in db_artists]
        #item['db_performances'] = db_performances
        
        return item
    
    def insert_performance(item, event, artist):
        ''' If the event didn't exist before, we can assume
            the event hasn't been scraped yet. We don't have
            to check for already existing performances.
        '''
        
        new_performance = {'artist_id': artist['id'],
                           'event_id': event['id'],
                           'kind_id': genres['Electronic Music']['id']}
        
        performance = db.insert_dict('performance', new_performance)
        #db.append_child('event', event, 'performances', new_performance)
        
        return performance
            
    def insert_artist(self, artist):
        
        try:
            artist_page = db.get_single('artist_page', artist['ra_url'], 'url')
            artist = artist_page['artist']
        
        # If artist and artist page dont exist yet:
        except IOError:
            
            # Obligatory fields:
            try:
                new_artist = {
                'name': artist['name'],
                'source_id': ra['id'],
                'last_modified': datetime.today().isoformat()}

                new_artist_page = {
                'url': artist['ra_url'],
                'third_party_id': ra['id']}
            
            except KeyError as key_error:
                key = key_error.message
                self.log('Couldnt add artist %s because field was missing: %s', (artist['ra_url'], key))
                return None
            
            artist = db.insert_dict('artist', new_artist)
            # Insert Artist Page
            new_artist_page['artist_id'] = artist['id']
            artist_page = db.insert_dict('artist_page', new_artist_page)
            #db.append_child('artist', artist, 'pages', new_artist_page)
            
        return artist