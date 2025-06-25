# Manual deployment to staging

Temporary instructions to manually deploy the service to staging.

The database is dropped and restored at every deployment. 

This won't be needed or even possible after the service is deployed to production, and it's actually used.

## Instructions:

- make a new release in the entitycore repo following the correct versioning schema
- make a PR to update aws-terraform-deployment with the new tag
- only the first time, prepare a dedicated local workspace to be used only for deployment
```
git clone git@github.com:openbraininstitute/entitycore.git entitycore-deployment
cd entitycore-deployment
ln -s ../entitycore-data/mba_hierarchy.json
ln -s ../entitycore-data/files.txt
ln -s ../entitycore-data/download
ln -s ../entitycore-data/out
ln -s ../entitycore-data/cell_composition.json
ln -s ../entitycore-data/project_ids.txt
```
- ensure that all the files and directories linked with the previous commands actually exist.
- every time, import the nexus data, curate and organize files, and dump the db:
```
- git fetch && git pull
- make install
- make destroy
- make import
- rm -Rf public
- rm -Rf curated
- make curate-files
- make assign-project
- make organize-files
- make dump
```
- optionally, check the size of the files in public. For reference:
```
du -L -sh public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/*

 50G	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording
4.0M	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/emodel
 72K	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/experimental_neuron_density
572K	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/ion_channel_model
357M	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/mesh
 11G	public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/reconstruction_morphology
```
- ensure that the new version of the service is being deployed to AWS. The deployment should be failing because of an alembic error, that will be fixed after the following steps.
- go to the staging bastion host (need credentials to access the host and the db), and restore the db (replace the tags with the release tag):
```
- scp data/db_2025.5.0.dump obi-staging:entitycore-data
- ssh obi-staging
- cd entitycore-data
- DUMPFILE=db_2025.5.0.dump ./restore-db.sh (requires the db password)
```
- from the local environment, login to AWS S3 staging:
```
export AWS_PROFILE=staging-s3
aws sso login
aws s3 ls entitycore-data-staging/
```
- optional but recommended, delete all the files in `private` on S3, since they are not referenced anymore in the db
- optional and not recommended, delete all the files in `public` on S3. If not deleted, they are synchronized automatically anyway in the next point.
- from the local environment, sync the desired directories:
```
paths=(
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/emodel
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/experimental_neuron_density
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/ion_channel_model
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/mesh
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/reconstruction_morphology
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/0000cd5a-28a4-4bc5-8e62-d50c6bd42cbc
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/00065077-2d98-4ce4-b55b-9d1b55874606
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/0007f3e0-b233-4843-97c9-162ad42c0b65
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/000cb6b1-d7aa-4761-81c8-1941cd5d17f7
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/0017d773-c9db-4765-9d03-164dd8f4de57
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/001eec70-aea3-486f-96f0-a81af5f8a11f
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/002d6974-9c66-49ef-b5e5-9fa14922296e
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/002eb927-97fd-43fe-9e7d-481fdb9af4b1
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/00356b61-1952-4a57-9a7a-fdca460eacc7
public/a98b7abc-fc46-4700-9e3d-37137812c730/0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6/assets/electrical_cell_recording/00377e95-7733-4951-a7d2-6906e92e4f0e
)

for SRC in "${paths[@]}"; do
  echo "Processing $SRC"
  DST="s3://entitycore-data-staging/$SRC"
  time aws s3 sync "$SRC" "$DST"
done
```
- verify the deployment on AWS

## Appendix

### restore-db.sh

Script to be run on the staging bastion host (PGHOST can be hardcoded, since it shouldn't change unless the db is redeployed).

```bash
#!/bin/bash
set -eux

PATH=/usr/pgsql-17/bin:$PATH

export PGUSER=entitycore
export PGHOST=entitycore.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com
export PGPORT=5432
export PGDATABASE=entitycore

echo "Restoring database $PGDATABASE from $DUMPFILE to $PGHOST:$PGPORT"
dropdb --force $PGDATABASE
createdb $PGDATABASE
pg_restore --clean --if-exists --exit-on-error --no-owner --dbname $PGDATABASE $DUMPFILE

psql -c "ANALYZE;"
```

### missing distributions

If distributions are referenced in the database but not present in the exported data, one can fetch the files using the following command:

``` make fetch-missing-distributions ```

This takes as an input the files.txt containing the exported digests, the "out" directory with the exported metadata, and put everything in a directory called "missing_distributions" (to be created beforehand)

### project_ids.txt

contains the list of projectid,virtuallabid in prod. For instance
```50be7f9f-c94d-4e8d-8dc1-aa5690f0cb05,7133f98a-1192-46bc-9358-f59aac00b99b```

it is generated with the following command against the virtual-lab-manager-db postgres database:
```\COPY (SELECT id, virtual_lab_id FROM project) TO 'project_id.csv' WITH CSV;```

