#!/usr/bin/env python3
"""
Simulated feed clients for local testing.
"""

class SimulatedFeedClient:
    def __init__(self, scores, default_score=None):
        self.scores = scores or []
        self.default_score = default_score or {"team_a": 0, "team_b": 0}
        self.index = 0

    async def get_score(self):
        if not self.scores:
            return self.default_score

        if self.index >= len(self.scores):
            return self.scores[-1]

        score = self.scores[self.index]
        self.index += 1
        return score
