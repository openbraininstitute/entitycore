# Exporting and importing public data

## Database

### Update the bash scripts:

Update the scripts, as it should be done after any db migration.

```
uv run ./scripts/export/write_scripts.py
```

### Export the public data from the database

This command requires a user with read-only access to the database.

```
PGPASSWORD=entitycore PGPORT=5433 PGDATABASE=entitycore \
./scripts/export/build_database_archive.sh
```

### Import the public data into a new database

This command drops the existing database and restores the data from the archive.

```
PGPASSWORD=entitycore PGPORT=5433 PGDATABASE=entitycore_public \
./install_db_20251021_805fc8028f39.sh

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

The public assets can be extracted and imported for example:

- in a new S3 bucket by using `aws s3 sync`
- in a new S3 bucket that is mounted r/w with `mount-s3`
- in the local instance of minio, by mounting the directory as the `/data/aws_s3_internal` volume.
