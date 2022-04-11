import pandas as pd
import sqlalchemy
from snowflake.sqlalchemy import URL


class SnowflakeConnector:
    """
    A class used to establish and govern connection between the API endpoints and the database (hosted in Snowflake)

    ...

    Attributes
    ----------
    loaded_tables : dictionary
        a dictionary of full Snowflake tables downloaded and stored in memory
    engine : None or SQLAlchemy engine
        stores the SQLALchemy engine (when open) set-up with credentials
    connection : None or SQLAlchemy connection
        stores the SQLALchemy connection based on the engine (when open)
    """
    def __init__(self):
        """Initializes the class with empty/None attributes"""
        self.loaded_tables = {}
        self.engine = None
        self.connection = None

    def open_connection(self):
        """Populates the engine and connection attributes with live SQLAlchemy objects based on credentials"""
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
        """Safely disposes of the live engine and connection attributes"""
        self.connection.close()
        self.engine.dispose()

    def pull_table(self, schema, table):
        """Pulls a full table from Snowflake and stores it in the loaded_tables attributes"""
        self.loaded_tables[table] = pd.read_sql('SELECT * FROM AUDITLOG.{}.{}'.format(schema, table), self.connection)

    def push_table(self, df, schema, table):
        """Creates a table in the Snowflake database based on a passed DataFrame or appends if the table already exists"""
        df.to_sql(table, self.connection, schema=schema, if_exists='append', index=False)

    def check_max_id(self, table):
        """Returns the max value of the event_id column in a passed table name in the Snowflake database"""
        if self.check_table_exists(table):
            return pd.read_sql('SELECT "EVENT_ID" FROM AUDITLOG.LOG.{}'.format(table), self.connection)['event_id'].max()
        else:
            return 0

    def check_table_exists(self, table):
        """Returns a Boolean based on whether a passed table name exists in the Snowflake database"""
        table_names = pd.read_sql('SELECT "TABLE_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.TABLES', self.connection)['table_name'].tolist()
        if table in table_names:
            return True
        else:
            return False

    def pull_columns(self, table=None):
        """Returns a list of columns present in the Snowflake database or in a specified table if a table name is passed"""
        if table:
            return pd.read_sql('SELECT "COLUMN_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.COLUMNS WHERE "TABLE_NAME" = \'{}\''.format(
                table), self.connection)['column_name'].tolist()
        else:
            return pd.read_sql('SELECT "COLUMN_NAME" FROM AUDITLOG.INFORMATION_SCHEMA.COLUMNS', self.connection)['column_name'].tolist()

    def pull_records(self, invar_conditions=None, var_conditions=None):
        """Returns a Dataframe of log details that satisfy query conditions from Snowflake database"""
        # if the query imposes conditions on the invariant fields, filter selection from invariant data table (LOGS)
        # and use event_id to merge any relevant variant field data onto selection, otherwise pull all invariant data
        if invar_conditions:
            data = pd.read_sql('SELECT * FROM AUDITLOG.LOG.LOGS WHERE ' + ''.join(
                '"%s" = \'%s\' AND ' % pair for pair in invar_conditions.items())[:-4], self.connection)
            for event_type in set(data["event_type"].values):
                if self.check_table_exists(event_type):
                    var_data = pd.read_sql('SELECT * FROM AUDITLOG.LOG."{}" WHERE '.format(event_type) + '"EVENT_ID" IN (' + ''.join(
                            '\'%s\',' % event_id for event_id in data["event_id"].values.tolist())[:-1] + ')', self.connection)

                    # first, left-merge the variant data with the selected event_ids to filter out unselected data, then
                    # use concat and group-by event_id to ensure that only nans are overwritten in the case of multiple
                    # event_type-specific tables having same-named columns
                    var_data = pd.merge(data[["event_id"]], var_data, how='left', on=["event_id"])
                    data = pd.concat((data, var_data), sort=False).groupby("event_id").first().reset_index()
        else:
            data = pd.read_sql('SELECT * FROM AUDITLOG.LOG.LOGS', self.connection)

        # if the query imposes conditions on any relevant (not already filtered-out) variant fields, filter selection
        # further by adding positively filtered event_id to var_selected_ids concat/groupby process as above to merge in variant fields
        # because of potentially additively-filtering in multiple steps of for-loop, actual filtration done after loop ends
        if var_conditions:
            invar_selected_ids = data["event_id"].values.tolist()
            var_selected_ids = []
            for event_type in set(data["event_type"].values):
                if event_type in sqlalchemy.inspect(self.engine).get_table_names():
                    relevant_conditions = {key: var_conditions[key] for key in [col for col in self.pull_columns(event_type) if col in var_conditions]}
                    if relevant_conditions:
                        var_data = pd.read_sql('SELECT * FROM AUDITLOG.LOG."{}" WHERE '.format(event_type) + ''.join(
                            '"%s" = \'%s\' AND ' % pair for pair in relevant_conditions.items())[:-4], self.connection)
                        # data = pd.merge(data, var_data[["event_id"]], how='right', on=["event_id"])
                        var_selected_ids += var_data["event_id"].values.tolist()
                        data = pd.concat((data, var_data), sort=False).groupby("event_id").first().reset_index()
                        print('after')
                        print(data)
            selected_ids = [col for col in var_selected_ids if col in invar_selected_ids]
            data = data[data["event_id"].isin(selected_ids)]
        return data

    def __getitem__(self, key):
        """Returns a Dataframe stored in the loaded_tables attribute when accessed by key"""
        return self.loaded_tables[key]
