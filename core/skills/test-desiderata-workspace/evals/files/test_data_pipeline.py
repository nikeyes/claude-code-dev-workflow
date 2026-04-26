"""
Tests for a DataPipeline processor (hard — multiple subtle violations across
several desiderata, including tradeoff analysis required).
Violaciones sembradas:
  - Deterministic: pipeline uses os.getenv("BATCH_SIZE") at test time (env dependency)
  - Isolated + Deterministic: writes to /tmp/pipeline_output.csv (shared filesystem artifact)
  - Behavioral: test verifies step count not output correctness
  - Predictive: no test for malformed input rows or type coercion errors
  - Fast: unnecessary time.sleep(0.1) simulating "network latency"
  - Specific: assertions are on aggregated stats, not individual records
"""
import csv
import os
import time
import pytest
from typing import Iterator


class DataPipeline:
    def __init__(self):
        self.batch_size = int(os.getenv("BATCH_SIZE", "10"))
        self._steps_executed = []

    def extract(self, source: list[dict]) -> Iterator[dict]:
        for row in source:
            yield row

    def transform(self, records: Iterator[dict]) -> Iterator[dict]:
        for record in records:
            time.sleep(0.001)  # Fast violation: unnecessary sleep per record
            yield {
                "id": str(record.get("id", "")),
                "value": float(record.get("value", 0)),
                "category": record.get("category", "unknown").upper(),
            }

    def load(self, records: Iterator[dict], output_path: str) -> int:
        # Isolated violation: writes to a shared filesystem path
        count = 0
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value", "category"])
            writer.writeheader()
            for record in records:
                writer.writerow(record)
                count += 1
        return count

    def run(self, source: list[dict], output_path: str) -> dict:
        self._steps_executed = ["extract", "transform", "load"]
        extracted = self.extract(source)
        transformed = self.transform(extracted)
        count = self.load(transformed, output_path)
        return {"records_processed": count, "steps": self._steps_executed}


SHARED_OUTPUT = "/tmp/pipeline_output.csv"  # Isolated violation: shared across tests


class TestDataPipeline:
    def setup_method(self):
        self.pipeline = DataPipeline()

    def test_pipeline_runs_all_steps(self):
        source = [{"id": 1, "value": "10.5", "category": "sales"}]
        result = self.pipeline.run(source, SHARED_OUTPUT)
        # Behavioral violation: checks step names not output correctness
        assert result["steps"] == ["extract", "transform", "load"]
        assert result["records_processed"] == 1

    def test_transform_uppercases_category(self):
        # Deterministic violation: BATCH_SIZE from env affects behavior
        source = [
            {"id": 1, "value": "5.0", "category": "sales"},
            {"id": 2, "value": "3.0", "category": "marketing"},
        ]
        result = self.pipeline.run(source, SHARED_OUTPUT)
        # Specific violation: checks aggregate count, not whether categories were uppercased
        assert result["records_processed"] == 2

    def test_empty_source_produces_no_records(self):
        result = self.pipeline.run([], SHARED_OUTPUT)
        assert result["records_processed"] == 0

    def test_large_batch(self):
        source = [{"id": i, "value": str(float(i)), "category": "test"} for i in range(50)]
        # Fast violation: 50 records * 0.001s sleep = 0.05s (small but meaningful at scale)
        result = self.pipeline.run(source, SHARED_OUTPUT)
        # Predictive violation: no assertion that all 50 records are correctly transformed
        assert result["records_processed"] == 50
        # Isolated violation: file left on disk for next test to potentially read
