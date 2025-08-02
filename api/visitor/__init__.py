import logging
import os
import json
import azure.functions as func
from azure.data.tables import TableClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError

TABLE_NAME = 'ResumeVisits'
PARTITION_KEY = 'counter'
ROW_KEY = 'visits'
COSMOSDB_CONNECTION_STRING = os.getenv('COSMOSDB_CONNECTION_STRING')

app = func.FunctionApp()

@app.route(route="GetResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def GetResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing GET request to retrieve resume visit counter.')

    if not COSMOSDB_CONNECTION_STRING:
        return func.HttpResponse("Missing DB connection string.", status_code=500)

    try:
        table_client = TableClient.from_connection_string(
            conn_str=COSMOSDB_CONNECTION_STRING,
            table_name=TABLE_NAME
        )
        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            count = entity.get('Count', 0)
        except ResourceNotFoundError:
            count = 0

        return func.HttpResponse(json.dumps({'count': count}), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.route(route="IncrementResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def IncrementResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing POST request to increment resume visit counter.')

    if not COSMOSDB_CONNECTION_STRING:
        return func.HttpResponse("Missing DB connection string.", status_code=500)

    try:
        table_client = TableClient.from_connection_string(
            conn_str=COSMOSDB_CONNECTION_STRING,
            table_name=TABLE_NAME
        )
        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            current_count = entity.get('Count', 0)
        except ResourceNotFoundError:
            current_count = 0

        new_count = current_count + 1
        updated_entity = {
            'PartitionKey': PARTITION_KEY,
            'RowKey': ROW_KEY,
            'Count': new_count
        }

        table_client.upsert_entity(entity=updated_entity, mode=UpdateMode.REPLACE)

        return func.HttpResponse(json.dumps({'newCount': new_count}), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error", status_code=500)