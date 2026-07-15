from pathlib import Path

PROJECT: Path = Path(__file__).parent.parent
DATA: Path = PROJECT / "data"
SHAPEFILES: Path = DATA / "Campus" / "shapefiles"
CODE: Path = PROJECT / "Code"
RESULTS: Path = PROJECT / "results"

