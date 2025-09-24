import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_CSV_FIELDS: List[str] = [
    "frame_id",
    "timestamp",
    "status",
    "within_tolerance",
    "detection_method",
    "cx_px",
    "cy_px",
    "angle_deg",
    "width_px",
    "height_px",
    "dx_mm",
    "dy_mm",
    "dtheta_deg",
    "session_id",
    "preset_name",
    "dataset_path",
]


@dataclass
class ResultLogger:
    output_dir: Path
    formats: List[str]
    csv_name: str = "results.csv"
    json_name: str = "results.jsonl"

    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._csv_file: Optional[object] = None
        self._csv_writer: Optional[csv.DictWriter] = None
        self._json_file: Optional[object] = None
        self._normalized_formats = {fmt.lower() for fmt in self.formats}

    def open(self) -> None:
        if "csv" in self._normalized_formats:
            self._csv_file = (self.output_dir / self.csv_name).open("w", newline="")
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=_CSV_FIELDS)
            self._csv_writer.writeheader()
        if "json" in self._normalized_formats:
            self._json_file = (self.output_dir / self.json_name).open("w")

    def close(self) -> None:
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
        if self._json_file:
            self._json_file.close()
            self._json_file = None

    def log(self, record: Dict[str, object]) -> None:
        if "csv" in self._normalized_formats and self._csv_writer:
            row = {key: record.get(key) for key in _CSV_FIELDS}
            self._csv_writer.writerow(row)
        if "json" in self._normalized_formats and self._json_file:
            self._json_file.write(json.dumps(record) + "\n")

    def __enter__(self) -> "ResultLogger":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
