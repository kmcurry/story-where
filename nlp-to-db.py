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

convert = {
    "NORFOLK": "Norfolk",
    "PORTSMOUTH": "Portsmouth",
    "VIRGINIA BEACH": "Virginia Beach",
    "SUFFOLK": "Suffolk",
    "HAMPTON": "Hampton",
    "NEWPORT NEWS": "Newport News"
}

bad_files = []

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
                if 'entities' not in nlp_response:
                    bad_files.append(path)
                    continue

                doc_id = f.replace(".json", "")

                if doc_id not in article_ids_by_doc_id:
                    print('Skipping results because article was filtered')
                    continue

                entities = nlp_response['entities']
                for entity in entities:
                    if entity['type'] == 'NUMBER':
                        continue

                    entity_count += 1

                    name = entity['name']
                    if name in convert:
                        name = convert[name]
                        print("Converted", entity['name'], "to", name)

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

                    nlentity_writer.writerow([
                        entity_count,
                        name,
                        entity['type'],
                        wiki,
                        salience,
                        any([mt == 'PROPER' for mt in mention_types]),
                        article_ids_by_doc_id[doc_id]
                    ])

db.clear_nl_entities()


print("Inserting NL Entities", entity_count)
db.copy_from_file('f_nlentities', 'nlentities.csv', False)

print("Insert complete")
print("The following files could not be inserted because they were not formated correctly")
for f in bad_files:
    print(f)
