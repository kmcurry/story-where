# TLA 2.a
# Create database tables
# Extract article text from DOM Paths
# Save article text to csv files structured to match db tables
# Use PG copy_from to upload data to tables
# copy_from runs many orders of magnitude faster than bulk insert

import csv
import os
import re
import xml.etree.ElementTree as ET
from pprint import pprint
from shutil import copyfile
from utils.db import Database

# Remove all HTML from text
# Also removes non-ascii characters and replaces new lines with pipes
# which is necessary for the copy_from to work because new lines and 
# non UTF8 characters break that process
# Returns a string
def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
  cleantext = re.sub(cleanr, '', raw_html.encode("ascii", errors="ignore").decode().replace("\n", "|"))
  return cleantext

# Get all text from named tag
# Cleans text
# Returns a string
def get_text(tag_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    return cleanhtml("".join(tag.itertext())) if tag is not None else None

# Get all text from p tags within named tag
# Cleans text
# Returns a string
def get_p_text(tag_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    p_tags = tag.findall('./x:p', ns)
    body = ""
    for p_tag in p_tags:
        body += "".join(p_tag.itertext()) + "\n"
    return cleanhtml(body)

# Get all web sections under pubdata tag
# Returns list of strings
def get_sections():
    pubdata = xml.findall('.//*x:pubdata', ns)
    sections = []
    for pd in pubdata:
        if 'type' in pd.attrib and pd.attrib['type'] == 'web':
            sections.append(pd.attrib['position.section'])
    return sections

# Get all keywords (key attribute of keyword tag)
# Removes non-ascii characters, new lines, and double quotes
# which is necessary for the copy_from to work because new lines and 
# non UTF8 characters break that process
# Returns list of keywords
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

# Gets publication
# This is a guess as it just takes the last line of the byline
# Returns a string
def get_publication():
    byline = get_text('byline').replace("|", "\n")
    bylines = [bl.strip() for bl in byline.splitlines() if bl.strip() != ""]
    return bylines[-1] if len(bylines) > 1 else None

# Gets author text
# Text of name.given and name.famliy tag
# Returns a string
def get_author():
    first_name = get_text('name.given')
    last_name = get_text('name.family')
    if first_name is None or last_name is None: 
        return None
    return first_name + " " + last_name 

# Get named attribute from named tag
# Returns a string
def get_tag_attr(tag_name, attr_name):
    tag = xml.find('.//*x:' + tag_name, ns)
    if tag is None:
        return tag
    return tag.get(attr_name)

# Get all data from article
# Returns dict of data
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

###
#   Begin article to database process
###

# Setup xml namespace
ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}

# Setup database
# Schema will be created
db = Database()

article_count = 0
all_sections = {}
all_keywords = {}

# Get list of content sections to filter for
# If an article is listed in one of these sections it will NOT be included in the database
filtered_sections = []
with open('filtered_sections.csv') as filtered_sections_file:
    for l in filtered_sections_file.readlines():
        section = l.rstrip()
        if section is not "":
            filtered_sections.append(section)

# Open csv files which reflect database tables
with open('articles.csv', 'w',  newline='') as articles_csvfile, \
     open('keywords.csv', 'w',  newline='') as keywords_csvfile, \
     open('sections.csv', 'w',  newline='') as sections_csvfile, \
     open('articles_keywords.csv', 'w',  newline='') as articles_keywords_csvfile, \
     open('articles_sections.csv', 'w',  newline='') as articles_sections_csvfile:

    # Create CSV writes for files
    # The article writer is a dict writer, so we have to specify the fieldnames
    article_writer = csv.DictWriter(articles_csvfile, fieldnames=[
        'id', 'filepath', 'doc_id', 'release_date', 'classifier',
        'location', 'headline', 'byline', 'publication', 'author',
        'abstract', 'body', 'tagline'
    ], delimiter='\t')
    article_writer.writeheader()

    # The other writers are simpiler, two column files so we don't need dict writers
    keyword_writer = csv.writer(keywords_csvfile, delimiter='\t')
    section_writer = csv.writer(sections_csvfile, delimiter='\t')
    article_keyword_writer = csv.writer(articles_keywords_csvfile, delimiter='\t')
    article_section_writer = csv.writer(articles_sections_csvfile, delimiter='\t')

    # Walk through articles directory
    for root, dirs, files in os.walk('.\\articles'):
        for f in files:
            path = os.path.join(root, f)
            print(path)

            # Parse the xml and get the data we need
            xml = ET.parse(path).getroot()
            article = get_data_from_article()
            
            if any([s in filtered_sections for s in article['sections']]):
                print('Article is in a filtered section and will not be included')
                continue

            article_count += 1
            article['id'] = article_count # this is the primary key for the article table
            article['filepath'] = path.replace('\\', '/') # backslashes break the copy_file

            # The keywords and sections both have separate tables and have a many-to-many
            # relationshop with the articles table. For each keyword / section in the
            # article, write it to the respective file if it's not already in there
            # then write it to the association table file

            # Keywords file and associations file
            keywords = article['keywords']
            for keyword in keywords:
                if keyword not in all_keywords:
                    all_keywords[keyword] = len(all_keywords) + 1
                    keyword_writer.writerow([all_keywords[keyword], keyword])
                article_keyword_writer.writerow([article_count, all_keywords[keyword]])
            del article['keywords']
            
            # Section file and associatons file
            sections = article['sections']
            for section in sections:
                if section not in all_sections:
                    all_sections[section] = len(all_sections) + 1
                    section_writer.writerow([all_sections[section], section])
                article_section_writer.writerow([article_count, all_sections[section]])
            del article['sections']

            # Write the article to the file
            article_writer.writerow(article)

# Call copy_from to upload data to each database

print('Inserting sections', len(all_sections))
db.copy_from_file('f_sections', 'sections.csv', False)

print('Inserting keywords', len(all_keywords))
db.copy_from_file('f_keywords', 'keywords.csv', False)

print('Inserting articles', article_count)
db.copy_from_file('f_articles', 'articles.csv', True)

print('Inserting article-section associations')
db.copy_from_file('f_articles_sections', 'articles_sections.csv', False)

print('Inserting article-keyword associations')
db.copy_from_file('f_articles_keywords', 'articles_keywords.csv', False)
