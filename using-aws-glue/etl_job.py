import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from awsglue.transforms import *

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'INPUT_S3_PATH', 'OUTPUT_DDB_TABLE'])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read CSV data
dyf = glueContext.create_dynamic_frame.from_options(
    connection_type = "s3",
    connection_options = {"paths": [args['INPUT_S3_PATH']]},
    format = "csv",
    format_options = {"withHeader": True},
    transformation_ctx="datasource1"
)

# Filter out rows where account or offer_id are null/empty
def filter_nulls(rec):
    return rec["account"] is not None and rec["account"] != "" and rec["offer_id"] is not None and rec["offer_id"] != ""

filtered_dyf = Filter.apply(frame = dyf, f = filter_nulls, transformation_ctx = "filtered_dyf")

# Convert key fields to strings to ensure compatibility with DynamoDB
def convert_keys_to_string(rec):
    rec["account"] = str(rec["account"])
    rec["offer_id"] = str(rec["offer_id"])
    return rec

transformed_dyf = Map.apply(frame = filtered_dyf, f = convert_keys_to_string, transformation_ctx = "transformed_dyf")

# Write to DynamoDB
glueContext.write_dynamic_frame.from_options(
    frame = transformed_dyf,
    connection_type = "dynamodb",
    connection_options = {
        "dynamodb.output.tableName": args['OUTPUT_DDB_TABLE'],
        "dynamodb.throughput.write.percent": "1"
    },
    transformation_ctx="datasink1"
)

job.commit()