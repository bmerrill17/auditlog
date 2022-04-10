from flask import Flask, request, jsonify
import datetime as dt
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd
import cons
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
import snowflake_connection
import helpers

class AllLogs(Resource):
    def __init__(self):
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key):
        """returns only standard (invariant) data for all logs"""
        helpers.check_api_key(api_key)
        self.SnowflakeConnector.open_connection()
        self.SnowflakeConnector.pull_table('LOG', 'LOGS')
        self.SnowflakeConnector.close_connection()
        data = self.SnowflakeConnector['LOGS'].to_dict()
        return {'data': data}, 200

    def post(self, api_key):
        """posts new event to database and returns dictionary contains new event"""
        helpers.check_api_key(api_key)
        self.SnowflakeConnector.open_connection()

        # "date" field is populated using datetime.now().date() instead of date.today() so as to avoid timezone confusion
        new_data = {"date": str(dt.datetime.now(dt.timezone.utc).date()),
                    "time": str(dt.datetime.now(dt.timezone.utc).time()),
                    "event_id": self.SnowflakeConnector.check_max_id('LOGS') + 1}

        for key, value in request.args.items():
            new_data[key] = value

        required_fields = ["source", "event_type", "log_text"]
        for field in required_fields:
            if field not in new_data.keys():
                abort(400, message="required field: {} is missing".format(field))

        new_data = pd.DataFrame([new_data])
        invar_data = new_data[["event_id", "date", "time"] + required_fields]
        self.SnowflakeConnector.push_table(invar_data, 'LOG', 'LOGS')

        # only creates/adds to a event_type-specific variant data table if the posted event has 1+ non-standard fields
        if len(new_data.columns.tolist()) > len(["event_id", "date", "time"] + required_fields):
            var_data = new_data[["event_id"] + [col for col in new_data.columns.tolist() if col not in invar_data.columns.tolist()]]
            self.SnowflakeConnector.push_table(var_data, 'LOG', invar_data["event_type"][0])

        self.SnowflakeConnector.close_connection()
        new_data = new_data.to_dict()
        return {'added log': new_data}, 200

class Log(Resource):
    def __init__(self):
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key, event_id):
        """returns all data for log specified by event_id"""
        helpers.check_api_key(api_key)
        self.SnowflakeConnector.open_connection()
        data = self.SnowflakeConnector.pull_records(invar_conditions={"EVENT_ID": event_id})
        self.SnowflakeConnector.close_connection()
        data = data.to_dict()
        return {'data': data}, 200

class QueryLogs(Resource):
    def __init__(self):
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key):
        """returns all data for logs that meet query conditions"""
        helpers.check_api_key(api_key)
        self.SnowflakeConnector.open_connection()
        for key, value in request.args.items():
            if key.upper() not in self.SnowflakeConnector.pull_columns():
                abort(404, message="parameter: {} doesn't exist".format(key))
        invar_fields = ["event_id", "date", "time", "source", "event_type", "log_text"]
        invar_cols = [col for col in request.args.keys() if col in invar_fields]
        var_cols = [col for col in request.args.keys() if col not in invar_fields]
        invar_args = {key.upper(): request.args.get(key) for key in invar_cols}
        var_args = {key.upper(): request.args.get(key) for key in var_cols}
        data = self.SnowflakeConnector.pull_records(invar_conditions=invar_args, var_conditions=var_args)
        self.SnowflakeConnector.close_connection()
        data = data.to_dict()
        return {'data': data}, 200