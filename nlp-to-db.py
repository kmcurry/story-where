import csv
import json
import os
from utils.db import Database

db = Database()

articles = db.get_article_doc_ids()
article_ids_by_doc_id = {}
for article in articles:
    article_ids_by_doc_id[article.doc_id] = article.id

entity_count = 0

# Open csv files which reflect database tables
with open('nlentities.csv', 'w',  newline='') as nlentities_csvfile:
    nlentity_writer = csv.writer(nlentities_csvfile, delimiter='\t')

    # Walk through articles directory
    for root, dirs, files in os.walk('.\\nlp_results'):
        for f in files:
            path = os.path.join(root, f)
            print(path)

            with open(path, 'r') as entities_file:
                nlp_response = json.load(entities_file)
                entities = nlp_response['entities']
                for entity in entities:
                    entity_count += 1

                    wiki = None
                    if 'metadata' in entity and 'wikipedia_url' in entity['metadata']:
                        wiki = entity['metadata']['wikipedia_url'].encode("ascii", errors="ignore").decode()
                    
                    salience = 0
                    if 'salience' in entity:
                        salience = entity['salience']
                    
                    mention_types = []
                    if 'mentions' in entity:
                        for mention in entity['mentions']:
                            if 'type' in mention:
                                mention_types.append(mention['type'])

                    doc_id = f.replace(".json", "")

                    nlentity_writer.writerow([
                        entity_count,
                        entity['name'],
                        entity['type'],
                        wiki,
                        salience,
                        any([mt == 'PROPER' for mt in mention_types]),
                        article_ids_by_doc_id[doc_id]
                    ])

db.clear_nl_entities()


print('Inserting NL Entities')
db.copy_from_file('nlentities', 'nlentities.csv', False)
