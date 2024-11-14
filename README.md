# Install

```
pip install tqdm fastapi uvicorn sqlalchemy

# create db & tables
python3 model.py

# import data
python3 ./import_data.py --db test.db --input_dir nexus-dump/nexus_data/out/

#run server
uvicorn app:app --reload
```
