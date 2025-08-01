import logging
import json
import os
import azure.functions as func
from azure.data.tables import TableClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError # Import for better error handling

# Read Cosmos DB Table API connection string from environment variables
# It's good practice to use a more specific name like COSMOSDB_CONNECTION_STRING
COSMOSDB_CONNECTION_STRING = os.environ.get('COSMOSDB_CONNECTION_STRING')
TABLE_NAME = 'ResumeVisits' # Changed to match previous recommendation
PARTITION_KEY = 'counter' # Consistent partition key for the single counter
ROW_KEY = 'visits' # Consistent row key for the single counter

# Initialize the Function App instance
app = func.FunctionApp()

@app.route(route="GetResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def GetResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to get counter.')

    if not COSMOSDB_CONNECTION_STRING:
        logging.error("COSMOSDB_CONNECTION_STRING environment variable is not set.")
        return func.HttpResponse("Internal Server Error: Database connection string missing.", status_code=500)

    try:
        table_client = TableClient.from_connection_string(
            conn_str=COSMOSDB_CONNECTION_STRING,
            table_name=TABLE_NAME
        )
        
        current_count = 0
        try:
            # Attempt to retrieve the entity
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            # Use .get() with a default value to safely retrieve 'Count'
            current_count = entity.get('Count', 0) 
        except ResourceNotFoundError:
            # This exception is raised if the entity (or table) does not exist
            logging.info(f"Counter entity (PartitionKey: {PARTITION_KEY}, RowKey: {ROW_KEY}) not found. Assuming count is 0.")
            current_count = 0
        except Exception as e:
            # Catch other potential errors during retrieval
            logging.error(f"Error retrieving counter entity: {e}", exc_info=True)
            return func.HttpResponse("Error retrieving counter.", status_code=500)
            
        return func.HttpResponse(
            json.dumps({'count': current_count}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Failed to connect to Table Service or other general error: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error while accessing database.", status_code=500)

@app.route(route="IncrementResumeCounter", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def IncrementResumeCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to increment counter.')

    if not COSMOSDB_CONNECTION_STRING:
        logging.error("COSMOSDB_CONNECTION_STRING environment variable is not set.")
        return func.HttpResponse("Internal Server Error: Database connection string missing.", status_code=500)

    try:
        table_client = TableClient.from_connection_string(
            conn_str=COSMOSDB_CONNECTION_STRING,
            table_name=TABLE_NAME
        )
        
        current_count = 0
        try:
            entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
            current_count = entity.get('Count', 0)
        except ResourceNotFoundError:
            # If entity not found, it's the first visit, so start count at 0
            logging.info(f"Counter entity not found during increment. Initializing count to 0.")
            current_count = 0
        except Exception as e:
            # Catch other potential errors during retrieval
            logging.error(f"Error retrieving counter entity for increment: {e}", exc_info=True)
            return func.HttpResponse("Error processing increment request.", status_code=500)

        new_count = current_count + 1
        
        updated_entity = {
            'PartitionKey': PARTITION_KEY,
            'RowKey': ROW_KEY,
            'Count': new_count # Store the new count
        }
        
        # upsert_entity will insert if not found, or update if found.
        # UpdateMode.REPLACE means it will replace the entity with the new one.
        table_client.upsert_entity(entity=updated_entity, mode=UpdateMode.REPLACE)
        
        return func.HttpResponse(
            json.dumps({'newCount': new_count}), # Return the new count
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Failed to connect to Table Service or other general error during increment: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error while incrementing counter.", status_code=500)