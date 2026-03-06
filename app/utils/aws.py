import boto3


def get_codeartifact_client():
    return boto3.client("codeartifact", region_name="us-east-1")
