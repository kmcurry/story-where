import csv
import json
import os
from utils.db import Database

db = Database()

location_count = 0
loc_component_count = 0
loc_type_count = 0

# Open csv files which reflect database tables
with open('locations.csv', 'w',  newline='') as loc_file, \
     open('loc_components.csv', 'w',  newline='') as loc_components_file, \
     open('loc_types.csv', 'w',  newline='') as loc_types_file:

    location_writer = csv.writer(loc_file, delimiter='\t')
    loc_components_writer = csv.writer(loc_components_file, delimiter='\t')
    loc_types_writer = csv.writer(loc_types_file, delimiter='\t')

    # Walk through articles directory
    for root, dirs, files in os.walk('.\\geocode_results'):
        for f in files:
            path = os.path.join(root, f)
            print(path)

            with open(path, 'r') as geo_file:
                geo_response = json.load(geo_file)

                location_count += 1

                if geo_response['status'] == 'ZERO_RESULTS':
                    location_writer.writerow([
                        location_count,
                        geo_response['address'],
                        None,
                        geo_response['collected_utc_date'],
                        None,
                        0, 0,
                        False,
                        0, 0, 0, 0
                    ])
                    continue

                geo_result = geo_response['results'][0]

                for component in geo_result['address_components']:
                    loc_component_count += 1
                    loc_components_writer.writerow([
                        loc_component_count,
                        component['long_name'],
                        component['types'][0],
                        location_count
                    ])

                for t in geo_result['types']:
                    loc_type_count += 1
                    loc_types_writer.writerow([
                        loc_type_count,
                        t,
                        location_count
                    ])

                has_bounds = 'bounds' in geo_result['geometry']

                location_writer.writerow([
                    location_count,
                    geo_response['address'],
                    geo_result['formatted_address'].encode("ascii", errors="ignore").decode(),
                    geo_response['collected_utc_date'],
                    geo_result['geometry']['location_type'],
                    geo_result['geometry']['location']['lat'],
                    geo_result['geometry']['location']['lng'],
                    has_bounds,
                    geo_result['geometry']['bounds']['northeast']['lat'] if has_bounds else 0,
                    geo_result['geometry']['bounds']['northeast']['lng'] if has_bounds else 0,
                    geo_result['geometry']['bounds']['southwest']['lat'] if has_bounds else 0,
                    geo_result['geometry']['bounds']['southwest']['lng'] if has_bounds else 0
                ])

print("Inserting Locations", location_count)
db.copy_from_file('locations', 'locations.csv', False)

print("Inserting Location Components", loc_component_count)
db.copy_from_file('location_components', 'loc_components.csv', False)

print("Inserting Location Types", loc_type_count)
db.copy_from_file('location_types', 'loc_types.csv', False)