# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
from scrapy.exceptions import DropItem
from hinterteil import Hinterteil
import settings

db = Hinterteil(settings.DATABASE_URL)

try:
    ra = db.get_single('thirdparties', 'http://www.residentadvisor.net/', 'url')
    
except IOError:
    ra = db.insert_dict('thirdparties', {'name': 'Resident Advisor', 'url': 'http://www.residentadvisor.net/'})
    
try:
    sc = db.get_single('thirdparties', 'https://soundcloud.com/', 'url')
    
except IOError:
    sc = db.insert_dict('thirdparties', {'name': 'SoundCloud', 'url': 'https://soundcloud.com/'})


class VenuePipeline(object):
    
    def __init__(self):
        pass
        
    def process_item(self, item, spider):
        
        try:
            club = item['club']
        except KeyError:
            raise DropItem('Event %s doesnt have a venue' % item['ra_url'])
        
        try:
            location = db.get_single('locations', club['ra_url'], 'url')
            #venue = venue_page['venue']
        
        # If venue and venue page dont exist yet:
        except IOError:
            
            # Obligatory fields:
            try:
                new_location = {
                'name': club['name'],
                'address': club['adress'],
                'lat': club['lat'],
                'lon': club['lon']}

                new_location_link = {
                'url': club['ra_url'],
                'third_party': ra['id']}
                #'third_party': ra}
                
            except KeyError as key_error:
                key = key_error.message
                raise DropItem('Venue %s misses an obligatory field: %s' % (club['ra_url'], key))
                
            # Insert Venue
            location = db.insert_dict('locations', new_location)
            # Insert Venue Page
            new_location_link['location'] = location['id']        

            db.insert_dict('locations/links', new_location_link)
        #item['location'] = location
        return item
    
class EventPipeline(object):
    
    def __init__(self):
        pass
    
    def process_item(self, item, spider):

        try:
            happening = db.get_single('happenings', item['ra_url'], 'url')
                   
        # If event and event page dont exist yet:
        except IOError:
            
            location = db.get_single('locations', item['club']['ra_url'], 'url')
            #location = item['location']
            
            # Obligatory fields:
            try:
                new_happening = {
                'name': item['name'],
                'start': item['start_datetime'],
                'stop': item['end_datetime'],
                'location': location['id']}

                new_happening_link = {
                'url': item['ra_url'],
                'third_party': ra['id'],}
                
            except KeyError as key_error:
                key = key_error.message
                raise DropItem('Event %s misses an obligatory field' % (item['ra_url'], key))
                
            # Insert Event
            happening = db.insert_dict('happenings', new_happening)
            # Insert Event Page
            new_happening_link['happening'] = happening['id']
            db.insert_dict('happenings/links', new_happening_link)
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
        
        happening = db.get_single('happenings', item['ra_url'], 'url')
        db_performances = [insert_performance(happening, a) for a in db_artists]
        #item['db_performances'] = db_performances
        
        return item
    
    def insert_performance(item, happening, artist):
        ''' If the event didn't exist before, we can assume
            the event hasn't been scraped yet. We don't have
            to check for already existing performances.
        '''
        
        new_performance = {'artist': artist['id'],
                           'happening': happening['id']}
                           #'kind_id': genres['Electronic Music']['id']}
        
        performance = db.insert_dict('performances', new_performance)
        return performance
            
    def insert_artist(self, artist_item):
        
        
        try:
            artist = db.get_single('artists', artist_item['ra_url'], 'url')
        
        # If artist and artist page dont exist yet:
        except IOError:
            
            # Obligatory fields:
            new_artist = {'name': artist_item['name']}
            artist = db.insert_dict('artists', new_artist)
            pages = [('ra_url', ra), ('sc_url', sc)]
            
            for url_field, tp in pages:
                self.insert_artist_link(artist_item, url_field, tp, artist)
            
        return artist
                        
    def insert_artist_link(self, artist_item, url_field, third_party, artist):
        
        def _prepare_url(url, tp):
            if tp['name'] == 'SoundCloud':
                url = ''.join(url.split('www.'))
            return url
        
        try:
            url = _prepare_url(artist_item[url_field], third_party)
                       
            try: 
                db.get_single('artists/links', url, 'url')

            except IOError:
               
                new_artist_link = {
                'url': url,
                'third_party': third_party['id'],
                'artist': artist['id']}
                log.msg('inserting page %s' % str(new_artist_link))
                db.insert_dict('artists/links', new_artist_link)
            
        except KeyError:
            pass
        
        

                
