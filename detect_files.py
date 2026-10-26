
from pathlib import Path
import pandas as pd
import pyreadstat

# ============================================================
# SETTINGS
# ============================================================

DATA_ROOT = Path("./data")
OUTPUT_DIR = Path("./01_file_headers")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_ROOT.exists():
    raise FileNotFoundError(
        f"Data directory not found: {DATA_ROOT.resolve()}"
    )

# ============================================================
# FIND FILES
# ============================================================

files = sorted(
    p for p in DATA_ROOT.rglob("*")
    if p.is_file() and p.suffix.lower() in {".csv", ".dta"}
)

if not files:
    raise FileNotFoundError(
        f"No CSV or DTA files found in {DATA_ROOT.resolve()}"
    )

print("=" * 80)
print("FILE AND HEADER INVENTORY")
print("=" * 80)
print(f"Files found: {len(files)}")
print()

# ============================================================
# EXTRACT HEADERS ONLY
# ============================================================

def extract_headers(path):

    if path.suffix.lower() == ".csv":
        # Read the CSV header only, not its observations.
        last_error = None

        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                df = pd.read_csv(
                    path,
                    nrows=0,
                    encoding=encoding
                )
                return list(df.columns)

            except Exception as exc:
                last_error = exc

        raise last_error

    elif path.suffix.lower() == ".dta":
        # Read Stata metadata only; do not load the data rows.
        _, meta = pyreadstat.read_dta(
            str(path),
            metadataonly=True
        )

        return list(meta.column_names)

    raise ValueError(f"Unsupported file type: {path.suffix}")


# ============================================================
# PROCESS ALL FILES
# ============================================================

records = []

for i, path in enumerate(files, start=1):

    relative_path = path.relative_to(DATA_ROOT)

    source = (
        relative_path.parts[0]
        if len(relative_path.parts) > 1
        else "ROOT"
    )

    print("=" * 80)
    print(f"[{i}/{len(files)}] {relative_path}")
    print(f"Source: {source}")
    print(f"Type: {path.suffix.lower()}")

    try:
        headers = extract_headers(path)

        status = "OK"
        error = ""

        print(f"Columns: {len(headers)}")

        for j, header in enumerate(headers, start=1):
            print(f"  {j:4d}. {header}")

    except Exception as exc:
        headers = []
        status = "ERROR"
        error = f"{type(exc).__name__}: {exc}"

        print(f"ERROR: {error}")

    records.append({
        "file_number": i,
        "source": source,
        "relative_path": str(relative_path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_MB": round(path.stat().st_size / (1024 ** 2), 3),
        "n_columns": len(headers) if status == "OK" else None,
        "headers": " | ".join(map(str, headers)),
        "status": status,
        "error": error
    })

# ============================================================
# SAVE CSV REPORT
# ============================================================

inventory = pd.DataFrame(records)

csv_path = OUTPUT_DIR / "file_headers.csv"

inventory.to_csv(
    csv_path,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# SAVE READABLE TEXT REPORT
# ============================================================

txt_path = OUTPUT_DIR / "file_headers.txt"

with open(txt_path, "w", encoding="utf-8") as f:

    f.write("FILE AND HEADER INVENTORY\n")
    f.write("=" * 80 + "\n")
    f.write(f"Data root: {DATA_ROOT.resolve()}\n")
    f.write(f"Files found: {len(files)}\n\n")

    for record in records:

        f.write("=" * 80 + "\n")
        f.write(f"File: {record['relative_path']}\n")
        f.write(f"Source: {record['source']}\n")
        f.write(f"Type: {record['extension']}\n")
        f.write(f"Status: {record['status']}\n")

        if record["status"] == "OK":
            f.write(f"Number of columns: {record['n_columns']}\n")

            for j, header in enumerate(
                record["headers"].split(" | "), start=1
            ):
                f.write(f"  {j}. {header}\n")
        else:
            f.write(f"Error: {record['error']}\n")

        f.write("\n")

# ============================================================
# SUMMARY
# ============================================================

successful = (inventory["status"] == "OK").sum()
failed = (inventory["status"] == "ERROR").sum()

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
print(f"Total files: {len(files)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

if failed:
    print("\nFiles that failed:")
    print(
        inventory.loc[
            inventory["status"] == "ERROR",
            ["relative_path", "error"]
        ].to_string(index=False)
    )

print(f"\nCSV report: {csv_path.resolve()}")
print(f"Text report: {txt_path.resolve()}")
print("Original files were not modified.")
