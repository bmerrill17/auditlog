from flask import Flask, request, jsonify
import datetime as dt
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd
import cons
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
import snowflake_connection
import endpoints

if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)
    api.add_resource(endpoints.Log, '/logs/<string:api_key>/<int:event_id>')
    api.add_resource(endpoints.AllLogs, '/logs/<string:api_key>')
    api.add_resource(endpoints.QueryLogs, '/logs/<string:api_key>/query')
    app.run()
