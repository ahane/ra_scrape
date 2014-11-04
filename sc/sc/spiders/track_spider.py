from sc.items import Track, TrackCollection
from collections import defaultdict
from scrapy.contrib.spiders import CrawlSpider, Rule
import urllib
import scrapy
import json

class TrackSpider(CrawlSpider):
    name = 'track_spider'
    allowed_domains = ['api.soundcloud.com']

    def __init__(self):
        with open('sc_cl_id.txt', 'r') as f:
            SC_CLIENT_ID = f.read().rstrip()
            sc_client_id = urllib.urlencode({'client_id': SC_CLIENT_ID})
        TRACKS_URL = 'http://api.soundcloud.com/users/%s/tracks.json?' + sc_client_id
        
        SC_ID = 2
        user_names = self.get_users_without_tracks(SC_ID)
               
        self.start_urls = [(TRACKS_URL % user) for user in user_names]

    def parse(self, response):
        tracks_response = json.loads(response.body)
        if tracks_response is not None and len(tracks_response) > 0:

            tracks_item = TrackCollection()
            tracks_item['sc_user_url'] = tracks_response[0]['user']['permalink_url']
            tracks_item['tracks'] = []

            for track_dict in tracks_response:

                track_dict = defaultdict(lambda: None, track_dict) # some track miss fields
                track = Track()
                track['sc_user_url'] = track_dict['user']['permalink_url']
                track['sc_track_url'] = track_dict['permalink_url']
                track['sc_name'] = track_dict['title']
                track['sc_track_id'] = track_dict['id']
                track['sc_num_plays'] = track_dict['playback_count']
                track['sc_description'] = track_dict['description']
                track['sc_genre'] = track_dict['genre']
                track['sc_embeddable_by'] = track_dict['embeddable_by']
                track['sc_streamable'] = track_dict['streamable']
                track['sc_license'] = track_dict['license']
                track['sc_lable_name'] = track_dict['label_name']

                tracks_item['tracks'].append(track)

            yield tracks_item

            
    def get_users_without_tracks(self, tp_id):
                
        def _extract_username(sc_url):
            return sc_url.split('/')[-1]
        
        def _tp_url(pages_df):

                if len(pages_df) > 0 and 'third_party_id' in pages_df:
                    try:
                        url = list(pages_df.query('third_party_id == %s' % tp_id)['url'])[0]

                    except IndexError, KeyError:
                        url = False

                else:
                    url = False

                return url
        
        def _check_for_samples(artist_df_in):
    
            # we copy so our changes dont persist
            artist_df = artist_df_in.copy()        

            if len(artist_df) > 0:
                pages = artist_df['pages']
                artist_df['tp_url'] = pages.apply(_tp_url)
                artist_df['has_tp'] = artist_df['tp_url'].apply(lambda x: not x == False)

                samples = artist_df['samples']
                artist_df['sample_url'] = samples.apply(_tp_url)
                artist_df['has_sample'] = artist_df['sample_url'].apply(lambda x: not x == False)


                artists_missing_sample = artist_df[artist_df['has_tp'] & ~(artist_df['has_sample'])]

                return artists_missing_sample
            
        from hinterteil import Hinterteil
        db = Hinterteil('http://localhost:5000/api/')
        artists_df = db.get_df('artist')
        
        sc_urls_no_samples = list(_check_for_samples(artists_df)['tp_url'])
        users_no_samples = [_extract_username(url) for url in sc_urls_no_samples]
        return users_no_samples