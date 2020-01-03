# TLA 2.a
# Extract text from DOM Paths and write to database

import os
import re
import xml.etree.ElementTree as ET
from pprint import pprint
from shutil import copyfile
from utils.db import Database

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
  cleantext = re.sub(cleanr, '', raw_html)
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
    return [keyword.attrib['key'].encode("ascii", errors="ignore").decode() for keyword in keywords]

def get_tag_attr(tag_name, attr_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    if tag is None:
        return tag
    return tag.get(attr_name)

def get_data_from_article():
    return {
        'docId': get_tag_attr('doc-id', 'id-string'),
        'releaseDate': get_tag_attr('date.release', 'norm'),
        'classifier': get_tag_attr('classifier', 'value'),
        'location': get_tag_attr('location', 'location-code'),
        'headline': get_text('hedline'),
        'byline': get_text('byline'),
        'publication': "",
        'author': "",
        'abstract': get_text('abstract'),
        'body': get_p_text('body.content'),
        'tagline': "",
        'sections': get_sections(),
        'keywords': get_keywords()
    }


ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}
db = Database()

for root, dirs, files in os.walk('.\\articles'):
    for f in files:
        path = os.path.join(root, f)
        xml = ET.parse(path).getroot()

        article = get_data_from_article()
        pprint(article)

        db.add_article(article)
