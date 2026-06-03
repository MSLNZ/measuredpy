from measuredpy import *

# single file
records = extract("simple-ex.py")
for r_i in records:
    for k,v in r_i.items():
        print(f"{k}: {v}")
    print()

# # or with Path
# from pathlib import Path
# records = extract_traceability(Path("src") / "calibration.py")

# # whole source tree
# records = extract_from_tree("src")