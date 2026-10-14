# configs

`collect.py` writes each device's running config here as `<site>/<device>.cfg` (`.xml` for PAN-OS), scrubbed of secrets. The nightly `collect` workflow commits them, so git history is your backup and change log.

It starts out seeded with the lab's startup configs (`lab/`), so the tests in `tests/` have something to run on. The first `collect.py` run against the lab replaces them with the switches' real running configs.
