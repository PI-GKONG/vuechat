from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json
import time

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
		self.messages: List[Dict[str, any]] = []

	async def connect(self, websocket: WebSocket, client_id: str):
		await websocket.accept()
		self.active_connections[client_id] = websocket
		await self.broadcast_active_connections()
		await self.broadcast({'id': 'system', 'data': f'{client_id}님이 참여했습니다.', 'type': 'system'})

	async def disconnect(self, client_id: str):
		self.active_connections.pop(client_id, None)
		await self.broadcast_active_connections()
		await self.broadcast({'id': 'system', 'data': f'{client_id}님이 나갔습니다.', 'type': 'system'})

	async def broadcast(self, message: Dict[str, any]):
		for connection in self.active_connections.values():
			await connection.send_text(json.dumps(message))
	
	async def broadcast_active_connections(self):
		user_list = list(self.active_connections.keys())
		active_connections_count = len(self.active_connections)
		await self.broadcast({'type': 'active_connections', 'count': active_connections_count, 'users': user_list})
	
	async def handle_message(self, client_id: str, data: str):
		message_id = len(self.messages) + 1
		now = time
		send_time = str(now.localtime().tm_hour) + ':' + str(now.localtime().tm_min)

		message = {'id': client_id, 'data': data, 'unreadCount': len(self.active_connections) - 1, 'messageId': message_id, 'type': 'message', 'time': send_time}
		self.messages.append(message)
		await self.broadcast(message)
	
	async def mark_as_read(self, message_id: int, client_id: str):
		for message in self.messages:
			print(self, message)
			if message['messageId'] == message_id and message['unreadCount'] > 0:
				message['unreadCount'] -= 1
				await self.broadcast({'type': 'read', 'messageId': message_id, 'unreadCount': message['unreadCount']})

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
			message = json.loads(data)
			if message['type'] == 'message':
				await manager.handle_message(client_id, message['data'])
			elif message['type'] == 'read':
				await manager.mark_as_read(message['messageId'], client_id)
	except WebSocketDisconnect:
		await manager.disconnect(client_id)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=18852, reload=True)
