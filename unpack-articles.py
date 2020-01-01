# This script walks a directory of XML files looking for newspaper articles.
# Found articles are copied another directory.
import xml.etree.ElementTree as ET
import os
from shutil import copyfile

# Newspaper Terms of North America namespace
ns = {'x': 'http://iptc.org/std/NITF/2006-10-18/'}

# A collection of unprocessed files
bad_files = []

# Walk the directory looking for XML files
for root, dirs, files in os.walk('.\\xml'):
    # For each file, try to parse it into an Element tree
    # or throw an exception and add the file to bad_files
    for f in files:
        path = os.path.join(root, f)
        print(path)
        xml = None
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError:
            bad_files.append(path)
            continue
        # If we get an Element Tree, check the doc to see if it's an article.
        # If article, copy it into the articles directory.
        classifier = xml.find('.//*x:classifier', ns)
        if classifier.get('value') == 'article':
            dest = path.replace('.\\xml', '.\\articles')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            copyfile(path, dest)
        # Else, skip it, not an article, ex., ?

print("DONE!")
print("Bad files:")
for f in bad_files:
    print(f)
