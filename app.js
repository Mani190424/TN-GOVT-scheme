// TN GOVT SCHEME BOT - JavaScript
const APP = {
    language: 'English',
    isListening: false,
    chatHistory: [],
    
    init() {
        this.attachEventListeners();
        this.loadLanguagePreference();
        this.setupVoice();
    },
    
    attachEventListeners() {
        const sendBtn = document.getElementById('send-btn');
        const voiceBtn = document.getElementById('voice-btn');
        const chatInput = document.getElementById('chat-input');
        const languageToggle = document.getElementById('language-toggle');
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        
        if (sendBtn) sendBtn.addEventListener('click', () => this.sendMessage());
        if (voiceBtn) voiceBtn.addEventListener('click', () => this.toggleVoice());
        if (chatInput) chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        if (languageToggle) languageToggle.addEventListener('click', () => this.toggleLanguage());
        if (darkModeToggle) darkModeToggle.addEventListener('click', () => this.toggleDarkMode());
    },
    
    setupVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.language = this.language === 'Tamil' ? 'ta-IN' : 'en-IN';
            this.recognition.onstart = () => {
                const btn = document.getElementById('voice-btn');
                if (btn) btn.classList.add('recording');
            };
            this.recognition.onend = () => {
                const btn = document.getElementById('voice-btn');
                if (btn) btn.classList.remove('recording');
            };
            this.recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        transcript += event.results[i][0].transcript;
                    }
                }
                if (transcript) {
                    const input = document.getElementById('chat-input');
                    if (input) input.value = transcript;
                }
            };
        }
    },
    
    toggleVoice() {
        if (!this.recognition) {
            alert('Voice not supported in your browser');
            return;
        }
        
        if (this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        } else {
            this.recognition.start();
            this.isListening = true;
        }
    },
    
    sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input) return;
        
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.displayMessage(message, 'user');
        input.value = '';
        
        // Get AI response
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                language: this.language
            })
        })
        .then(response => response.json())
        .then(data => {
            this.displayMessage(data.response, 'bot');
            this.playAudio(data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            this.displayMessage('Sorry, I encountered an error. Please try again.', 'bot');
        });
    },
    
    displayMessage(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${sender}`;
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.chatHistory.push({ text, sender, timestamp: new Date() });
    },
    
    playAudio(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = this.language === 'Tamil' ? 'ta-IN' : 'en-IN';
            speechSynthesis.speak(utterance);
        }
    },
    
    toggleLanguage() {
        this.language = this.language === 'English' ? 'Tamil' : 'English';
        localStorage.setItem('language', this.language);
        
        const toggle = document.getElementById('language-toggle');
        if (toggle) {
            toggle.textContent = this.language === 'English' ? '🌐 English | தமிழ்' : '🌐 தமிழ் | English';
        }
        
        if (this.recognition) {
            this.recognition.language = this.language === 'Tamil' ? 'ta-IN' : 'en-IN';
        }
    },
    
    loadLanguagePreference() {
        const saved = localStorage.getItem('language');
        if (saved) {
            this.language = saved;
            const toggle = document.getElementById('language-toggle');
            if (toggle) {
                toggle.textContent = this.language === 'English' ? '🌐 English | தமிழ்' : '🌐 தமிழ் | English';
            }
        }
    },
    
    toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    },
    
    checkEligibility() {
        fetch('/api/check-eligibility', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            this.displayEligibilityResults(data);
        })
        .catch(error => console.error('Error:', error));
    },
    
    displayEligibilityResults(data) {
        const container = document.getElementById('eligibility-results');
        if (!container) return;
        
        let html = '<div class="card">';
        
        if (data.eligible && data.eligible.length > 0) {
            html += '<h3 style="color: var(--success);">✓ Eligible Schemes</h3>';
            html += '<div class="scheme-grid">';
            data.eligible.forEach(scheme => {
                html += `
                    <div class="scheme-card">
                        <div class="scheme-name">${scheme.name}</div>
                        <div class="scheme-benefit">${scheme.benefit}</div>
                        <a href="/scheme/${scheme.id}" class="btn btn-secondary btn-sm">View Details</a>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        if (data.not_eligible && data.not_eligible.length > 0) {
            html += '<h3 style="color: var(--danger); margin-top: 2rem;">✗ Not Eligible</h3>';
            html += '<div class="scheme-grid">';
            data.not_eligible.forEach(scheme => {
                html += `
                    <div class="scheme-card">
                        <div class="scheme-name">${scheme.name}</div>
                        <div style="color: #ef4444; font-size: 0.9rem;">
                            ${scheme.reasons.join('<br>')}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    },
    
    toggleFavorite(schemeId) {
        fetch(`/api/favorite/${schemeId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            const btn = event.target;
            if (data.status === 'added') {
                btn.classList.add('favorited');
                btn.textContent = '❤️ Favorited';
            } else {
                btn.classList.remove('favorited');
                btn.textContent = '🤍 Add to Favorites';
            }
        })
        .catch(error => console.error('Error:', error));
    },
    
    submitFeedback() {
        const rating = document.getElementById('rating');
        const feedbackText = document.getElementById('feedback-text');
        const isHelpful = document.getElementById('is-helpful');
        
        if (!rating || !feedbackText) return;
        
        fetch('/api/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rating: rating.value,
                feedback: feedbackText.value,
                is_helpful: isHelpful ? isHelpful.checked : false
            })
        })
        .then(response => response.json())
        .then(data => {
            alert('Thank you for your feedback!');
            const form = document.getElementById('feedback-form');
            if (form) form.reset();
        })
        .catch(error => console.error('Error:', error));
    },
    
    updateProfile() {
        const form = document.getElementById('profile-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        fetch('/api/update-profile', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                alert('Profile updated successfully!');
                location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    APP.init();
    
    // Load dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
});