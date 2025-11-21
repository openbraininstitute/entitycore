# Extract response payloads generated in unit tests

### Dump the request and response payloads when running unit tests

To save the payloads in the `traces` directory, execute:

```
REQUEST_TRACER_ENABLE=1 REQUEST_TRACER_INDENT=2 make test-local
```

### Extract the response payloads for the POST requests, and organize them in subfolders

To extract all the response payloads to the `extracted` directory, remove any pre-existing directory and execute the following command, after replacing the source directory:

```
uv run ./scripts/extract_traces/run.py --source traces/2025-11-19T09:44:19.114166+00:00
```

### Copy the extracted directory to entitysdk

Copy the extracted folder to `tests/unit/model/data/extracted` if desired.
