"""
Event Logger — AutoGen-style event logging for feasibility evaluation.
NHS Agentic AI Platform | LD7326 | W25041744
"""

import json
import time
import datetime
import pandas as pd
from typing import Any
from pathlib import Path


class EventLogger:
    """
    Logs all agent actions with timestamps for feasibility evaluation.
    Produces structured JSON and CSV outputs compatible with AutoGen logging.
    """

    def __init__(self, session_id: str = None):
        self.events = []
        self.start_time = time.time()
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(self, agent: str, action: str, input_data: Any,
            output: str, duration_ms: float) -> None:
        """Log a single agent action event."""
        event = {
            "session_id":     self.session_id,
            "timestamp":      datetime.datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - self.start_time, 3),
            "agent":          agent,
            "action":         action,
            "duration_ms":    round(duration_ms, 2),
            "input_summary":  str(input_data)[:100],
            "output_summary": output[:200]
        }
        self.events.append(event)
        print(f"  [{event['elapsed_seconds']:6.3f}s] [{agent:<25}] {output[:70]}")

    def save_json(self, filepath: str = "outputs/logs/event_log.json") -> None:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.events, f, indent=2)
        print(f"\nEvent log saved: {filepath} ({len(self.events)} events)")

    def save_csv(self, filepath: str = "outputs/logs/event_log.csv") -> None:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(self.events)
        df.to_csv(filepath, index=False)
        print(f"Event log CSV saved: {filepath}")

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.events)

    def summary(self) -> dict:
        return {
            "session_id":   self.session_id,
            "total_events": len(self.events),
            "total_time_s": round(time.time() - self.start_time, 3),
            "agents_used":  list(set(e["agent"] for e in self.events))
        }