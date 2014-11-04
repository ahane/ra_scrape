from sqlalchemy.engine.url import URL
from sqlalchemy import Column, ForeignKey, Integer, Unicode, Date, Table, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

import settings
#import ra.settings as settings

Base = declarative_base()

def db_connect():
    #return create_engine(URL(**settings.DATABASE))
    engine = create_engine('sqlite:///foo6.db')
    return engine

def create_tables(engine):
    Base.metadata.create_all(engine)

class Venue(Base):
    __tablename__ = 'venue'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    
    #one-to-many
    pages = relationship('VenuePage', backref='venue')
    
    
class VenuePage(Base):
    __tablename__ = 'venue_page'
    id = Column(Integer, primary_key=True)
    
    url = Column(Unicode, nullable=False) #the url at the third party
    page_id = Column(Unicode, nullable=True) #the id on the third party
    
    #field venue was set in backref of class Venue
    venue_id = Column(Integer, ForeignKey('venue.id'))
        
    third_party = relationship('ThirdParty', backref='venue_pages')
    third_party_id = Column(Integer, ForeignKey('third_party.id'))
    #name = Column(Unicode, nullable=False) replaced by third_party.name
    
class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    date = Column(Date, nullable=False)
    
    #one-to-many
    performances = relationship('Performance', backref='event')
    pages = relationship('EventPage', backref='event')
    
    #many-to-one
    
    venue = relationship("Venue")
    venue_id = Column(Integer, ForeignKey('venue.id'), nullable=True)

class EventPage(Base):
    __tablename__ = 'event_page'
    id = Column(Integer, primary_key=True)
    #name = Column(Unicode, nullable=False) #replaced by third_party.name
    url = Column(Unicode, nullable=False)
    
    #field event set in class Event backref
    event_id = Column(Integer, ForeignKey('event.id'))
    
    page_id = Column(Unicode, nullable=True) #id at third party
    third_party = relationship('ThirdParty', backref='event_pages')
    
class Performance(Base):
    __tablename__ = 'performance'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'))
    artist_id = Column(Integer, ForeignKey('artist.id'))
    time = Column(DateTime)

class Artist(Base):
    __tablename__ = 'artist'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    performances = relationship('Performance', backref='artist')
    pages = relationship('ArtistPage', backref='artist')
    
class ArtistPage(Base):
    __tablename__ = 'artist_page'
    id = Column(Integer, primary_key=True)
    #name = Column(Unicode, nullable=False)
    url = Column(Unicode, nullable=False)
    
    #field artist set in class Artist backref
    artist_id = Column(Integer, ForeignKey('artist.id'))
    
    page_id = Column(Unicode, nullable=True) 
    third_party = relationship('ThirdParty', backref='artist_pages')
    
#To fully normalize we should do this!
class ThirdParty(Base):
    __tablename__ = 'third_party'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    url = Column(Unicode, nullable=False)

    #potentially created by backrefs:
    #artist_pages
    #event_pages
    #venue_pages