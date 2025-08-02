import logging
import os
import json
import azure.functions as func
from azure.data.tables import TableClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError

# Constants
TABLE_NAME = 'ResumeVisits'
PARTITION_KEY = 'counter'
ROW_KEY = 'visits'
COSMOSDB_CONNECTION_STRING = os.getenv('COSMOSDB_CONNECTION_STRING')

HTTP_200 = 200
HTTP_500 = 500
MISSING_CONN_MSG = "Missing DB connection string."
ERROR_MSG = "Internal Server Error"

# Optional CORS headers
HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
}

app = func.FunctionApp()

def get_table_client():
    return TableClient.from_connection_string(
        conn_str=COSMOSDB_CONNECTION_STRING,
        table_name=TABLE_NAME
    )

@app.route(route="GetResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def GetResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing GET request to retrieve resume visit counter.')

    if not COSMOSDB_CONNECTION_STRING:
        logging.error("Missing DB connection string.")
        return func.HttpResponse(MISSING_CONN_MSG, status_code=HTTP_500)

    try:
        table_client = get_table_client()
        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            count = entity.get('Count', 0)
        except ResourceNotFoundError:
            logging.warning("Entity not found. Initializing counter to 0.")
            count = 0

        return func.HttpResponse(json.dumps({'count': count}), headers=HEADERS, status_code=HTTP_200)

    except Exception as e:
        logging.error(f"Error retrieving counter: {e}", exc_info=True)
        return func.HttpResponse(ERROR_MSG, status_code=HTTP_500)

@app.route(route="IncrementResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def IncrementResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing POST request to increment resume visit counter.')

    if not COSMOSDB_CONNECTION_STRING:
        logging.error("Missing DB connection string.")
        return func.HttpResponse(MISSING_CONN_MSG, status_code=HTTP_500)

    try:
        table_client = get_table_client()
        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            current_count = entity.get('Count', 0)
        except ResourceNotFoundError:
            logging.warning("Entity not found. Initializing counter to 0.")
            current_count = 0

        new_count = current_count + 1
        updated_entity = {
            'PartitionKey': PARTITION_KEY,
            'RowKey': ROW_KEY,
            'Count': new_count
        }

        table_client.upsert_entity(entity=updated_entity, mode=UpdateMode.REPLACE)

        return func.HttpResponse(json.dumps({'newCount': new_count}), headers=HEADERS, status_code=HTTP_200)

    except Exception as e:
        logging.error(f"Error incrementing counter: {e}", exc_info=True)
        return func.HttpResponse(ERROR_MSG, status_code=HTTP_500)
