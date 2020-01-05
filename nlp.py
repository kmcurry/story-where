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

db = Database()
articles = db.get_articles_to_nlp(10)
for article in articles:
    print("=" * 10)
    nlp_text = clean_text(article.headline) + '. ' + clean_text(article.body)
    
    path = article.filepath.replace('/', '\\')
    outfile = path.replace(".\\articles", ".\\nlp_results")
    outfile = outfile.replace(".xml", ".json")
    print(outfile)

    if not os.path.exists(outfile):
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

    with open(outfile, 'r') as entities_file:
        nlp_response = json.load(entities_file)
        entities = nlp_response['entities']
        for entity in entities:
            print(entity)
