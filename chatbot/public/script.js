
document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    const appendMessage = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        messageElement.innerText = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const sendMessage = async () => {
        const message = userInput.value.trim();
        if (message) {
            appendMessage(message, 'user');
            userInput.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });

                const data = await response.json();
                appendMessage(data.reply, 'bot');
            } catch (error) {
                console.error('Error:', error);
                appendMessage('Error: Could not connect to the server.', 'bot');
            }
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
