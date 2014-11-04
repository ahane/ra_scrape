
import scrapy

class Track(scrapy.Item):
    sc_track_id = scrapy.Field()
    sc_track_url = scrapy.Field()
    sc_name = scrapy.Field()
    sc_user_url = scrapy.Field()
    sc_num_plays = scrapy.Field()
    sc_description = scrapy.Field()
    sc_genre = scrapy.Field()
    sc_embeddable_by = scrapy.Field()
    sc_streamable = scrapy.Field()
    sc_license = scrapy.Field()
    sc_lable_name = scrapy.Field()
    sc_last_modiefied = scrapy.Field()

class TrackCollection(scrapy.Item):
    sc_user_url = scrapy.Field()
    tracks = scrapy.Field()