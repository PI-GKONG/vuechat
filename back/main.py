from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json

app = FastAPI()

# CORS 설정
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # 모든 도메인 허용
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

class ConnectionManager:
	def __init__(self):
		self.active_connections: Dict[str, WebSocket] = {}

	async def connect(self, websocket: WebSocket, client_id: str):
		await websocket.accept()
		self.active_connections[client_id] = websocket
		await self.broadcast_active_connections()
		await self.broadcast({'id': 'system', 'data': f'{client_id}님이 참여했습니다.'})

	async def disconnect(self, client_id: str):
		self.active_connections.pop(client_id, None)
		await self.broadcast_active_connections()
		await self.broadcast({'id': 'system', 'data': f'{client_id}님이 나갔습니다.'})

	async def broadcast(self, message: Dict[str, str]):
		for connection in self.active_connections.values():
			await connection.send_text(json.dumps(message))
	
	async def broadcast_active_connections(self):
		user_list = list(self.active_connections.keys())
		print(user_list)
		active_connections_count = len(self.active_connections)
		await self.broadcast({'type': 'active_connections', 'count': active_connections_count, 'users': user_list})

manager = ConnectionManager()

@app.get("/")
def hi():
  return 'WebSocket Api Online'

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
	await manager.connect(websocket, client_id)
	try:
		while True:
			data = await websocket.receive_text()
			await manager.broadcast({'id': client_id, 'data': data})
	except WebSocketDisconnect:
		await manager.disconnect(client_id)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=18852, reload=True)
