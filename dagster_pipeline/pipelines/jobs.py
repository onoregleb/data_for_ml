from dagster import Definitions, define_asset_job, AssetSelection
from .assets import getmatch_data, hh_data, cleaned_data, merged_data, processed_data
from dagster_pipeline.pipelines.resources import sqlite_resource

assets = [
    getmatch_data,
    hh_data,
    cleaned_data,
    merged_data,
    processed_data
]

data_pipeline = define_asset_job(
    name="data_pipeline",
    selection=AssetSelection.all(),
    description="Полный пайплайн обработки данных вакансий"
)

defs = Definitions(
    assets=assets,
    jobs=[data_pipeline],
    resources={"sqlite_resource": sqlite_resource}
)
