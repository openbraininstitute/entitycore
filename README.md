# Install

Make sure you have `uv`: https://docs.astral.sh/uv/getting-started/installation/

```
# setup virtualenv:
$ uv sync

# import data:
uv run -m app.cli.import-data --db test.db --input_dir

#run server
uv run uvicorn app:app --reload
```
