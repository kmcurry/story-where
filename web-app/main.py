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
from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

from db import WebDatabase

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

db = WebDatabase()

firebase_request_adapter = requests.Request()
# [END gae_python37_auth_verify_token]

datastore_client = datastore.Client()

app = Flask(__name__)

allowed_emails = [
    'ben.schoenfeld@gmail.com',
    'kmcurry@gmail.com',
    'ericasmith13@gmail.com',
    'e.smith@pilotonline.com '
]

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
        if claims['email'] not in allowed_emails:
            return jsonify({'error': "User not allowed"})
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


@app.route('/map/')
def map_entities():
    sections = db.get_sections()
    return render_template(
        'entities.html',
        sections=sections)

@app.route('/postal-codes/', defaults={"city": "Norfolk"})
@app.route('/postal-codes/<string:city>/')
def map_postal_codes(city):
    key = 'pk.eyJ1Ijoia21jdXJyeSIsImEiOiJjanJlNXE2NzMweWk1M3lscHQ5dTJ6MmU3In0.GrB9Ngw2dm4HewnoFI5rKA' # os.environ['MAPBOX_KEY']
    print(key)
    return render_template(
        'postal_codes.html',
        city=city,
        mapbox_key=key)


#vv########################### API endpoints by alpha ################################

@app.route('/api/article/<int:article_id>')
def get_article(article_id): 
    return jsonify(db.get_article(article_id))

@app.route("/api/entities/", defaults={"page": 0, "length": 100})
@app.route("/api/entities/<int:page>", defaults={"length": 100})
@app.route('/api/entities/<int:page>/<int:length>')
def get_entities(page, length):
    entities = db.get_entities(page, length)
    return jsonify(entities)

@app.route("/api/headlines/", defaults={"page": 0, "length": 100})
@app.route("/api/headlines/<int:page>/", defaults={"length": 100})
@app.route('/api/headlines/<int:page>/<int:length>')
def get_headlines(page, length): 
    headlines = db.get_headlines(page, length)
    return jsonify(headlines)

@app.route("/api/info/", defaults={"salience": 0.1})
@app.route("/api/info/<float:salience>")
def get_info(salience):
    info = db.get_info(salience)
    return jsonify(info)

@app.route("/api/postal-codes/", defaults={"city": "Norfolk"})
@app.route("/api/postal-codes/<string:city>")
def get_count_of_articles_by_postal_code(city):
    data = db.get_count_of_articles_by_postal_code(city)
    return jsonify(data)

@app.route("/api/sub-city-locations/", defaults={"cities": "Norfolk"})
@app.route("/api/sub-city-locations/<path:cities>")
def get_locations_within_cities(cities):
    data = db.get_locations_within_cities(cities.split('/'))
    return jsonify(data)

@app.route("/api/proper-locations/", defaults={"salience": 0.1, "page": 0, "length": 100})
@app.route("/api/proper-locations/<float:salience>", defaults={"page": 0, "length": 100})
@app.route("/api/proper-locations/<float:salience>/<int:page>/", defaults={"length": 100})
@app.route("/api/proper-locations/<float:salience>/<int:page>/<int:length>")
def get_proper_locations(salience, page, length):
    proper_locations = db.get_proper_locations(salience, page, length)
    return jsonify(proper_locations)

@app.route("/api/proper-organizations/", defaults={"salience": 0.1, "page": 0, "length": 100})
@app.route("/api/proper-organizations/<float:salience>", defaults={"page": 0, "length": 100})
@app.route("/api/proper-organizations/<float:salience>/<int:page>/", defaults={"length": 100})
@app.route("/api/proper-organizations/<float:salience>/<int:page>/<int:length>")
def get_proper_organizations(salience, page, length):
    proper_organizations = db.get_proper_organizations(salience, page, length)
    return jsonify(proper_organizations)

@app.route("/api/sections")
def get_sections():
    sections = db.get_sections()
    return jsonify(sections)

#vv########################### MAIN ################################

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
