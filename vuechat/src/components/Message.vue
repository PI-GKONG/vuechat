<script setup>
	import { ref, onMounted, watch, nextTick } from 'vue';
	import 'emoji-picker-element';


	const id = ref()
	const ws = ref(null);
	const input = ref('');
	const messages = ref([]);
	const isOpen = ref('');
	const activeConnections = ref(0);
	const activeUsers = ref();
	const isList = ref(false)
	const showEmojiPicker = ref(false)

	const messageContainer = ref(null);

	const scrollToBottom = () =>  {
		nextTick(() => {
			const container = messageContainer.value;
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
  });
	};

	const addEmoji = (emoji) => {
		input.value += emoji.detail.unicode;
		showEmojiPicker.value = false;
	}

	onMounted(() => {
		if (localStorage.getItem('userName') == '' || localStorage.getItem('userName') == null || localStorage.getItem('userName') == 'null') {
			const userName = prompt('사용할 이름을 입력해주세요.');
			localStorage.setItem('userName', userName);
		}

		if (localStorage.getItem('userName') == '' || localStorage.getItem('userName') == null || localStorage.getItem('userName') == 'null') {
			alert('사용자 이름을 반드시 입력해주세요.')
			window.location.reload()
		}

		id.value = localStorage.getItem('userName') || null;
		ws.value = new WebSocket(`ws://localhost:18852/ws/${id.value}`);

		ws.value.onopen = () => {
			console.log('웹소켓 연결');
			isOpen.value = true;
		};

		ws.value.onmessage = (e) => {
			const message = JSON.parse(e.data);
			if (message.type === 'active_connections') {
				activeUsers.value = message.users
				activeConnections.value = message.count;
			} else {
				messages.value.push({ id: message.id, text: message.data });
			}
		};

		ws.value.onerror = (error) => {
			console.error('웹소켓 에러:', error);
			isOpen.value = false
		};

		ws.value.onclose = (event) => {
			console.log('웹소켓 연결 닫힘:', event);
		};

		watch(messages.value, () => {
			scrollToBottom();
		});
	});

	const sendMessage = () => {
		if(input.value !== '') {
			ws.value.send(input.value);
			input.value = ''
		}
	};

</script>

<template>
	<div style="height: 90%;">
		<div>
			채팅방 
			<span v-if="activeConnections > 0" style="margin-left: 5px;">
				({{ activeConnections }}명 접속 중)
			</span>
		</div>
		<div class="user-list-btn">
			<label class="font-semibold text-xl text-gray" @click="isList = !isList">
				접속자 확인 ▼
			</label>
			<div v-show="isList" class="dropdown-menu">
				<div v-for="(user, index) in activeUsers" :key="index" class="user-div">
					{{ index + 1 }}. {{ user }}
				</div>
			</div>
		</div>
		<div style="margin-top: 10px;">
			<span v-if="isOpen == true">
				연결되었습니다.
			</span>
			<span v-else-if="isOpen == false">
				연결에 실패했습니다.
			</span>
			<span v-else>
				연결중...
			</span>
		</div>
    <div class="message-container" ref="messageContainer">
			<div v-for="message in messages" :key="message.text" :class="{ 'text-right': message.id === id, 'text-left': message.id !== id && message.id != 'system', 'text-center': message.id == 'system' }">
				<strong>{{ message.id }}</strong> 
				<div :class="{ 'paddingTop': message.id != 'system' }">
					<span :class="{ 'own-message': message.id === id, 'other-message': message.id !== id && message.id != 'system', 'center-message': message.id == 'system' }">
						{{ message.text }} 
					</span>
				</div>
			</div>
		</div>
  </div>
	<div style="display: flex; justify-content: center; align-items: center;">
		<input v-model="input" @keyup.enter="sendMessage" placeholder="메세지를 입력하세요." />
		<button @click="showEmojiPicker = !showEmojiPicker">😀</button>
		<div v-if="showEmojiPicker" class="emoji-picker-popup">
			<emoji-picker @emoji-click="addEmoji"></emoji-picker>
		</div>
		<button class="submit-btn" @click="sendMessage">
			전송
		</button>
	</div>
</template>

<style scoped>
	@import '../assets/style.css'
</style>