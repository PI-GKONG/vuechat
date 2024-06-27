<script setup>
	import '../assets/style.css'
	import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue';
	import 'emoji-picker-element';

	const id = ref('');
	const ws = ref(null);
	const input = ref('');
	const messages = ref([]);
	const isOpen = ref(false);
	const activeConnections = ref(0);
	const activeUsers = ref([]);
	const isList = ref(false);
	const showEmojiPicker = ref(false);

	const messageContainer = ref(null);
	let observer = null;

	const scrollToBottom = () => {
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
	};

	const markMessageAsRead = (message) => {
		console.log(`markMessageAsRead ${document.visibilityState}`)
		if (document.visibilityState === 'visible' && message.unreadCount > 0 && message.id != id.value && !message.isRead) {
			ws.value.send(JSON.stringify({ type: 'read', messageId: message.messageId }));
			message.isRead = true
		}
	};

	const observeMessages = () => {
		if (observer) {
			observer.disconnect();
		}

		observer = new IntersectionObserver((entries) => {
			entries.forEach(entry => {
				if (entry.isIntersecting) {
					const messageId = entry.target.dataset.messageId;
					const message = messages.value.find(msg => msg.messageId == messageId);
					if (message && message.unreadCount > 0) {
						markMessageAsRead(message);
					}
				}
			});
		});

		messages.value.forEach(message => {
			const element = document.querySelector(`[data-message-id="${message.messageId}"]`);
			if (element) {
				observer.observe(element);
			}
		});
	};

	const handleVisibilityChange = () => {
		console.log(`handleVisibilityChange ${document.visibilityState}`)
		if (document.visibilityState === 'visible') {
			observeMessages();
		} else if (observer) {
			observer.disconnect();
		}
	};

	onMounted(() => {
		if (!localStorage.getItem('userName')) {
			const userName = prompt('사용할 이름을 입력해주세요.');
			if (userName) {
				localStorage.setItem('userName', userName);
			} else {
				alert('사용자 이름을 반드시 입력해주세요.');
				window.location.reload();
			}
		}

		id.value = localStorage.getItem('userName');
		ws.value = new WebSocket(`ws://222.114.53.153:18852/ws/${id.value}`);

		ws.value.onopen = () => {
			console.log('웹소켓 연결');
			isOpen.value = true;
		};

		ws.value.onmessage = (e) => {
			const message = JSON.parse(e.data);
			if (message.type === 'active_connections') {
				activeUsers.value = message.users;
				activeConnections.value = message.count;
			} else if (message.type === 'message' || message.type === 'system') {
				messages.value.push({ ...message, read: false, isRead: false });
			} else if (message.type === 'read') {
				const msg = messages.value.find(m => m.messageId === message.messageId);
				if (msg) {
					msg.unreadCount = message.unreadCount;
				}
			}
		};

		ws.value.onerror = (error) => {
			console.error('웹소켓 에러:', error);
			isOpen.value = false;
		};

		ws.value.onclose = (event) => {
			console.log('웹소켓 연결 닫힘:', event);
		};

		watch(messages.value, () => {
			scrollToBottom();
			if (document.visibilityState === 'visible') {
				nextTick(observeMessages);
			}
		});

		document.addEventListener('visibilitychange', handleVisibilityChange);
	});

	onBeforeUnmount(() => {
		document.removeEventListener('visibilitychange', handleVisibilityChange);
		if (observer) {
			observer.disconnect();
		}
	});

	const sendMessage = () => {
		if(input.value !== '') {
			const message = { type: 'message', data: input.value };
			ws.value.send(JSON.stringify(message));
			input.value = '';
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
    <div class="user-list-btn" style="text-align: center;">
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
      <span v-if="isOpen">
        연결되었습니다.
      </span>
      <span v-else-if="isOpen === false">
        연결에 실패했습니다.
      </span>
      <span v-else>
        연결중...
      </span>
    </div>
    <div class="message-container" ref="messageContainer">
      <div v-for="message in messages" :key="message.messageId" :class="{ 'text-right': message.id === id, 'text-left': message.id !== id && message.id != 'system', 'text-center': message.id == 'system' }" :data-message-id="message.messageId">
        <strong>{{ message.id }}</strong> 
        <div :class="{ 'paddingTop': message.id != 'system' }" 
					:style="{ display: message.id === 'system' ? 'block' : 'flex', 
										flexDirection: message.id !== 'system' && message.id !== id ? 'row' : message.id === id ? 'row-reverse' : 'none', 
										alignItems: 'center' }"
				>
					<span :class="{ 'own-message': message.id === id, 'other-message': message.id !== id && message.id != 'system', 'center-message': message.id == 'system' }">
						{{ message.data }} 
          </span>
					<span v-if="message.id != 'system' && message.unreadCount != 0" class="unread-count">{{ message.unreadCount }}</span>
        </div>
				<span>
					{{ message.time }}
				</span>
      </div>
    </div>
  </div>
  <div style="display: flex; justify-content: center; align-items: center; margin-top: 10px; position: relative;">
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

