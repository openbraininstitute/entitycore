from app.db.model import Base

NOT_VERSIONED = {
    "transaction",
    "transaction_changes",
}


def test_versioned_tables():
    versioned_tables = set()
    not_versioned_tables = set()
    check_existing = set()  # _version tables
    for mapper in Base.registry.mappers:
        versioned = getattr(mapper.class_, "__versioned__", None)
        table = getattr(mapper.class_, "__table__", None)
        tablename = getattr(table, "name", None)
        if tablename is None:
            continue
        if tablename.endswith("_version"):
            check_existing.add(tablename.removesuffix("_version"))
        elif versioned is None:
            not_versioned_tables.add(tablename)
        else:
            versioned_tables.add(tablename)
    # sanity check
    assert len(versioned_tables) > 0
    # check that the _version table exists for each table with __versioned__ attribute
    assert versioned_tables == check_existing
    # check that all the tables are versioned, excluding the tables not expected to be versioned
    assert not_versioned_tables == NOT_VERSIONED
