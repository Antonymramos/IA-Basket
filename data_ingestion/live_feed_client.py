#!/usr/bin/env python3
"""
Live Feed Client - WebSocket client for real-time game scores
"""

import asyncio
import json
import websockets

class LiveFeedClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
    
    async def get_score(self):
        """
        Connect to WebSocket and get current score
        """
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send request for score
                await websocket.send(json.dumps({"action": "get_score"}))
                response = await websocket.recv()
                data = json.loads(response)
                return data
        except Exception as e:
            print(f"Erro ao obter placar da transmissão: {e}")
            return {"team_a": 0, "team_b": 0}