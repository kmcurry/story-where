import io
import os
from datetime import datetime, date
from sqlalchemy import (create_engine, Boolean, Column,
                        Date, DateTime, Integer, BigInteger,
                        Float, String, Text, func, desc,
                        Table, ForeignKey, Index)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from sqlalchemy.pool import NullPool
from pprint import pprint
from marshmallow import Schema, fields

Base = declarative_base()

articles_sections_assoc_table = Table('articles_sections', Base.metadata,
    Column('articles_id', Integer, ForeignKey('articles.id')),
    Column('sections_id', Integer, ForeignKey('sections.id'))
)

articles_keywords_assoc_table = Table('articles_keywords', Base.metadata,
    Column('articles_id', Integer, ForeignKey('articles.id')),
    Column('keywords_id', Integer, ForeignKey('keywords.id'))
)

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    filepath = Column(String)
    doc_id = Column(String)
    release_date = Column(DateTime)
    classifier = Column(String)
    location = Column(String)
    headline = Column(Text)
    byline = Column(String)
    publication = Column(String)
    author = Column(String)
    abstract = Column(Text)
    body = Column(Text)
    tagline = Column(String)
    nlp_date = Column(DateTime)
    sections = relationship(
        "Section",
        secondary=articles_sections_assoc_table,
        back_populates="articles")
    keywords = relationship(
        "Keyword",
        secondary=articles_keywords_assoc_table,
        back_populates="articles")
    nl_entities = relationship(
        "NLEntity", 
        back_populates="article")

class ArticleSchema(Schema):
    id = fields.Int(dump_only=True)
    filepath = fields.Str()
    doc_id = fields.Str()
    release_date = fields.DateTime()
    classifier = fields.Str()
    location = fields.Str()
    headline = fields.Str()
    byline = fields.Str()
    publication = fields.Str()
    author = fields.Str()
    abstract = fields.Str()
    body = fields.Str()
    tagline = fields.Str()
    nlp_date = fields.DateTime()

class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    articles = relationship(
        "Article",
        secondary=articles_sections_assoc_table,
        back_populates="sections")

class SectionSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    articles = fields.Nested(ArticleSchema)

class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    articles = relationship(
        "Article",
        secondary=articles_keywords_assoc_table,
        back_populates="keywords")

class KeywordSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    articles = fields.Nested(ArticleSchema)

class NLEntity(Base):
    __tablename__ = 'nlentities'
    id = Column(Integer, primary_key=True)
    name = Column(String, ForeignKey('locations.address'))
    type = Column(String)
    wiki = Column(String)
    salience = Column(Float)
    proper = Column(Boolean)
    article_id = Column(Integer, ForeignKey('articles.id'))
    article = relationship(
        "Article", 
        back_populates="nl_entities")
    location = relationship(
        "Location",
        back_populates="nl_entities")

class LocationSchema(Schema):
    id = fields.Int(dump_only=True)

    address = fields.Str()
    formatted_address = fields.Str()
    collected_utc_date = fields.DateTime()
    type = fields.Str()

    lat = fields.Float()
    lng = fields.Float()

    has_bounds = fields.Bool()
    ne_lat = fields.Float()
    ne_lng = fields.Float()
    sw_lat = fields.Float()
    sw_lng = fields.Float()

class NLEntitySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    type = fields.Str()
    wiki = fields.Str()
    salience = fields.Float()
    proper = fields.Bool()
    location = fields.Nested(LocationSchema)
    articles = fields.Nested(ArticleSchema)

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)

    address = Column(String)
    formatted_address = Column(String)
    collected_utc_date = Column(DateTime)
    type = Column(String)

    lat = Column(Float)
    lng = Column(Float)

    has_bounds = Column(Boolean)
    ne_lat = Column(Float)
    ne_lng = Column(Float)
    sw_lat = Column(Float)
    sw_lng = Column(Float)

    nl_entities = relationship(
        "NLEntity", 
        back_populates="location")

    components = relationship(
        "LocationComponent", 
        back_populates="location")
    types = relationship(
        "LocationType", 
        back_populates="location")

class LocationComponent(Base):
    __tablename__ = 'location_components'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    location_id = Column(Integer, ForeignKey('locations.id'))
    location = relationship(
        "Location", 
        back_populates="components")

class LocationType(Base):
    __tablename__ = 'location_types'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    location_id = Column(Integer, ForeignKey('locations.id'))
    location = relationship(
        "Location", 
        back_populates="types")


