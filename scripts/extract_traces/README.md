# Extract response payloads generated in unit tests

Execute:

```
make extract-traces
```

to:

1. Dump the request and response payloads when running unit tests the `traces/latest` directory.
2. Extract the response payloads for some selected requests, and organize them in subfolders in the `extracted` directory.

**Warning: the content of the above directories will be completely deleted before running the extraction!**


Alternatively, you can define directories different from the default by executing:

```
REQUEST_TRACER_OUTPUT=traces/latest \
EXTRACTED_TRACES=extracted \
make extract-traces
```

The extracted folder can be moved to `tests/unit/model/data/extracted` in entitysdk to update the data used during tests.
