import json
import sys
import time
from dataclasses import dataclass, field, asdict


@dataclass
class LLMCall:
    duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class MetricsCollector:
    framework: str = ""
    pattern: str = ""
    answer: str = ""
    llm_calls: list[LLMCall] = field(default_factory=list)
    total_duration_ms: float = 0.0
    _start: float = field(default=0.0, repr=False)

    def start_timer(self):
        self._start = time.perf_counter()

    def stop_timer(self):
        self.total_duration_ms = (time.perf_counter() - self._start) * 1000

    def record_llm_call(self, duration_ms: float, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.llm_calls.append(LLMCall(duration_ms=duration_ms, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens))

    def emit(self):
        result = asdict(self)
        del result["_start"]
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
