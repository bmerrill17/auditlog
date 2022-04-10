from flask import Flask, request, jsonify
import datetime as dt
from flask_restful import Resource, Api, reqparse, abort
import pandas as pd
import cons
import sqlalchemy
from snowflake.sqlalchemy import URL

class SnowflakeConnector:
    def __init__(self):
        self.loaded_tables = {}
        self.engine = None
        self.connection = None

    def open_connection(self):
        self.engine = sqlalchemy.create_engine(URL(
            user='AUDITLOGGER',
            password='AuditPass123',
            account='OBA19334',
            database='AUDITLOG',
            role='AUDITLOGGER',
            warehouse='COMPUTE_WH'
        ))
        self.connection = self.engine.connect()

    def close_connection(self):
        self.connection.close()
        self.engine.dispose()

    def pull_table(self, schema, table):
        self.loaded_tables[table] = pd.read_sql('SELECT * FROM AUDITLOG.{}.{}'.format(schema, table), self.connection)

    def push_table(self, df, schema, table):
        df.to_sql(table, self.connection, schema=schema, if_exists='append', index=False)

    def check_max_id(self, table):
        if self.check_table_exists(table):
            print(pd.read_sql('SELECT "EVENT_ID" FROM AUDITLOG.LOG.{}'.format(table), self.connection)['event_id'].max())
            return pd.read_sql('SELECT "EVENT_ID" FROM AUDITLOG.LOG.{}'.format(table), self.connection)['event_id'].max()
        else:
            return 0

    def check_table_exists(self, table):
        table_names = pd.read_sql('SELECT "TABLE_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.TABLES', self.connection)['table_name'].tolist()
        print(table_names)
        if table in table_names:
            return True
        else:
            return False

    def pull_columns(self, table=None):
        if table:
            return pd.read_sql('SELECT "COLUMN_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.COLUMNS WHERE "TABLE_NAME" = \'{}\''.format(
                table), self.connection)['column_name'].tolist()
        else:
            return pd.read_sql('SELECT "COLUMN_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.COLUMNS', self.connection)['column_name'].tolist()

    def pull_records(self, invar_conditions=None, var_conditions=None):
        if invar_conditions:
            data = pd.read_sql('SELECT * FROM AUDITLOG.LOG.LOGS WHERE ' + ''.join(
                '"%s" = \'%s\' AND ' % pair for pair in invar_conditions.items())[:-4], self.connection)
            for event_type in set(data["event_type"].values):
                if self.check_table_exists(event_type):
                    var_data = pd.read_sql('SELECT * FROM AUDITLOG.LOG.LOGS WHERE ' + '"EVENT_ID" IN (' + ''.join(
                            '\'%s\',' % event_id for event_id in data["event_id"].values.tolist())[:-1] + ')', self.connection)
                    data = pd.merge(data, var_data[["event_id"]], how='inner', on=["event_id"])
        else:
            data = pd.read_sql('SELECT * FROM AUDITLOG.LOG.LOGS', self.connection)
        if var_conditions:
            for event_type in set(data["event_type"].values):
                if event_type in sqlalchemy.inspect(self.engine).get_table_names():
                    relevant_conditions = {key: var_conditions[key] for key in [col for col in self.pull_columns(event_type) if col in var_conditions]}
                    if relevant_conditions:
                        var_data = pd.read_sql('SELECT * FROM AUDITLOG.LOG."{}" WHERE '.format(event_type) + ''.join(
                            '"%s" = \'%s\' AND ' % pair for pair in relevant_conditions.items())[:-4], self.connection)
                        data = pd.merge(data, var_data, how='right', on=["event_id"])
        return data

    def __getitem__(self, key):
        return self.loaded_tables[key]