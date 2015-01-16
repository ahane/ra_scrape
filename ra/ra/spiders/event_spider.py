import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
scrapy.contrib.linkextractors.lxmlhtml.LxmlLinkExtractor
from ra.items import Event, Club, Performance, Artist
import urllib
import datetime
from datetime import timedelta
import pytz
import re
import geocoder
BASE_URL = 'http://www.residentadvisor.net'
LISTINGS_EXT = '/events.aspx?'
LOCALE_TZ = {34: 'Europe/Berlin'}

# Helper Functions
extract_digits_re = re.compile(r'(\d+)')

def datetimes_from_date_div(date_div, locale):
    ''' Extracts start and end datetimes from
        the resident advisor date div
    '''
    
    links = date_div.xpath('a/@href').extract()
    num_date_links = len(links)
    start_date = date_from_events_url(links[0])
    end_date = None
    if num_date_links > 1:
        end_date = date_from_events_url(links[-1])
    
    start_time, end_time = times_from_str(date_div.extract())
    tzstring = LOCALE_TZ[locale]
    start_datetime, end_datetime = join_times_dates(start_date, end_date, start_time, end_time, tzstring)
    
    return start_datetime, end_datetime

def date_from_events_url(url):
    from urlparse import parse_qs, urlparse
    from datetime import date
    date_dict = parse_qs(urlparse(url).query, keep_blank_values=True)
    try:
        y = int(date_dict['yr'][0])
        m = int(date_dict['mn'][0])
        d = int(date_dict['dy'][0])
    except:
        raise
    return date(y, m , d)

def times_from_str(string):
    '''
        Looks for '12:00 - 13:00' in a string and returns
        both times as python time objects.
    '''
    def time_from_str(time_str):
        return datetime.datetime.strptime(time_str, '%H:%M').time()
    
    def search_start_end(string):
        match = re.search('(\d\d\:\d\d)\s\-\s(\d\d\:\d\d)', string)
        if match:
            start_str = match.group(1)
            start_time = time_from_str(start_str)
            
            end_str = match.group(2)
            end_time = time_from_str(end_str)
        else:
            raise KeyError('Coulnt find start and end times')
        
        return start_time, end_time
            
    def search_start(string):
        match = re.search('(\d\d\:\d\d)', string)
        if match:
            start_str = match.group(1)
            start_time = time_from_str(start_str)
       
        else:
            raise KeyError('Couldnt find start time')
        
        return start_time
    
    start_time, end_time = None, None
    
    try:
        start_time, end_time = search_start_end(string)
    except KeyError:
        try:
            start_time = search_start(string)
        except KeyError:
            pass
    return start_time, end_time

def join_times_dates(start_date, end_date, start_time, end_time, tzstring):
    ''' Takes one or more dates and two times and turns them
        into a start datetime and an end datetime.
    '''    
    
    DEFAULT_START_TIME = '23:59'
    DEFAULT_DURATION = 6
    
    from datetime import datetime, timedelta
    
    
    def same_day(st, et):
        if not st or not et:
            return True
        else:
            return st <= et
    
    def datetime_from_date_time(date, time):
        dt = datetime(date.year, date.month, date.day, time.hour, time.minute)
        tz = pytz.timezone(tzstring)
        return tz.localize(dt)
    
    if not start_time:
        start_time  = datetime.strptime(DEFAULT_START_TIME, '%H:%M').time()
    
    start_datetime = datetime_from_date_time(start_date, start_time)
    
    
    # If we didn't receive a end_date and the end time is
    # after the start time, the event ends on the same day.
    if not end_date and same_day(start_time, end_time):
        end_date = start_date
    
    # If no end_date and end time is before start time
    # the event ends one day after the start date
    elif not end_date and not same_day(start_time, end_time):
        end_date = start_date + timedelta(1) #add one day
    
    # Otherwise we use the end_date we got passed
    else:
        pass
    
    if not end_time:
        duration = timedelta(hours=DEFAULT_DURATION)
        end_datetime = start_datetime + duration
        end_time = end_datetime.time()
    
    end_datetime = datetime_from_date_time(end_date, end_time)
    
    return start_datetime, end_datetime

