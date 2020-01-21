# story-where
Given a corpus of news stories:

* How precisely can we identify geographic features in news stories?
  * place names
  * longitudes, latitudes
  * rural, suburban, urban
* Can we put identified geographic features into context?
* Where are stories located on maps?
* How are stories distributed by geographic features?
* Are there reasonable correlations between the geographies of news stories and other boundaries?
  * Census Tracts
  * Zip Codes
  * School Zones
  * Voting Districts

# Setup
This web application is built on Google Cloud with Postgres and Python 3.

We referenced the ["Writing a Basic Web Service of App Engine"](https://cloud.google.com/appengine/docs/standard/python3/building-app/writing-web-service) guide to get started.

See [web-app/requirements.txt](web-app/requirements.txt) for dependencies.

Mac users on Mojave may encounter an error with psycopg2, which is used by SQLAlchemy. The error can be resolved by running the following:
`sudo installer -pkg /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg -target /` [reference](https://github.com/python-pillow/Pillow/issues/3438#issuecomment-435169249)

## Keys
The following keys are required:
* server-ca.pem
* client-key.pem
* client-cert.pem

## Environment Variables
The following env vars are required:
* PG_USE_SSL
* PG_CONN_STR
* PG_CLIENT_KEY
* PG_CLIENT_CERT
* PG_SERVER_CA
* GOOGLE_APPLICATION_CREDENTIALS
