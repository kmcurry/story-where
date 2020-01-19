import csv
import json
import os
from utils.db import Database

db = Database()

# Open csv files which reflect database tables
with open('geo.csv', 'w',  newline='') as geo_csvfile:
    geo_writer = csv.writer(geo_csvfile, delimiter='\t')

    # Walk through articles directory
    for root, dirs, files in os.walk('.\\geocode_results'):
        for f in files:
            path = os.path.join(root, f)
            print(path)

            with open(path, 'r') as geo_file:
                geo_response = json.load(geo_file)
                if geo_response['status'] == 'ZERO_RESULTS':
                    continue

                print(geo_response['results'][0]['geometry'].keys())