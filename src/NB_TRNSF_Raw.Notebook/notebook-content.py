# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "3d020a17-ccd9-402e-9f1a-01c458a797b2",
# META       "default_lakehouse_name": "LH_STORE_RAW",
# META       "default_lakehouse_workspace_id": "84912f9a-8d9a-43d0-a945-99e74142a0f2",
# META       "known_lakehouses": [
# META         {
# META           "id": "3d020a17-ccd9-402e-9f1a-01c458a797b2"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import os
from pyspark.sql import functions as F

# Incremental tables
csv_files = ["customer.csv", "sales.csv", "product.csv", "store.csv"]

for csv_file in csv_files:

    table_name = os.path.splitext(csv_file)[0]

    # Read the source table
    df = spark.read.format("csv").option("header","true").load(f"Files/raw/{csv_file}")

    # remove column name invalid chars

    df = df.select([F.col(col).alias(col.replace(' ', '')) for col in df.columns])
   
    # Write to the target schema, replacing the existing table

    df.write.mode("overwrite").option("overwriteSchema", "true").format("delta").saveAsTable(f"raw.{table_name}")    
    

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
