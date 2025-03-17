import os
from utils import *

capacity_name = "Trial-ruiromano-microsoft-com-05-24-2023-15-11-UTC"
workspace_name = "RR-SalesSense"
semanticmodel_name = "Sales Model"
report_name = "Sales Report"
semanticmodel_src_path = "src/adventureworks/semanticmodels/adventureworks"

# Create workspace and skip error if exists

#run_fab_command(f"create /{workspace_name}.Workspace -P capacityName={capacity_name}", silently_continue=True)

# deploy pipeline

#run_fab_command(f"import -f /{workspace_name}.workspace/DP_INGST_CopyCSV2.datapipeline -i src/DP_INGST_CopyCSV.DataPipeline")

run_fab_command(f"import -f /{workspace_name}.workspace/NB_TRNSF_Raw.Notebook -i src/NB_TRNSF_Raw.Notebook")
