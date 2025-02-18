       import { marked } from 'marked';
        let currentImagePath = null;
        const userId = 'user_' + Math.random().toString(36).substr(2, 9);

        // Load conversation history
        async function loadConversations() {
            try {
                const response = await fetch(`/get_conversations?user_id=${userId}`);
                const data = await response.json();
                const conversationList = document.getElementById('conversation-list');
                conversationList.innerHTML = '';
                
                data.history.forEach(msg => {
                    const chatBody = document.getElementById('chat-body');
                    const messageDiv = document.createElement('div');
                    messageDiv.classList.add('chat-message', msg.role);
                    messageDiv.innerHTML = marked.parse(msg.message);
                    chatBody.appendChild(messageDiv);
                });
            } catch (error) {
                console.error('Error loading conversations:', error);
            }
        }

        function closeAttachmentPreview() {
            document.getElementById('attachment-preview').classList.remove('active');
            document.getElementById('photo-input').value = '';
            document.getElementById('image-preview').innerHTML = '';
            currentImagePath = null;
        }

        // Handle file upload
        document.getElementById('photo-input').addEventListener('change', async function(e) {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/upload_image', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    currentImagePath = data.file_path;
                    
                    // Show image preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('image-preview').innerHTML = `
                            <img src="${e.target.result}" alt="Preview">
                        `;
                    };
                    reader.readAsDataURL(file);
                    
                    // Show attachment preview
                    document.getElementById('attachment-preview').classList.add('active');
                    document.getElementById('file-name').textContent = file.name;
                } catch (error) {
                    console.error('Error uploading file:', error);
                }
            }
        });

        // Send message with attachment
        async function sendAttachment() {
            const attachmentMessage = document.getElementById('attachment-message').value;
            if (!attachmentMessage.trim()) {
                alert('Please enter a message about the image.');
                return;
            }

            await sendMessageToServer(attachmentMessage, currentImagePath);
            
            // Reset attachment state
            closeAttachmentPreview();
        }

        // Send regular message
        async function sendMessage() {
            const userInput = document.getElementById('user-input');
            const message = userInput.value.trim();
            
            if (message === '') return;
            
            await sendMessageToServer(message);
            userInput.value = '';
        }

        // Send message to server
        async function sendMessageToServer(message, imagePath = null) {
            const chatBody = document.getElementById('chat-body');
            
            // Add user message to chat
            const userMessage = document.createElement('div');
            userMessage.classList.add('chat-message', 'user');
            userMessage.innerHTML = `<p>${message}</p>`;
            chatBody.appendChild(userMessage);

            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        message: message,
                        image_path: imagePath
                    })
                });

                const data = await response.json();
                
                // Add bot response to chat
                const botMessage = document.createElement('div');
                botMessage.classList.add('chat-message', 'bot');
                botMessage.innerHTML = `<p>${data.response}</p>`;
                chatBody.appendChild(botMessage);
                
                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
            } catch (error) {
                console.error('Error sending message:', error);
            }
        }

        // Allow sending message with Enter key
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Load initial conversations
        loadConversations();