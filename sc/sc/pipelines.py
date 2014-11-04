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
    sc = db.get_single('third_party', 'SoundCloud', 'name')
    
except IOError:
    sc = db.insert_dict('third_party', {'name': 'SoundCloud', 'url': 'https://soundcloud.com/'})

log.start()    
class TrackCollectionPipeline(object):
    
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        
        tracks = item['tracks']
        embeddable_tracks = [t for t in tracks if t['sc_embeddable_by'] == 'all' and t['sc_streamable']]
        embeddable_tracks.sort(key=lambda x: x['sc_num_plays'])
        
        most_played_track = embeddable_tracks[-1]
        
        return most_played_track

class TrackPipeline(object):
    
    '''
    track['sc_user_url']
    track['sc_name']
    track['sc_track_id']
    track['sc_num_plays']
    track['sc_description']
    track['sc_genre']
    track['sc_embeddable_by']
    track['sc_streamable']
    track['sc_license']
    track['sc_lable_name']
    '''
    def process_item(self, item, spider):
        track_item = item
        user_url = track_item['sc_user_url']
        try:
            db_artist = db.get_single('artist_page', user_url, 'url')['artist']
        
            new_artist_sample = {
                'url': track_item['sc_track_url'],
                'resource_id': track_item['sc_track_id'],
                'name': track_item['sc_name'],
                #'description': track_item['sc_description'],
                'genre_string': track_item['sc_genre'],
                #'label': track_item['sc_lable_name'],
                #'license': track_item['sc_license'],    
                'artist_id': db_artist['id'],
                'third_party_id': sc['id']}
            
            log.msg('Inserting:')
            log.msg(str(new_artist_sample))
            log.msg('--')
            db.insert_dict('artist_sample', new_artist_sample)
        
        except IOError:
            raise
        return item