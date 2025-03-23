import os
import time
import argparse
import glob
from utils import *

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--spn-auth", action="store_true", default=True)
parser.add_argument("--workspace", default="SalesSense")
parser.add_argument("--admin-upns", default=os.getenv("FABRIC_ADMIN_UPNS"))
parser.add_argument(
    "--capacity", default=os.getenv("FABRIC_CAPACITY")
)

args = parser.parse_args()

spn_auth = args.spn_auth
capacity_name = args.capacity
workspace_name = args.workspace
admin_upns = args.admin_upns

workspace_name_data = f"{workspace_name} - Data"
workspace_name_analytics = f"{workspace_name} - Analytics"

if admin_upns:
    admin_upns = [upn.strip() for upn in admin_upns.split(",")]

lakehouse_name = "LH_STORE_RAW"
connection_name = "SalesSense - PRD"
connection_source_url = "https://raw.githubusercontent.com/pbi-tools/sales-sample/refs/heads/data/RAW-Sales.csv"

# Authenticate

if spn_auth:
    fab_authenticate_spn()

# Create Fabric connection to use in data pipeline

connection_id = create_connection(    
    connection_name=connection_name,
    parameters={
        "connectionDetails.type": "HttpServer",
        "connectionDetails.parameters.url": connection_source_url,
        "credentialDetails.type": "Anonymous",
    }    
)

# Data Workspace

workspace_id_data = create_workspace(workspace_name_data, capacity_name, upns=admin_upns)

workspace_id_analytics = create_workspace(workspace_name_analytics, capacity_name, upns=admin_upns)

# Create lakehouse

lakehouse_id = create_item(
    workspace_name=workspace_name_data,
    item_type="lakehouse",
    item_name=lakehouse_name,
    parameters={"enableSchemas": "true"},
)

# Deploy data pipeline binded to the connection and workspace

deploy_item(
    "src/DP_INGST_CopyCSV.DataPipeline",
    workspace_name=workspace_name_data,
    find_and_replace={
        (
            r"pipeline-content.json",
            r'("workspaceId"\s*:\s*)".*"',
        ): rf'\1"{workspace_id_data}"',
        (
            r"pipeline-content.json",
            r'("artifactId"\s*:\s*)".*"',
        ): rf'\1"{lakehouse_id}"',
        (
            r"pipeline-content.json",
            r'("connection"\s*:\s*)".*"',
        ): rf'\1"{connection_id}"',
    },    
)

# Deploy notebook

deploy_item(
    "src/NB_TRNSF_Raw.Notebook",
    workspace_name=workspace_name_data,
    find_and_replace={
        (
            r"notebook-content.ipynb",
            r'("default_lakehouse"\s*:\s*)".*"',
        ): rf'\1"{lakehouse_id}"',
        (
            r"notebook-content.ipynb",
            r'("default_lakehouse_name"\s*:\s*)".*"',
        ): rf'\1"{lakehouse_name}"',
        (
            r"notebook-content.ipynb",
            r'("default_lakehouse_workspace_id"\s*:\s*)".*"',
        ): rf'\1"{workspace_id_data}"',
        (
            r"notebook-content.ipynb",
            r'("known_lakehouses"\s*:\s*)\[[\s\S]*?\]',
        ): rf'\1[{{"id": "{lakehouse_id}"}}]',
    },
)

# Get SQL endpoint - its created asynchronously so we need to wait for it to be available

for attempt in range(3):

    sql_endpoint = run_fab_command(
        f"get /{workspace_name_data}.workspace/{lakehouse_name}.lakehouse -q properties.sqlEndpointProperties.connectionString",
        capture_output=True,
    )

    time.sleep(5)

if not sql_endpoint:
    raise Exception(f"Cannot resolve SQL endpoint for lakehouse {lakehouse_name}")

# Deploy semantic model

semanticmodel_id = deploy_item(
    "src/SM_SalesSense.SemanticModel",
    workspace_name=workspace_name_analytics,
    find_and_replace={
        (
            r"expressions.tmdl",
            r'(expression\s+Server\s*=\s*)".*?"',
        ): rf'\1"{sql_endpoint}"'
    },
)

# Deploy reports

for report_path in glob.glob("src/*.Report"):

    deploy_item(
        report_path,
        workspace_name=workspace_name_analytics,
        find_and_replace={
            ("definition.pbir", r"\{[\s\S]*\}"): json.dumps(
                {
                    "version": "4.0",
                    "datasetReference": {
                        "byConnection": {
                            "connectionString": None,
                            "pbiServiceModelId": None,
                            "pbiModelVirtualServerName": "sobe_wowvirtualserver",
                            "pbiModelDatabaseName": semanticmodel_id,
                            "name": "EntityDataSource",
                            "connectionType": "pbiServiceXmlaStyleLive",
                        }
                    },
                }
            )
        },
    )

# Log out in case of auth with SPN

if spn_auth:
    run_fab_command("auth logout")
