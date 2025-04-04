"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)

import deliveryweb.views
@app.teardown_appcontext
def teardown_db(exception):
    deliveryweb.views.close_db(exception)
   
