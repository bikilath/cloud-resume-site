const { TableClient, TablesSharedKeyCredential } = require("@azure/data-tables");

module.exports = async function (context, req) {
  const account = process.env["AZURE_STORAGE_ACCOUNT"];
  const accountKey = process.env["AZURE_STORAGE_KEY"];
  const tableName = "Visitors";

  const credential = new TablesSharedKeyCredential(account, accountKey);
  const client = new TableClient(`https://${account}.table.core.windows.net`, tableName, credential);

  const partitionKey = "counter";
  const rowKey = "visitors";

  let entity;
  try {
    entity = await client.getEntity(partitionKey, rowKey);
    entity.count++;
    await client.updateEntity(entity, "Merge");
  } catch (error) {
    entity = { partitionKey, rowKey, count: 1 };
    await client.createEntity(entity);
  }

  context.res = {
    headers: { "Content-Type": "application/json" },
    body: { visitors: entity.count }
  };
};
