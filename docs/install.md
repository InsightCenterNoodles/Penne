Installation is as simple as:

```bash
pip install penne
```

Penne has a few dependencies:

* [`websockets`](https://websockets.readthedocs.io/en/stable/): Websocket connections in Python.
* [`cbor2`](https://cbor2.readthedocs.io/en/latest/): Concise Binary Object Representation for messages.
* [`pydantic`](https://docs.pydantic.dev/dev-v2/): Data validation and coercion for parsing messages.
* [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types): Easy to use color format

If you've got Python 3.9+ and `pip` installed, you're good to go.

!!! Note

    For stability, Penne's dependencies are pinned to specific versions. While these are up to date as of August
    2023, you may want to update them to the latest versions. To do so, simply update the package yourself.