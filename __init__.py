import logging
import azure.functions as func
import os
import json
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity

# Read Cosmos DB Table API connection string from environment variables
connection_string = os.getenv('COSMOS_TABLE_CONNECTION_STRING')

table_service = TableService(connection_string=connection_string)
table_name = 'VisitorCount'
partition_key = 'visitor'
row_key = 'count'

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Received a request.')

    try:
        if req.method == 'GET':
            entity = table_service.get_entity(table_name, partition_key, row_key)
            count = entity.get('Count', 0)
            return func.HttpResponse(json.dumps({'count': count}), status_code=200)

        elif req.method == 'POST':
            entity = table_service.get_entity(table_name, partition_key, row_key)
            count = entity.get('Count', 0) + 1
            entity['Count'] = count
            table_service.update_entity(table_name, entity)
            return func.HttpResponse(json.dumps({'count': count}), status_code=200)

        else:
            return func.HttpResponse("Method not allowed", status_code=405)

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
