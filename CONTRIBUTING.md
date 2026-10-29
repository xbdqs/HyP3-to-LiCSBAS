# Contributing

Contributions that improve interoperability, validation, documentation or platform support are welcome.

## Before opening a pull request

1. Create a focused branch from `main`.
2. Keep scientific transformations explicit and documented.
3. Do not silently invent missing processor metadata.
4. Add or update regression tests for scientific behavior changes.
5. Run the local tests:

```bash
python tests/test_look_vector_branchcut.py
python tests/test_synthetic_zip_stack.py
python tests/test_end_to_end_crossplatform.py
```

6. Update `CHANGELOG.md` when user-visible behavior changes.

## Bug reports

Use the GitHub issue template and include the operating system, Python version, Rasterio/GDAL versions, the exact command, the traceback, and the non-sensitive part of the preflight/validation output needed to reproduce the problem.

Do not upload proprietary or sensitive source rasters unless you have permission to redistribute them.
