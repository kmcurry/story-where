import json
import os
from utils.db import Database

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from google.protobuf.json_format import MessageToJson

# Instantiates a client
client = language.LanguageServiceClient()

def clean_text(text):
    return text.replace('|', ' ').replace('""', '"').strip()

long_files = [
    ".\\articles\\2018\\05\\2fcb91a4-5954-11e8-93fc-dbd091fa05a0.xml",
    ".\\articles\\2018\\05\\e8d253b4-5953-11e8-bd86-37fbf45ee952.xml",
    ".\\articles\\2018\\05\\5e8c2a1c-5954-11e8-a054-ef298f853f45.xml",
    ".\\articles\\2019\\04\\2e32fe28-67a3-11e9-a1ae-93ecaca7e528.xml",
    ".\\articles\\2018\\05\\422f671c-5954-11e8-a168-f34a636bf007.xml",
    ".\\articles\\2019\\04\\6cc4e540-67b0-11e9-8e27-57a6ee87a386.xml"
]

db = Database()
articles = db.get_articles_to_nlp(10)
for article in articles:
    print("=" * 10)
    nlp_text = clean_text(article.headline) + '. ' + clean_text(article.body)
    
    path = article.filepath.replace('/', '\\')
    print(path)
    if path in long_files:
        print("Skipping because article has too many characters")
        continue

    outfile = path.replace(".\\articles", ".\\nlp_results")
    outfile = outfile.replace(".xml", ".json")
    print(outfile)

    if os.path.exists(outfile):
        print("Skipping because NLP results already exist")
        continue

    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    print("Getting NL Results")

    document = types.Document(
        content=nlp_text,
        language='en',
        type=enums.Document.Type.PLAIN_TEXT)
    
    response = client.analyze_entities(
        document=document,
        encoding_type='UTF32')
    
    with open(outfile, 'w') as outfile:
        outfile.write(MessageToJson(response, preserving_proto_field_name=True))

print("Finished NLP")
print("The following long files were skipped")
for f in long_files:
    print(f)