import sys
sys.path.append("C:/Users/Gleb Onore/Desktop/data_for_ml/dagster_pipeline")

from dagster import AssetExecutionContext, asset
from dagster_pipeline.scrappers.getmatch_parser import getmatch_scrape
from dagster_pipeline.scrappers.hh_parser import hh_scrape
from dagster_pipeline.processing.data_cleaning import merge_datasets, clean_data
from dagster_pipeline.processing.feature_engineering import engineer_features


@asset(required_resource_keys={"sqlite_resource"})
def getmatch_data(context: AssetExecutionContext):
    db = context.resources.sqlite_resource
    return getmatch_scrape(db)



@asset(required_resource_keys={"sqlite_resource"})
def hh_data(context: AssetExecutionContext):
    db = context.resources.sqlite_resource
    hh_scrape(db)


@asset
def merged_data(getmatch_data, hh_data):
    return merge_datasets(getmatch_data, hh_data)

@asset
def cleaned_data(merged_data):
    return clean_data(merged_data)

@asset(required_resource_keys={"sqlite_resource"})
def processed_data(context: AssetExecutionContext, cleaned_data):
    features_df = engineer_features(cleaned_data)
    db = context.resources.sqlite_resource
    db.save_dataframe(features_df, table_name="processed_data")  # пример
    return features_df

__all_assets__ = [
    getmatch_data,
    hh_data,
    merged_data,
    cleaned_data,
    processed_data
]
