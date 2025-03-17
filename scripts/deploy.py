import os
from utils import *

capacity_name = "Trial-ruiromano-microsoft-com-05-24-2023-15-11-UTC"
workspace_name = "RR-SalesSense2"
semanticmodel_name = "SM_SalesSense"
report_name = "Sales Report"
connection_name = "RR - Git Sample files2"
source_url = "https://raw.githubusercontent.com/pbi-tools/sales-sample/refs/heads/data/RAW-Sales.csv"
semanticmodel_src_path = "src/SM_SalesSense.SemanticModel"

# Create workspace

run_fab_command(f"create /{workspace_name}.Workspace -P capacityName={capacity_name}", silently_continue=True)

# Create connection to the data files location

run_fab_command(f"create .connections/{connection_name}.Connection -P connectionDetails.type=HttpServer,connectionDetails.parameters.url={source_url},credentialDetails.type=Anonymous", silently_continue=True)

connection_id = run_fab_command(f"get .connections/{connection_name}.Connection -q id", capture_output=True)

# Import data pipeline

run_fab_command(f"import -f /{workspace_name}.workspace/DP_INGST_CopyCSV.datapipeline -i src/DP_INGST_CopyCSV.DataPipeline")

# TODO: How to bind to the connection created above? Can I do this in the import command and not after deploy?

# Create lakehouse

run_fab_command(f"create /{workspace_name}.workspace/LH_STORE_RAW.lakehouse")

lakehouse_id = run_fab_command(f"get /{workspace_name}.workspace/LH_STORE_RAW.lakehouse -q id", capture_output=True)

sql_endpoint = run_fab_command(f"get /{workspace_name}.workspace/LH_STORE_RAW.lakehouse -q properties.sqlEndpointProperties.connectionString", capture_output=True)

print(f"SQL Endpoint: {sql_endpoint}, Lakehouse ID: {lakehouse_id}")

# Import notebook

run_fab_command(f"import -f /{workspace_name}.workspace/NB_TRNSF_Raw.Notebook -i export/NB_TRNSF_Raw.Notebook")

# TODO: Attach to notebook to lakehouse. Can I do this in the import command and not after deploy? Do I need to type all that JSON in the command?

# Attach notebook to lakehouse

# run_fab_command(f"set -f /{workspace_name}.workspace/NB_TRNSF_Raw.Notebook -q lakehouse -i '{"known_lakehouses": [{"id": "${_lakehouse_id}\"}],\"default_lakehouse\": \"${_lakehouse_id}\",\"default_lakehouse_name\": \"${_lakehouse_name}\",\"default_lakehouse_workspace_id\": \"${_workspace_id}\"}'")

deploy_semanticmodel(semanticmodel_src_path, workspace_name, semanticmodel_name, semanticmodel_parameters={"Server": sql_endpoint})



