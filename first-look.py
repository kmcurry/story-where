import csv
import xml.etree.ElementTree as ET
import os
from shutil import copyfile

ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}

area = [
    'hampton roads',
    'north carolina',
    'peninsula',
    'hatteras',
    'florida'
]


cities = [
    'virginia beach',
    'norfolk',
    'chesapeake',
    'chesaepake',
    'portsmouth',
    'suffolk',
    'outer banks',
    'newport news',
    'williamsburg',
    'hampton',
    'elizabeth city',
    'charlottesville',
    'richmond',
    'corolla'
]

schools = [
    'old dominion university',
    'odu football',
    'old dominion football',
    'odu monarchs',
    'odu basketball',
    'odu athletics',
    'virginia tech football',
    'cavaliers',
    'uva football',
    'virginia tech',
    'spartans',
    'norfolk state football',
    'tidewater community college',
    'norfolk state university',
    'nsu basketball',
    'norfolk state'
]

locale = [
    'oceanfront',
    'western branch',
    'norfolk tides',
    'norfolk admirals',
    'naval station norfolk',
    'great bridge',
    'ocean lakes',
    'harbor park',
    'town center',
    'ocean view',
    'cox',
    'something in the water',
    'lake taylor',
    'indian river',
    'south norfolk',
    'ghent',
    'deep creek',
    'maury',
    'macarthur center',
    'norfolk botanical garden',
    'nansemond river',
    'norfolk international airport',
    'hampton roads regional jail',
    'princess anne',
    'greenbrier',
    'scope',
    'sentara norfolk general hospital',
    'first colonial',
    'university of virginia',
    'eastern virginia medical school',
    'downtown norfolk',
    'william & mary',
    'cavalier hotel',
    'hickory',
    'chrysler hall',
    'norfolk academy'
]

stories = 0
with_location = 0
with_keylist = 0
with_section = 0
keywords_count = {}
sections_count = {}
sections_no_keywords_count = {}

stories_with_wide_location = 0
stories_with_gen_location = 0
stories_with_spec_location = 0

for root, dirs, files in os.walk('.\\articles'):
    for f in files:
        path = os.path.join(root, f)
        xml = ET.parse(path).getroot()
        location = xml.find('.//*x:location', ns)
        keylist = xml.find('.//*x:key-list', ns)
        stories += 1
        if location is not None: with_location += 1
        if keylist is not None: with_keylist += 1

        wide = False
        gen = False
        spec = False

        keywords = xml.findall('.//*x:keyword', ns)
        for keyword in keywords:
            key = keyword.attrib['key'].encode("ascii", errors="ignore").decode()
            if key not in keywords_count:
                keywords_count[key] = 0
            keywords_count[key] += 1

            if key in area:
                wide = True
            if key in cities:
                gen = True
            if key in schools or key in locale:
                spec = True
        
        if spec:
            stories_with_spec_location += 1
        elif gen:
            stories_with_gen_location += 1
        elif wide:
            stories_with_wide_location += 1

        has_section = False
        pubdata = xml.findall('.//*x:pubdata', ns)
        for pd in pubdata:
            if 'type' in pd.attrib and pd.attrib['type'] == 'web':
                has_section = True
                section = pd.attrib['position.section']
                if section == 'print_only/tabs_your_town_calendar': print(path)
                if section not in sections_count:
                    sections_count[section] = 0
                sections_count[section] += 1

                if keywords is None or len(keywords) == 0:
                    if section not in sections_no_keywords_count:
                        sections_no_keywords_count[section] = 0
                    sections_no_keywords_count[section] += 1
        if has_section:
            with_section += 1



print("DONE!")
print(stories)
print("With location", (1.0* with_location) / stories * 100)
print("With keylist", (1.0* with_keylist) / stories * 100)
print("With section", (1.0* with_section) / stories * 100)

print("Wide", stories_with_wide_location)
print("Gen", stories_with_gen_location)
print("Specific", stories_with_spec_location)

with open('keywords.csv', 'w') as f:
    for key in keywords_count.keys():
        f.write("%s,%s\n"%(key,keywords_count[key]))

with open('sections.csv', 'w') as f:
    for key in sections_count.keys():
        f.write("%s,%s\n"%(key,sections_count[key]))

with open('sections_no_keywords.csv', 'w') as f:
    for key in sections_no_keywords_count.keys():
        f.write("%s,%s\n"%(key,sections_no_keywords_count[key]))

