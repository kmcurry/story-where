from utils.db import Database
from datetime import datetime
import hashlib
import json
import os
import requests

url = 'https://maps.googleapis.com/maps/api/geocode/json'
api_key = os.environ['GOOGLE_MAPS_API_KEY']
params = {'key': api_key, 'address': 'Mountain View, CA'}

print("Downloading entities")
db = Database()
entities = db.get_entities_to_geocode()
print("Entities downloaded", len(entities))

for entity in entities:
    print(entity.name)
    h = hashlib.md5(bytes(entity.name, encoding='utf-8')).hexdigest()
    print(h)

    outfile = ".\\geocode_results\\" + h + ".json"
    print(outfile)

    if os.path.exists(outfile):
        print("Skipping because Geocode results already exist")
        continue

    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))

    params['address'] = entity.name
    r = requests.get(url, params=params)
    results = r.json()
    results['address'] = entity.name
    results['collected_utc_date'] = str(datetime.utcnow())

    with open(outfile, 'w') as f:
        json.dump(results, f)

