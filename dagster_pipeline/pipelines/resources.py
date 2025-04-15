from dagster import resource
from dagster_pipeline.database.sqlite_handler import SQLiteHandler

@resource
def sqlite_resource(_):
    return SQLiteHandler()