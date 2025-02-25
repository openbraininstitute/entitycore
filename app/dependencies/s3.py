from typing import Annotated

from fastapi import Depends
from types_boto3_s3 import S3Client

from app.utils.s3 import get_s3_client

S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]
