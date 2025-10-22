# Exporting and importing public data

## Database

### Update the bash scripts

After any db migration, the script `build_database_archive.sh` should be updated by running:

```
uv run ./scripts/export/write_scripts.py
```

### Export the public data from the database

The script `build_database_archive.sh` requires access to read the database, and it builds a self-extracting archive named `install_db_{YYYYMMDD}_{DB_VERSION}.run` in the working directory.

It requires:

- [psql](https://www.postgresql.org/docs/current/app-psql.html)
- [pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)
- [makeself](https://github.com/megastep/makeself)

To read the source database, the env variables `PG*` must be set accordingly:

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

The script `install_db_{YYYYMMDD}_{DB_VERSION}.run` drops the database and loads the data contained in the archive.

It requires:

- [psql](https://www.postgresql.org/docs/current/app-psql.html)

To write the target database, the env variables `PG*` must be set accordingly:

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

The script `build_assets_archive.sh` synchronizes data from a S3 bucket to a local directory (`data/assets-sync` by default), and build an archive named `assets_{BUCKET_NAME}_{YYYYMMDD}.tar.gz` in the working directory.

You should set some env variables:

```
AWS_PROFILE: name of the AWS profile.
BUCKET_NAME: name of the source bucket.
SYNC_OPTIONS: options to pass to `aws s3 sync`.
DST_DIR: directory where the files are downloaded. Warning: any data in this directory might be overwritten or deleted!
```

By default the scripts uses `SYNC_OPTIONS=--dryrun` so you may need to specify `SYNC_OPTIONS=` to actually retrieve the data, or `SYNC_OPTIONS=--delete` to delete local files that aren't present in the S3 bucket.

Example:

```
AWS_PROFILE=staging-ro BUCKET_NAME=entitycore-data-staging SYNC_OPTIONS= \
./scripts/export/build_assets_archive.sh
```

### Import the public assets

The public assets can be extracted and imported, for example:

- in a new S3 bucket with `aws s3 sync`
- in a new S3 bucket that is mounted r/w with `mount-s3`
- in the local instance of minio, by mounting the directory as the `/data/aws_s3_internal` volume.
