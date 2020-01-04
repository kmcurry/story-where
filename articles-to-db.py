# TLA 2.a
# Extract text from DOM Paths and write to database

import csv
import os
import re
import xml.etree.ElementTree as ET
from pprint import pprint
from shutil import copyfile
from utils.db import Database

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
  cleantext = re.sub(cleanr, '', raw_html.encode("ascii", errors="ignore").decode().replace("\n", "|"))
  return cleantext

def get_text(tag_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    return cleanhtml("".join(tag.itertext())) if tag is not None else None

def get_p_text(tag_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    p_tags = tag.findall('./x:p', ns)
    body = ""
    for p_tag in p_tags:
        body += "".join(p_tag.itertext()) + "\n"
    return cleanhtml(body)

def get_sections():
    pubdata = xml.findall('.//*x:pubdata', ns)
    sections = []
    for pd in pubdata:
        if 'type' in pd.attrib and pd.attrib['type'] == 'web':
            sections.append(pd.attrib['position.section'])
    return sections

def get_keywords():
    keywords = xml.findall('.//*x:keyword', ns)
    return [
        keyword.attrib['key']\
                .encode("ascii", errors="ignore")\
                .decode()\
                .replace('"', '')\
                .replace("\n", " ") 
        for keyword in keywords
    ]

def get_publication():
    byline = get_text('byline').replace("|", "\n")
    bylines = [bl.strip() for bl in byline.splitlines() if bl.strip() != ""]
    return bylines[-1] if len(bylines) > 1 else None

def get_author():
    first_name = get_text('name.given')
    last_name = get_text('name.family')
    if first_name is None or last_name is None: 
        return None
    return first_name + " " + last_name 

def get_tag_attr(tag_name, attr_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    if tag is None:
        return tag
    return tag.get(attr_name)

def get_data_from_article():
    return {
        'doc_id': get_tag_attr('doc-id', 'id-string'),
        'release_date': get_tag_attr('date.release', 'norm'),
        'classifier': get_tag_attr('classifier', 'value'),
        'location': get_tag_attr('location', 'location-code'),
        'headline': get_text('hedline'),
        'byline': get_text('byline'),
        'publication': get_publication(),
        'author': get_author(),
        'abstract': get_text('abstract'),
        'body': get_p_text('body.content'),
        'tagline': get_text('tagline'),
        'sections': get_sections(),
        'keywords': get_keywords()
    }


ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}
db = Database()

article_count = 0
all_sections = {}
all_keywords = {}

with open('articles.csv', 'w',  newline='') as articles_csvfile, \
     open('keywords.csv', 'w',  newline='') as keywords_csvfile, \
     open('sections.csv', 'w',  newline='') as sections_csvfile, \
     open('articles_keywords.csv', 'w',  newline='') as articles_keywords_csvfile, \
     open('articles_sections.csv', 'w',  newline='') as articles_sections_csvfile:

    article_writer = csv.DictWriter(articles_csvfile, fieldnames=[
        'id', 'filepath', 'doc_id', 'release_date', 'classifier',
        'location', 'headline', 'byline', 'publication', 'author',
        'abstract', 'body', 'tagline'
    ], delimiter='\t')
    keyword_writer = csv.writer(keywords_csvfile, delimiter='\t')
    section_writer = csv.writer(sections_csvfile, delimiter='\t')
    article_keyword_writer = csv.writer(articles_keywords_csvfile, delimiter='\t')
    article_section_writer = csv.writer(articles_sections_csvfile, delimiter='\t')

    article_writer.writeheader()

    for root, dirs, files in os.walk('.\\articles'):
        for f in files:
            path = os.path.join(root, f)
            print(path)

            xml = ET.parse(path).getroot()

            article = get_data_from_article()
            article_count += 1
            article['id'] = article_count
            article['filepath'] = path.replace('\\', '/')

            keywords = article['keywords']
            for keyword in keywords:
                if keyword not in all_keywords:
                    all_keywords[keyword] = len(all_keywords) + 1
                    keyword_writer.writerow([all_keywords[keyword], keyword])
                article_keyword_writer.writerow([article_count, all_keywords[keyword]])
            del article['keywords']
            
            sections = article['sections']
            for section in sections:
                if section not in all_sections:
                    all_sections[section] = len(all_sections) + 1
                    section_writer.writerow([all_sections[section], section])
                article_section_writer.writerow([article_count, all_sections[section]])
            del article['sections']

            article_writer.writerow(article)

print('Inserting sections', len(all_sections))
db.copy_from_file('sections', 'sections.csv', False)

print('Inserting keywords', len(all_keywords))
db.copy_from_file('keywords', 'keywords.csv', False)

print('Inserting articles', article_count)
db.copy_from_file('articles', 'articles.csv', True)

print('Inserting article-section associations')
db.copy_from_file('articles_sections', 'articles_sections.csv', False)

print('Inserting article-keyword associations')
db.copy_from_file('articles_keywords', 'articles_keywords.csv', False)
