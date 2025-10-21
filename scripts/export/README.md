# Exporting and importing public data

## Database

### Update the bash scripts

Update the scripts, as it should be done after any db migration:

```
uv run ./scripts/export/write_scripts.py
```

### Export the public data from the database

The following command requires read access to the database, and it builds a self-extracting archive.

It requires [makeself](https://github.com/megastep/makeself) to be available in the build system.

The env variables `PG*` must be set to read the source database:

```
PGUSER
PGHOST
PGPORT
PGDATABASE
PGPASSWORD
```

Example:

```
PGPASSWORD=entitycore PGPORT=5433 PGDATABASE=entitycore \
./scripts/export/build_database_archive.sh
```

### Import the public data into a new database

The following command drops the defined database and restores the data from the archive.

The env variables `PG*` must be set to write the target database:

```
PGUSER
PGHOST
PGPORT
PGDATABASE
PGPASSWORD
```

Example:

```
PGPASSWORD=entitycore PGPORT=5433 PGDATABASE=entitycore_public \
./install_db_20251021_805fc8028f39.run
```

## Assets

### Export the public assets from S3 to a local archive

By default `SYNC_OPTIONS=--dryrun` so you may need to specify `SYNC_OPTIONS=` as in the example below.
You may want to specify additional options, such as `SYNC_OPTIONS=--delete` to delete local files that aren't present in the S3 bucket.

```
AWS_PROFILE=staging-ro BUCKET_NAME=entitycore-data-staging SYNC_OPTIONS= \
./scripts/export/build_assets_archive.sh
```

### Import the public assets

The public assets can be extracted and imported, for example:

- in a new S3 bucket with `aws s3 sync`
- in a new S3 bucket that is mounted r/w with `mount-s3`
- in the local instance of minio, by mounting the directory as the `/data/aws_s3_internal` volume.
