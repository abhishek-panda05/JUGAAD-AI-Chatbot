document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const suggestionChips = document.querySelectorAll('.chip');

    // Variables
    let isProcessing = false;

    // Initialize the chat with a greeting
    fetchGreeting();

    // Event Listeners
    chatForm.addEventListener('submit', handleSubmit);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    });

    // Add event listeners to suggestion chips
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', function() {
            const suggestion = this.getAttribute('data-suggestion');
            userInput.value = suggestion;
            userInput.focus();
        });
    });

    // Functions
    function fetchGreeting() {
        showTypingIndicator();
        
        fetch('https://web-production-a76fe.up.railway.app/api/greeting')
            .then(response => response.json())
            .then(data => {
                removeTypingIndicator();
                if (data.greeting) {
                    addBotMessage(data.greeting);
                } else {
                    addBotMessage("Namaste! I'm JUGAAD, your personal shopping assistant. I'm here to help you save money with the best deals and coupons. What would you like to shop for today? 🎉");
                }
            })
            .catch(error => {
                console.error('Error fetching greeting:', error);
                removeTypingIndicator();
                addBotMessage("Namaste! I'm JUGAAD, your personal shopping assistant. I'm here to help you save money with the best deals and coupons. What would you like to shop for today? 🎉");
            });
    }

    function handleSubmit(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message || isProcessing) return;
        
        // Add user message to chat
        addUserMessage(message);
        
        // Clear input
        userInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Set processing flag
        isProcessing = true;
        
        // Send message to server
        fetch('https://web-production-a76fe.up.railway.app/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            if (data.response) {
                addBotMessage(data.response);
            } else {
                addBotMessage("I'm sorry, I couldn't process your request. Please try again.");
            }
            isProcessing = false;
        })
        .catch(error => {
            console.error('Error sending message:', error);
            removeTypingIndicator();
            addBotMessage("I'm sorry, there was an error processing your request. Please try again.");
            isProcessing = false;
        });
    }

    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'user-message');
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        
        const paragraphElement = document.createElement('p');
        paragraphElement.textContent = message;
        
        contentElement.appendChild(paragraphElement);
        messageElement.appendChild(contentElement);
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'bot-message');
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('message-content');
        
        // Check if the message contains coupon information
        if (message.includes('🏷️ CODE:') || message.includes('💰 DISCOUNT:')) {
            // Format coupon message
            const formattedMessage = formatCouponMessage(message);
            contentElement.innerHTML = formattedMessage;
        } else {
            const paragraphElement = document.createElement('p');
            paragraphElement.textContent = message;
            contentElement.appendChild(paragraphElement);
        }
        
        messageElement.appendChild(contentElement);
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    function formatCouponMessage(message) {
        // Split the message by newlines
        const lines = message.split('\n');
        let formattedHtml = '';
        
        // Process each line
        lines.forEach(line => {
            if (line.startsWith('🏷️ CODE:')) {
                const code = line.replace('🏷️ CODE:', '').trim();
                formattedHtml += `<div class="coupon-code" onclick="copyToClipboard('${code}')">${code}</div>`;
            } else if (line.startsWith('💰 DISCOUNT:') || 
                       line.startsWith('🛍️ STORE:') || 
                       line.startsWith('📝 DETAILS:') || 
                       line.startsWith('⏰ VALID TILL:') || 
                       line.startsWith('💡 TIP:')) {
                const icon = line.charAt(0);
                const text = line.substring(2).trim();
                const label = line.split(':')[0].substring(2).trim();
                formattedHtml += `<p><i class="fas fa-${getIconClass(icon)}"></i> <strong>${label}:</strong> ${text.substring(text.indexOf(':') + 1).trim()}</p>`;
            } else {
                formattedHtml += `<p>${line}</p>`;
            }
        });
        
        return formattedHtml;
    }

    function getIconClass(icon) {
        const iconMap = {
            '💰': 'money-bill',
            '🛍️': 'shopping-bag',
            '📝': 'file-alt',
            '⏰': 'clock',
            '💡': 'lightbulb'
        };
        
        return iconMap[icon] || 'tag';
    }

    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'bot-message');
        typingElement.id = 'typing-indicator';
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('typing-indicator');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            contentElement.appendChild(dot);
        }
        
        typingElement.appendChild(contentElement);
        chatMessages.appendChild(typingElement);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add copy to clipboard functionality
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Create a temporary notification
            const notification = document.createElement('div');
            notification.textContent = 'Coupon code copied!';
            notification.classList.add('copy-notification');
            document.body.appendChild(notification);
            
            // Remove notification after animation
            setTimeout(() => {
                notification.classList.add('show');
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => {
                        notification.remove();
                    }, 300);
                }, 1500);
            }, 10);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    };
}); 
