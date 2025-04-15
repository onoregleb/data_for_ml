import sys
sys.path.append("C:/Users/Gleb Onore/Desktop/data_for_ml/dagster_pipeline")

from dagster import AssetExecutionContext, asset, AssetObservation, MetadataValue
from dagster_pipeline.scrappers.getmatch_parser import getmatch_scrape
from dagster_pipeline.scrappers.hh_parser import hh_scrape
from dagster_pipeline.processing.data_cleaning import merge_datasets, clean_data
from dagster_pipeline.processing.feature_engineering import engineer_features
from dagster_pipeline.processing.model import train_salary_model


@asset(required_resource_keys={"sqlite_resource"})
def getmatch_data(context: AssetExecutionContext):
    db = context.resources.sqlite_resource
    getmatch_scrape(db)
    return None


@asset(required_resource_keys={"sqlite_resource"})
def hh_data(context: AssetExecutionContext):
    db = context.resources.sqlite_resource
    hh_scrape(db)
    return None


@asset(required_resource_keys={"sqlite_resource"})
def merged_data(context: AssetExecutionContext, getmatch_data, hh_data):
    db = context.resources.sqlite_resource
    return merge_datasets(db)


@asset(required_resource_keys={"sqlite_resource"})
def cleaned_data(context: AssetExecutionContext, merged_data):
    db = context.resources.sqlite_resource
    return clean_data(db)


@asset(required_resource_keys={"sqlite_resource"})
def processed_data(context: AssetExecutionContext, cleaned_data):
    db = context.resources.sqlite_resource
    return engineer_features(db)



@asset(required_resource_keys={"sqlite_resource"})
def train_model(context: AssetExecutionContext, processed_data):
    db = context.resources.sqlite_resource
    features_df = db.read_sql("SELECT * FROM features_for_model")

    model, metrics = train_salary_model(features_df)

    for key, value in metrics.items():
        context.log_event(
            AssetObservation(
                asset_key="train_model",
                metadata={key: MetadataValue.float(float(value))}  # Используем обертку
            )
        )

    return model


__all_assets__ = [
    getmatch_data,
    hh_data,
    merged_data,
    cleaned_data,
    processed_data,
    train_model
]
