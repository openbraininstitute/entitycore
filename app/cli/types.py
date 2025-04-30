from enum import StrEnum


class ContentType(StrEnum):
    nwb = "application/nwb"
    h5 = "application/x-hdf"
    rab = "application/rab"
    smr = "application/smr"
    json = "application/json"