#
# Database class
#
class Database():
    def __init__(self):
        db_conn_str = os.environ['PG_CONN_STR']
        ssl_args = { 
            'sslmode': 'verify-ca',
            'sslrootcert': os.environ['PG_SERVER_CA'],
            'sslcert': os.environ['PG_CLIENT_CERT'],
            'sslkey': os.environ['PG_CLIENT_KEY']
        }
        self.engine = create_engine(db_conn_str, connect_args=ssl_args, poolclass=NullPool)
        self.session = sessionmaker(bind=self.engine)()
        Base.metadata.create_all(self.engine, checkfirst=True)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def disconnect(self):
        self.session.close()
    
    def clear_nl_entities(self):
        self.session.query(NLEntity).delete()
        self.session.commit()
    
    def add_single_article(self, article):
        sections = article['sections']
        keywords = article['keywords']

        del article['sections']
        del article['keywords']

        article_entity = Article(**article)

        existing_sections = {s.name: s for s in self.session.query(Section).filter(Section.name.in_(sections)).all()}
        existing_keywords = {k.name: k for k in self.session.query(Keyword).filter(Keyword.name.in_(keywords)).all()}

        article_entity.sections = [existing_sections[s] if s in existing_sections else Section(name=s) for s in sections]
        article_entity.keywords = [existing_keywords[k] if k in existing_keywords else Keyword(name=k) for k in keywords]

        self.session.add(article_entity)
        self.session.commit()

    def copy_from_file(self, table_name, filename, header):
        with open(filename, 'r') as f:
            cols = None
            if header:
                cols = f.readline().split('\t')
            connection = self.engine.raw_connection()
            cursor = connection.cursor()
            cursor.copy_from(f, table_name, columns=cols)
            connection.commit()

    def get_articles_to_nlp(self, count):
        return self.session \
            .query(Article) \
            .filter(Article.nlp_date == None) \
            .limit(count) \
            .all()

    def get_article_doc_ids(self):
        return self.session \
            .query(Article.id, Article.doc_id) \
            .all()
    
    def get_entities_to_geocode(self):
        return self.session \
            .query(NLEntity.name) \
            .distinct(NLEntity.name) \
            .filter(NLEntity.proper, NLEntity.salience >= 0.1, NLEntity.type.in_( ("ORGANIZATION", "LOCATION") )) \
            .all()

class WebDatabase():
    def __init__(self):
        db_conn_str = os.environ['PG_CONN_STR']
        use_ssl = os.environ['PG_USE_SSL'] == 'true'

        ssl_args = {}
        if use_ssl:
            ssl_args = { 
                'sslmode': 'verify-ca',
                'sslrootcert': os.environ['PG_SERVER_CA'],
                'sslcert': os.environ['PG_CLIENT_CERT'],
                'sslkey': os.environ['PG_CLIENT_KEY']
            }

        self.engine = create_engine(db_conn_str, connect_args=ssl_args)
        self.session = sessionmaker(bind=self.engine)()
    
    def get_article(self, article_id):
        article_entity = self.session.query(Article).get(article_id)

        article_schema = ArticleSchema()
        article = article_schema.dump(article_entity)

        sections_schema = SectionSchema(many=True, exclude=["articles"])
        article['sections'] = sections_schema.dump(article_entity.sections)

        keywords_schema = KeywordSchema(many=True, exclude=["articles"])
        article['keywords'] = keywords_schema.dump(article_entity.keywords)

        nl_entities_schema = NLEntitySchema(many=True, exclude=["articles"])
        article['nlEntities'] = nl_entities_schema.dump(article_entity.nl_entities)

        return article
    
    def get_entities(self, page):
        entity_query = self.session \
            .query(NLEntity.name, func.count('*').label('entity_count'), func.array_agg(NLEntity.article_id)) \
            .filter(NLEntity.proper, NLEntity.salience >= 0.1, NLEntity.type.in_( ("ORGANIZATION", "LOCATION") )) \
            .group_by(NLEntity.name) \
            .order_by(desc('entity_count')) \
            .offset(page * 100) \
            .limit(100) \
            .cte()
            
        return self.session \
            .query(entity_query, Location) \
            .join(Location, entity_query.c.name==Location.address) \
            .all()

    def get_headlines(self, page, length):
        headlines = self.session \
            .query(Article.headline, Article.release_date, Article.id) \
            .order_by(Article.id) \
            .limit(length) \
            .offset(page * length) \
            .all()

        return headlines

    def get_locations_proper(self, page, length):
        locations_proper = self.session \
            .query(NLEntity) \
            .distinct(NLEntity.name) \
            .filter(NLEntity.proper, NLEntity.salience >= 0.1, NLEntity.type=="LOCATION") \
            .limit(length)  \
            .offset(page * length) \
            .all()

        nl_entities_schema = NLEntitySchema(many=True)
        locations_proper = nl_entities_schema.dump(locations_proper)
        
        return locations_proper
