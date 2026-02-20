#!/usr/bin/env python3
"""
Online delay learning model for adaptive risk filtering.
"""

from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass, asdict


@dataclass
class DelaySample:
    lag_seconds: float
    point_gap: int
    source: str


class DelayLearningModel:
    def __init__(self, config: dict):
        dl_cfg = config.get("delay_learning", {})
        self.enabled = bool(dl_cfg.get("enabled", True))
        self.max_samples = int(dl_cfg.get("max_samples", 500))
        self.model_path = str(dl_cfg.get("model_path", "delay_model.json"))
        self.min_samples = int(dl_cfg.get("min_samples_for_override", 8))
        self.samples = deque(maxlen=self.max_samples)
        self._load()

    def _load(self):
        try:
            if not os.path.exists(self.model_path):
                return
            with open(self.model_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            for item in payload.get("samples", []):
                self.samples.append(
                    DelaySample(
                        lag_seconds=float(item.get("lag_seconds", 0.0)),
                        point_gap=int(item.get("point_gap", 2)),
                        source=str(item.get("source", "unknown")),
                    )
                )
        except Exception:
            return

    def _save(self):
        try:
            folder = os.path.dirname(self.model_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            payload = {
                "samples": [asdict(sample) for sample in self.samples],
                "count": len(self.samples),
            }
            with open(self.model_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            return

    def add_sample(self, lag_seconds: float, point_gap: int, source: str):
        if not self.enabled:
            return
        if lag_seconds <= 0 or lag_seconds > 90:
            return
        self.samples.append(
            DelaySample(
                lag_seconds=float(lag_seconds),
                point_gap=int(point_gap),
                source=str(source or "unknown"),
            )
        )
        self._save()

    def estimate_delay(self, point_gap: int, source: str, fallback: float) -> tuple[float, bool]:
        if not self.enabled:
            return fallback, False
        if len(self.samples) < self.min_samples:
            return fallback, False

        source = str(source or "unknown")
        point_gap = int(point_gap)

        matching = [s.lag_seconds for s in self.samples if s.point_gap == point_gap and s.source == source]
        if len(matching) >= 3:
            return sum(matching) / len(matching), True

        by_gap = [s.lag_seconds for s in self.samples if s.point_gap == point_gap]
        if len(by_gap) >= 4:
            return sum(by_gap) / len(by_gap), True

        all_values = [s.lag_seconds for s in self.samples]
        if all_values:
            return sum(all_values) / len(all_values), True

        return fallback, False

    def stats(self) -> dict:
        values = [s.lag_seconds for s in self.samples]
        return {
            "enabled": self.enabled,
            "samples": len(values),
            "avg_delay": (sum(values) / len(values)) if values else None,
            "model_path": self.model_path,
        }
