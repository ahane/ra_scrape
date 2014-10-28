#Scrapy settings for ra project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'ra'

SPIDER_MODULES = ['ra.spiders']
NEWSPIDER_MODULE = 'ra.spiders'

DATABASE = {'drivername': 'postgres',
            'host': 'localhost',
            'port': '5432',
            'username': 'postgres',
            'password': '212121',
            'database': 'cm'
            }

DATABASE_URL = 'http://localhost:5000/api/'
ITEM_PIPELINES = {'ra.pipelines.VenuePipeline': 100,
                  'ra.pipelines.EventPipeline': 200,
                  'ra.pipelines.ArtistPipeline': 300}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ra (+http://www.yourdomain.com)'