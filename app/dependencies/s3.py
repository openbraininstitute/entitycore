from typing import Annotated

from fastapi import Depends

from app.utils.s3 import StorageClientFactory, get_s3_client

StorageClientFactoryDep = Annotated[StorageClientFactory, Depends(lambda: get_s3_client)]
