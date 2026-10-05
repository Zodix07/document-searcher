import json
from pathlib import Path
import sys

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from app.main import app


output_path = (
    Path(__file__).resolve().parents[1]
    / "docs.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        app.openapi(),
        file,
        ensure_ascii=False,
        indent=2,
    )

print(f"OpenAPI documentation saved to {output_path}")