import urllib
import json
from ra.items import Track
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
# artist_id = scrapy.Field()
# sc_track_id = scrapy.Field()
# sc_user_name = scrapy.Field()
# sc_num_plays = scrapy.Field()
# sc_description = scrapy.Field()
# sc_genre = scrapy.Field()
# sc_embeddable_by = scrapy.Field()
# sc_lable_name = scrapy.Field()
# sc_last_modiefied = scrapy.Field()
class SoundCloudSpider(CrawlSpider):
    name = 'sc_track_spider'
    allowed_domains = ['api.soundcloud.com']

    def __init__(self):
        with open('sc_cl_id.txt', 'r') as f:
            SC_CLIENT_ID = f.read().rstrip()
            sc_client_id = urllib.urlencode({"client_id": SC_CLIENT_ID})
        TRACKS_URL = "http://api.soundcloud.com/users/%s/tracks.json?"+sc_client_id
        
        self.users_dict = get_sc_users_without_tracks()
        self.user_names = users_dict.keys()
        
        self.start_urls = [(TRACKS_URL % user) for user in user_names]

    def parse(self, response):
        tracks = json.loads(response.body)
        if tracks:
            for track_dict in tracks:
                track_dict =  defaultdict(int, track_dict) # some track miss fields
            track = Track()
            track['sc_user_name'] = track_dict['user']['username']
            track['artist_id'] = users_dict[track['sc_user_name']] #we look up the internal artist id
            track['sc_track_id'] = track_dict['id']
            track['sc_num_plays'] = track_dict['playback_count']
            track['sc_description'] = track_dict['description']
            track['sc_genre'] = track_dict['genre']
            track['sc_embeddable_by'] = track_dict['embeddable_by']
            track['sc_lable_name'] = track_dict['label_name']
            track['sc_last_modiefied'] = track_dict['last_modiefied']
            yield track
            
    def get_sc_users_without_tracks(self):
        from db.dbmodel import db_connect, create_tables, ArtistPage, ThirdParty, ArtistSample
        from sqlalchemy.orm import sessionmaker
        
        engine = db_connect()
        create_tables(engine)
        Session = sessionmaker(bind=engine)
        s = Session()

        left_outer = s.query(ArtistPage).join(ThirdParty).outerjoin(
                        ArtistSample, ArtistPage.artist_id == ArtistSample.artist_id
                        ).filter(ArtistSample.sample_id == None, ThirdParty.name == 'SoundCloud')

        users = {a.page_id: a.artist_id for a in left_outer}

        s.close()
        return users



