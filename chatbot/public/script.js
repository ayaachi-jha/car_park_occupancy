document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Array to store the entire conversation history
    let messages = [];

    const appendMessage = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        messageElement.innerText = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const sendMessage = async () => {
        const userText = userInput.value.trim();
        if (userText) {
            appendMessage(userText, 'user');
            userInput.value = '';

            // Add user's message to the history
            messages.push({ role: 'user', content: userText });

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    // Send the entire message history
                    body: JSON.stringify({ messages: messages }),
                });

                const data = await response.json();
                
                if (data.error) {
                    appendMessage(data.error, 'bot');
                } else {
                    const assistantMessage = data.reply;
                    // Add assistant's response to the history
                    messages.push(assistantMessage);
                    appendMessage(assistantMessage.content, 'bot');
                }

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