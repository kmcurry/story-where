import xml.etree.ElementTree as ET
import os
from shutil import copyfile

ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}

bad_files = []

for root, dirs, files in os.walk('.\\xml'):
    for f in files:
        path = os.path.join(root, f)
        print(path)
        xml = None
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError:
            bad_files.append(path)
            continue
        classifier = xml.find('.//*x:classifier', ns)
        if classifier.get('value') == 'article':
            dest = path.replace('.\\xml', '.\\articles')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            copyfile(path, dest)

print("DONE!")
print("Bad files:")
for f in bad_files:
    print(f)
