from dagster import Definitions
from dagster_pipeline.pipelines.jobs import data_pipeline
from dagster_pipeline.pipelines.resources import sqlite_resource
from pipelines import assets

defs = Definitions(
    assets=assets.__all_assets__,
    jobs=[data_pipeline],
    resources={"sqlite_resource": sqlite_resource}
)
