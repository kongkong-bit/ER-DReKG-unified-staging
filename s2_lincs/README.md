# S1 and LINCS processing

The project-scoped S2 API runs `project_screen.py` with `s2_lincs/.venv` when
present; otherwise it uses the Python interpreter running the backend. Install
the pinned scientific dependencies from `requirements.txt` into that selected
environment before running an analysis. For example, from the repository root:

```powershell
uv pip install --python backend/.venv/Scripts/python.exe -r s2_lincs/requirements.txt
```

To isolate the ETL instead, create `s2_lincs/.venv`, install the same
requirements there, and install pytest there to run `python -m pytest -q`.
Original input data are read-only. `work/` contains decompressed HDF5 data and
must be prepared from the documented LINCS source files. Random seed: 42.
