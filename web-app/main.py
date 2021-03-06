# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import logging


# [START gae_python37_auth_verify_token]
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

from db import WebDatabase

logger = logging.getLogger('scope.name')

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

db = WebDatabase()

firebase_request_adapter = requests.Request()
# [END gae_python37_auth_verify_token]

datastore_client = datastore.Client()

app = Flask(__name__)

@app.before_request
def before_request():
    if request.endpoint == 'index' or request.endpoint == 'static':
        return

    # Verify Firebase auth.
    id_token = request.cookies.get("token")

    if not id_token:
        return jsonify({'error': "User not logged in"})

    try:
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, firebase_request_adapter)
        logger.info(claims['email'])
        # if claims['email'] not in allowed_emails:
        #     return jsonify({'error': "User not allowed"})
    except ValueError as exc:
        error_message = str(exc)
        return jsonify({'error': error_message})

#vv########################### Pages ################################

# [START gae_python37_auth_verify_token]
@app.route('/')
def index():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            error_message = str(exc)

    return render_template(
        'index.html',
        user_data=claims, error_message=error_message)
# [END gae_python37_auth_verify_token]

@app.route('/webfonts/<path:path>')
def send_webfonts(path):
    return send_from_directory('static/webfonts', path)

@app.route("/browse/", defaults={"page": 0, "length": 100})
@app.route("/browse/<int:page>/", defaults={"length": 100})
@app.route('/browse/<int:page>/<int:length>')
def browse(page, length):
    h = db.get_headlines(page, length)
    error_message = None
    return render_template(
        'article_locations.html',
        headlines=h, 
        error_message=error_message)

@app.route('/graph/')
def graph_entities():
    return render_template('graph_entities.html')

@app.route('/map/')
def map_entities():
    sections = db.get_sections()
    return render_template(
        'entities.html',
        sections=sections)

@app.route('/heat-map/')
def map_entities2():
    return render_template('map_entities.html')

@app.route('/map/<path:section>')
def map_section(section):
    section = [section]
    locations = db.get_locations_for_sections(section)
    return render_template(
        'entities.html',
        locations=locations)

@app.route('/postal-codes/', defaults={"city": "Norfolk"})
@app.route('/postal-codes/<string:city>/')
def map_postal_codes(city):
    key = os.environ['MAPBOX_KEY']
    return render_template(
        'map_postal_codes.html',
        city=city,
        mapbox_key=key)


############################ API endpoints by alpha ################################

# Returns all Locations for given array of Sections
@app.route('/api/locations', methods=['POST'])
def get_locations():
    sections = request.get_json(force=True)
    return jsonify(db.get_locations_for_sections(sections))

# Returns all Articles for given Location and array of Sections
@app.route('/api/location/<path:location>', methods=['POST'])
def get_articles_for_location(location): 
    sections = request.get_json(force=True)
    return jsonify(db.get_articles_for_entity(sections, location))

# Returns the Article with the given ID
@app.route('/api/article/<int:article_id>')
def get_article(article_id): 
    return jsonify(db.get_article(article_id))

# Returns Entities for the given combination of page and length, defaults are page=0&length=100
@app.route("/api/entities/", defaults={"page": 0, "length": 100})
@app.route("/api/entities/<int:page>", defaults={"length": 100})
@app.route('/api/entities/<int:page>/<int:length>')
def get_entities(page, length):
    entities = db.get_entities(page, length)
    return jsonify(entities)

# Returns Headlines for the given combination of page and length, defaults are page=0&length=100
@app.route("/api/headlines/", defaults={"page": 0, "length": 100})
@app.route("/api/headlines/<int:page>/", defaults={"length": 100})
@app.route('/api/headlines/<int:page>/<int:length>')
def get_headlines(page, length): 
    headlines = db.get_headlines(page, length)
    return jsonify(headlines)

# Returns the count of distinct Proper Locations and distinct Proper Organizations given the minimum salience, default salience=0.1
@app.route("/api/info/", defaults={"salience": 0.1})
@app.route("/api/info/<float:salience>")
def get_info(salience):
    info = db.get_info(salience)
    return jsonify(info)

# Returns the count of articles by postal code for the given city, default city=Norfolk
@app.route("/api/postal-codes/", defaults={"city": "Norfolk"})
@app.route("/api/postal-codes/<string:city>")
def get_count_of_articles_by_postal_code(city):
    data = db.get_count_of_articles_by_postal_code(city)
    return jsonify(data)

# Returns Proper Locations within a given city, default city=Norfolk
@app.route("/api/sub-city-locations/", defaults={"cities": "Norfolk"})
@app.route("/api/sub-city-locations/<path:cities>")
def get_locations_within_cities(cities):
    data = db.get_locations_within_cities(cities.split('/'))
    return jsonify(data)

# Returns Proper Locations having the given minimum salience, length Locations per page, defaults are salience=0.1&page=0&length=100
@app.route("/api/proper-locations/", defaults={"salience": 0.1, "page": 0, "length": 100})
@app.route("/api/proper-locations/<float:salience>", defaults={"page": 0, "length": 100})
@app.route("/api/proper-locations/<float:salience>/<int:page>/", defaults={"length": 100})
@app.route("/api/proper-locations/<float:salience>/<int:page>/<int:length>")
def get_proper_locations(salience, page, length):
    proper_locations = db.get_proper_locations(salience, page, length)
    return jsonify(proper_locations)

# Returns Proper Organizations having the given minimum salience, length Organizations per page, defaults are salience=0.1&page=0&length=100
@app.route("/api/proper-organizations/", defaults={"salience": 0.1, "page": 0, "length": 100})
@app.route("/api/proper-organizations/<float:salience>", defaults={"page": 0, "length": 100})
@app.route("/api/proper-organizations/<float:salience>/<int:page>/", defaults={"length": 100})
@app.route("/api/proper-organizations/<float:salience>/<int:page>/<int:length>")
def get_proper_organizations(salience, page, length):
    proper_organizations = db.get_proper_organizations(salience, page, length)
    return jsonify(proper_organizations)

# Returns an array of sections of the Publication
@app.route("/api/sections")
def get_sections():
    sections = db.get_sections()
    return jsonify(sections)

############################ MAIN ################################

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
