from flask import request
import datetime as dt
from flask_restful import Resource, abort
import pandas as pd
import snowflake_connection
import helpers

class AllLogs(Resource):
    """Endpoint for API actions that affect all logs: get all logs and post new log"""
    def __init__(self):
        """Defines the connection to Snowflake (but does not open it)"""
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key):
        """Returns only standard (invariant) data for all logs"""
        helpers.check_api_key(api_key)

        self.SnowflakeConnector.open_connection()
        self.SnowflakeConnector.pull_table('LOG', 'LOGS')
        self.SnowflakeConnector.close_connection()

        data = self.SnowflakeConnector['LOGS'].to_dict()
        return {'data': data}, 200

    def post(self, api_key):
        """Posts new event to database and returns dictionary contains new event"""
        helpers.check_api_key(api_key)
        self.SnowflakeConnector.open_connection()

        # "date" field is populated using datetime.now().date() instead of date.today() so as to avoid timezone confusion
        new_data = {"date": str(dt.datetime.now(dt.timezone.utc).date()),
                    "time": str(dt.datetime.now(dt.timezone.utc).time()),
                    "event_id": self.SnowflakeConnector.check_max_id('LOGS') + 1}

        for key, value in request.args.items():
            new_data[key] = value

        # checks to make sure all required fields are provided in the POST request
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
    """Endpoint for API actions that concern only one specific log: get log details by event_id"""
    def __init__(self):
        """Defines the connection to Snowflake (but does not open it)"""
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key, event_id):
        """Returns all data for log specified by event_id"""
        helpers.check_api_key(api_key)

        self.SnowflakeConnector.open_connection()
        data = self.SnowflakeConnector.pull_records(invar_conditions={"EVENT_ID": event_id})
        self.SnowflakeConnector.close_connection()

        data = data.to_dict()
        return {'data': data}, 200

class QueryLogs(Resource):
    """Endpoint for querying the API in order to access one or more logs (with details)"""
    def __init__(self):
        """Defines the connection to Snowflake (but does not open it)"""
        self.SnowflakeConnector = snowflake_connection.SnowflakeConnector()

    def get(self, api_key):
        """Returns all data for logs that meet query conditions or blank dictionary if no logs meet conditions"""
        helpers.check_api_key(api_key)

        # opens and closes a Snowflake connection to pull existing columns to avoid leaving hanging connection in case of abort
        self.SnowflakeConnector.open_connection()
        existent_cols = self.SnowflakeConnector.pull_columns()
        self.SnowflakeConnector.close_connection()
        # checks to make sure all parameters in the query exist somewhere in the log data
        for key, value in request.args.items():
            if key.upper() not in existent_cols:
                abort(404, message="parameter: {} doesn't exist".format(key))

        # seperates the invariant and variant arguments from the fields/values passed as parameters
        invar_fields = ["event_id", "date", "time", "source", "event_type", "log_text"]
        invar_cols = [col for col in request.args.keys() if col in invar_fields]
        var_cols = [col for col in request.args.keys() if col not in invar_fields]
        invar_args = {key.upper(): request.args.get(key) for key in invar_cols}
        var_args = {key.upper(): request.args.get(key) for key in var_cols}

        # checks to make sure a leat one parameter/value pair was passed
        if not (invar_args or var_args):
            abort(400, message="No parameters passed to query, please use AllLogs endpoint instead at: /logs")

        self.SnowflakeConnector.open_connection()
        data = self.SnowflakeConnector.pull_records(invar_conditions=invar_args, var_conditions=var_args)
        self.SnowflakeConnector.close_connection()

        data = data.to_dict()
        return {'data': data}, 200
