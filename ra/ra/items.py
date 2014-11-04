import scrapy

class Event(scrapy.Item):
    #item_type = scrapy.Field(default='event')
    item_type = scrapy.Field()
    ra_event_id = scrapy.Field()
    ra_url = scrapy.Field()
    name = scrapy.Field()    
    start_datetime = scrapy.Field()
    end_datetime = scrapy.Field()
    #ra_club_id = scrapy.Field()
    
    #these fields are for a document-like serving
    club = scrapy.Field()
    artists = scrapy.Field()
    
class Club(scrapy.Item):
    item_type = scrapy.Field(default='club')
    ra_club_id = scrapy.Field()
    ra_url = scrapy.Field()
    name = scrapy.Field()
    adress = scrapy.Field()
    lat = scrapy.Field()
    lon = scrapy.Field()
    ra_locale_id = scrapy.Field()

class Performance(scrapy.Item):
    item_type = scrapy.Field(default='performance')
    ra_event_id = scrapy.Field()
    sc_artist_id = scrapy.Field()
    artist = scrapy.Field()
    
class Artist(scrapy.Item):
    item_type = scrapy.Field(default='artist')
    ra_artist_id = scrapy.Field()
    ra_url = scrapy.Field()
    name = scrapy.Field()
    sc_user = scrapy.Field()
    sc_url = scrapy.Field()
    #sc_track_permalink = scrapy.Field()
    #sc_track_id = scrapy.Field()
    #sc_value = scrapy.Field() #arbitray number for rankin artists
    
class Track(scrapy.Item):
    artist_id = scrapy.Field()
    sc_track_id = scrapy.Field()
    sc_user_name = scrapy.Field()
    sc_num_plays = scrapy.Field()
    sc_description = scrapy.Field()
    sc_genre = scrapy.Field()
    sc_embeddable_by = scrapy.Field()
    sc_lable_name = scrapy.Field()
    sc_last_modiefied = scrapy.Field()