document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    let messages = []; // Array to store the entire conversation history

    const appendMessage = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.innerText = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageElement;
    };

    const toggleInput = (enabled) => {
        sendBtn.disabled = !enabled;
        userInput.disabled = !enabled;
        if (enabled) {
            userInput.focus();
        }
    };

    const sendMessage = async () => {
        const userText = userInput.value.trim();
        if (!userText) return;

        appendMessage(userText, 'user-message');
        userInput.value = '';
        messages.push({ role: 'user', content: userText });

        // --- Create and show typing indicator ---
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('message', 'bot-message', 'typing-indicator');
        typingIndicator.innerHTML = `<span></span><span></span><span></span>`;
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;
        toggleInput(false);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ messages: messages }),
            });

            const data = await response.json();

            // --- Remove typing indicator ---
            chatBox.removeChild(typingIndicator);

            if (data.error) {
                appendMessage(`Error: ${data.error}`, 'bot-message');
            } else {
                const assistantMessage = data.reply;
                messages.push(assistantMessage);
                if (assistantMessage.content) {
                    appendMessage(assistantMessage.content, 'bot-message');
                }
            }

        } catch (error) {
            // --- Remove typing indicator on error ---
            if (chatBox.contains(typingIndicator)) {
                chatBox.removeChild(typingIndicator);
            }
            console.error('Error:', error);
            appendMessage('Error: Could not connect to the server.', 'bot-message');
        } finally {
            toggleInput(true);
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});