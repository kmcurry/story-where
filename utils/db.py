import io
import os
from datetime import datetime, date
from sqlalchemy import (create_engine, Boolean, Column,
                        Date, DateTime, Integer, BigInteger,
                        Float, String, Text, 
                        Table, ForeignKey, Index)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
from pprint import pprint

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

class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    articles = relationship(
        "Article",
        secondary=articles_sections_assoc_table,
        back_populates="sections")

class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    articles = relationship(
        "Article",
        secondary=articles_keywords_assoc_table,
        back_populates="keywords")

class NLEntity(Base):
    __tablename__ = 'nlentities'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    wiki = Column(String)
    salience = Column(Float)
    proper = Column(Boolean)
    article_id = Column(Integer, ForeignKey('articles.id'))
    article = relationship(
        "Article", 
        back_populates="nl_entities")

#
# Database class
#
class Database():
    def __init__(self):
        db_conn_str = 'postgresql://' + os.environ['PG_CONN_STR']
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