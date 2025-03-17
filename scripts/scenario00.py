import os
from utils import *

capacity_name = "Trial-ruiromano-microsoft-com-05-24-2023-15-11-UTC"
workspace_name = "RR-SalesSense"
semanticmodel_name = "Sales Model"
report_name = "Sales Report"
connection_name = "RR - Git Sample files2"
source_url = "https://raw.githubusercontent.com/pbi-tools/sales-sample/refs/heads/data/RAW-Sales.csv"
semanticmodel_src_path = "src/adventureworks/semanticmodels/adventureworks"

# Create workspace and skip error if exists

#run_fab_command(f"create /{workspace_name}.Workspace -P capacityName={capacity_name}", silently_continue=True)

# Create connection to the data files location

#run_fab_command(f"create .connections/{connection_name}.Connection -P connectionDetails.type=HttpServer,connectionDetails.parameters.url={source_url},credentialDetails.type=Anonymous", silently_continue=True)

# Import data pipeline

#run_fab_command(f"import -f /{workspace_name}.workspace/DP_INGST_CopyCSV.datapipeline -i src/DP_INGST_CopyCSV.DataPipeline")

# Import notebook
    
run_fab_command(f"import -f /{workspace_name}.workspace/NB_TRNSF_Raw.Notebook -i src/NB_TRNSF_Raw.Notebook")