# Actual Spider:
class RAEventSpider(CrawlSpider):
    
    name = 'event_spider'
    allowed_domains = [BASE_URL, 'www.residentadvisor.net', 'api.soundcloud.com']
    rules = [Rule(LinkExtractor(allow=(r'\/event\.aspx\?',), canonicalize=False),
                    callback='parse_event'),
            ]


    def __init__(self, ra_locale=34, num_days=3, *args, **kwargs):
        super(CrawlSpider, self).__init__(*args, **kwargs)
        
        today = datetime.date.today()
        dates = [today + timedelta(i) for i in range(num_days)]
        listings_params = [{'ai': ra_locale,
                          'v': 'day',
                          'mn': d.month,
                          'yr': d.year,
                          'dy': d.day} for d in dates]
        self.locale = ra_locale
        self.start_urls = [BASE_URL + LISTINGS_EXT + urllib.urlencode(p) for p in listings_params]
        

     
    def parse_event(self, response):
        '''
            @url http://www.residentadvisor.net/events.aspx?ai=34&v=day&mn=10&yr=2014&dy=20
            @returns requests 5
            @returns items 1
        '''
        
        event = Event()
        event['ra_url'] = response.url    
        event['ra_event_id'] = extract_digits_re.search(event['ra_url']).group(1)
        event['item_type'] = 'event'
        
        event_title = response.xpath("//div[@id = 'sectionHead']/h1/text()").extract()[0]
        event['name'] = re.match('(.+)\sat.+$', event_title).group(1) #remove 'at LOCATION'
        
        date_div = response.xpath("//div[text()='Date /']/..")[0]
        
        start, end = datetimes_from_date_div(date_div, self.locale)
        event['start_datetime'], event['end_datetime'] = start.isoformat(), end.isoformat()
        event['artists'] = []
       
        club_link = response.xpath("//a[contains(@title, 'Club profile')]")
        if club_link:
            club = Club()
            club['ra_locale_id'] = self.locale
            club['ra_url'] = BASE_URL + '/' + club_link.xpath("@href").extract()[0]
            club['name'] = club_link.xpath("text()").extract()[0]
            id_match = extract_digits_re.search(club['ra_url'])
            #self.log(type(id_match))
            club['ra_club_id'] = id_match.group(1)
            club['adress'] = club_link.xpath("../text()").extract()[0]
            
            ## Todo: move geocoding into sperate scraper
            geocode = geocoder.google(club['adress'])
            if geocode.status_description == 'OK':

                club['lat'] = geocode.latlng[0]
                club['lon'] = geocode.latlng[1]
            #event['ra_club_id'] = club['ra_club_id']
            event['club'] = club
        
        lineup_selector = response.css(".lineup").xpath("a")
        if lineup_selector:
            num_artists = len(lineup_selector)
            for link_sel in lineup_selector:
                artist = Artist()
                url_ext = link_sel.xpath("@href").extract()[0]
                if url_ext[:4] == "/dj/":
                    artist['ra_url'] = BASE_URL + url_ext
                    artist['name'] = link_sel.xpath("text()").extract()[0]
                    artist['ra_artist_id'] = url_ext.split("/")[2]
                    
                    #step into RA artist page
                    request = scrapy.Request(artist['ra_url'], callback=self.parse_artist_page)
                    request.meta['event'] = event
                    request.meta['artist'] = artist
                    request.meta['num_artists'] = num_artists
                    yield request
        else:
            yield event
    
    def parse_artist_page(self, response):
        
        artist = response.meta['artist']
        event = response.meta['event']
        
        sc_link_sel = response.xpath("//a[contains(@href, 'http://www.soundcloud.com')][contains(text(), 'SoundCloud')]/@href")
        if sc_link_sel:
            artist['sc_url'] = sc_link_sel.extract()[0]
            artist['sc_user'] = artist['sc_url'].split('/')[-1]
        
        event['artists'] = event['artists'] + [artist]
        
        if response.meta['num_artists'] == len(event['artists']):
           # from scrapy.shell import inspect_response
           # inspect_response(response)
            yield event    
    
    

    
    