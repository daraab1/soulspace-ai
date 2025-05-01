from flask import Flask, render_template_string, request, jsonify, session
from utils.rag import get_response
import secrets
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Ensure database directory exists
Path("database").mkdir(exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SoulSpace Therapist</title>
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #333;
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 250px;
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            overflow-y: auto;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            max-width: calc(100% - 250px);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .chat-container { 
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            flex: 1;
            overflow-y: auto;
            padding: 20px; 
            margin-bottom: 20px;
        }
        .message { 
            margin: 10px 0;
            padding: 12px 15px; 
            border-radius: 18px; 
            max-width: 80%; 
            line-height: 1.4;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message { 
            background: #e3f2fd;
            margin-left: auto; 
            border-bottom-right-radius: 5px;
        }
        .bot-message { 
            background: #f1f1f1; 
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        #input-box { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 25px; 
            font-size: 16px;
            box-sizing: border-box;
        }
        #typing-indicator {
            color: #666; 
            font-style: italic;
            padding: 10px; 
            display: none;
        }
        .session-item {
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        .session-item:hover {
            background: #34495e;
        }
        .session-item.active {
            border-left: 3px solid #3498db;
            background: rgba(52, 152, 219, 0.1);
            font-weight: bold;
        }
        .new-session-btn {
            background: #4a6fa5;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
            width: 100%;
        }
        .new-session-btn:hover {
            background: #3a5a80;
        }
        .clear-history-btn {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
            width: 100%;
            margin-top: 10px;
        }
        .clear-history-btn:hover {
            background: #c0392b;
        }
        .breathing-btn {
            background: #5d9c59;
            color: white;
            border: none;
            padding: 12px 20px; /* Larger padding */
            border-radius: 20px;
            cursor: pointer;
            font-size: 16px; /* Larger font */
            transition: all 0.3s;
            margin-left: 10px;
        }
        .breathing-btn:hover {
            background: #4a7d45;
            transform: scale(1.05); /* Slight grow effect */
        }
        .countdown {
            font-size: 2em; /* Much larger countdown */
            text-align: center;
            padding: 15px;
            color: #5d9c59;
            font-weight: bold;
            margin: 10px 0;
        }
        .breathing-instruction {
            font-size: 1.2em; /* Larger instructions */
            font-weight: bold;
            margin: 10px 0;
            color: #2c3e50;
        }
        .buttons-container {
            display: flex;
            gap: 10px;
        }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar">
        <h2>Chat History</h2>
        <div id="sessions-list">
            <!-- Sessions will appear here -->
        </div>
        <button class="new-session-btn" id="newSessionBtn">+ New Session</button>
        <button class="clear-history-btn" id="clearHistoryBtn">Clear All History</button>
    </div>

    <div class="main-content">
        <div class="header">
            <h1>SoulSpace AI</h1>
            <div class="buttons-container">
                <button class="breathing-btn" id="breathingBtn"> Breathing Exercise</button>
            </div>
        </div>
        <div class="chat-container" id="chat">
            <!-- Current chat messages appear here -->
        </div>
        <input type="text" id="input-box" placeholder="How are you feeling today?" autofocus>
        <p id="typing-indicator">Therapist is thinking...</p>
    </div>

    <script>
        // Chat Manager Class
        class ChatManager {
            constructor() {
                this.currentSessionId = null;
                this.sessions = JSON.parse(localStorage.getItem('soulspaceSessions')) || {};
                
                // Clear history if requested via URL
                if (new URLSearchParams(window.location.search).has('reset')) {
                    this.clearAllHistory();
                    window.history.replaceState({}, document.title, window.location.pathname);
                }
                
                this.init();
            }
            
            init() {
                if (Object.keys(this.sessions).length === 0) {
                    this.createNewSession();
                } else {
                    // Load most recent session
                    const sessions = Object.values(this.sessions).sort((a, b) => 
                        new Date(b.createdAt) - new Date(a.createdAt));
                    this.currentSessionId = sessions[0].id;
                    this.loadSession(this.currentSessionId);
                }
            }
            
            createNewSession() {
                // Clear chat display immediately
                document.getElementById('chat').innerHTML = '';
                
                // Create new session ID
                const sessionId = 'session-' + Date.now();
                this.currentSessionId = sessionId;
                
                // Create fresh session object
                this.sessions[sessionId] = {
                    id: sessionId,
                    title: 'Session ' + (Object.keys(this.sessions).length + 1),
                    messages: [],
                    createdAt: new Date().toISOString()
                };
                
                // Save and update UI
                this.saveSessions();
                this.renderSessionsList();
                
                // Clear server-side memory
                fetch('/new_session', { 
                    method: 'POST'
                }).catch(err => console.error('Error clearing server memory:', err));
                
                // Add welcome message
                this.addMessage("Welcome to a new session. How can I help you today?", false);
                
                return sessionId;
            }
            
            clearAllHistory() {
                localStorage.removeItem('soulspaceSessions');
                this.sessions = {};
                this.createNewSession();
            }
            
            saveCurrentSession() {
                if (this.currentSessionId && this.sessions[this.currentSessionId]) {
                    const chatDiv = document.getElementById('chat');
                    this.sessions[this.currentSessionId].messages = Array.from(chatDiv.children)
                        .map(el => ({
                            html: el.innerHTML,
                            isUser: el.classList.contains('user-message')
                        }));
                    this.saveSessions();
                }
            }
            
            loadSession(sessionId) {
                // Save current session before switching
                this.saveCurrentSession();
                
                // Set new session ID
                this.currentSessionId = sessionId;
                const chatDiv = document.getElementById('chat');
                chatDiv.innerHTML = '';
                
                // Load messages for this session
                const session = this.sessions[sessionId];
                if (session && session.messages) {
                    session.messages.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = `message ${msg.isUser ? 'user-message' : 'bot-message'}`;
                        div.innerHTML = msg.html;
                        chatDiv.appendChild(div);
                    });
                }
                
                // Scroll to bottom and update UI
                chatDiv.scrollTop = chatDiv.scrollHeight;
                this.updateActiveSession();
            }
            
            renderSessionsList() {
                const listDiv = document.getElementById('sessions-list');
                listDiv.innerHTML = '';
                
                // Sort sessions by date (newest first)
                Object.values(this.sessions)
                    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
                    .forEach(session => {
                        const item = document.createElement('div');
                        item.className = 'session-item';
                        item.textContent = session.title;
                        item.dataset.sessionId = session.id;
                        item.addEventListener('click', () => this.loadSession(session.id));
                        listDiv.appendChild(item);
                    });
                
                this.updateActiveSession();
            }
            
            updateActiveSession() {
                document.querySelectorAll('.session-item').forEach(item => {
                    item.classList.toggle('active', item.dataset.sessionId === this.currentSessionId);
                });
            }
            
            saveSessions() {
                localStorage.setItem('soulspaceSessions', JSON.stringify(this.sessions));
            }
            
            addMessage(content, isUser) {
                const chatDiv = document.getElementById('chat');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                
                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                messageDiv.innerHTML = `
                    <strong>${isUser ? 'You' : 'Therapist'}:</strong> ${content}
                    <div class="timestamp">${timestamp}</div>
                `;
                
                chatDiv.appendChild(messageDiv);
                chatDiv.scrollTop = chatDiv.scrollHeight;
                
                // Update session title if first user message
                if (isUser && this.sessions[this.currentSessionId].messages.length === 0) {
                    this.sessions[this.currentSessionId].title = 
                        content.length > 25 ? content.substring(0, 25) + '...' : content;
                    this.renderSessionsList();
                }
                
                // Save message to session
                this.sessions[this.currentSessionId].messages.push({
                    html: messageDiv.innerHTML,
                    isUser
                });
                this.saveSessions();
                
                return messageDiv;
            }
        }

        // Initialize chat manager
        const chatManager = new ChatManager();

        // Event Listeners
        document.getElementById('newSessionBtn').addEventListener('click', () => {
            if (confirm('Start a fresh session? Your current chat will be saved.')) {
                chatManager.createNewSession();
            }
        });

        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            if (confirm('Permanently delete ALL chat history?')) {
                chatManager.clearAllHistory();
            }
        });

        document.getElementById('input-box').addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                const userMessage = e.target.value.trim();
                if (!userMessage) return;
                
                e.target.value = '';
                chatManager.addMessage(userMessage, true);
                
                // Show typing indicator
                document.getElementById('typing-indicator').style.display = 'block';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: userMessage })
                    }).then(res => res.json());
                    
                    document.getElementById('typing-indicator').style.display = 'none';
                    chatManager.addMessage(response.response, false);
                } catch (error) {
                    document.getElementById('typing-indicator').style.display = 'none';
                    chatManager.addMessage("I'm having trouble connecting. Please try again.", false);
                    console.error('Error:', error);
                }
            }
        });

        // Enhanced Breathing Exercise
        document.getElementById('breathingBtn').addEventListener('click', () => {
            const steps = [
                {text: " Let's begin the 4-7-8 breathing exercise", duration: 1},
                {text: " First, empty your lungs completely", duration: 1},
                {text: " Breathe in quietly through your nose for 4 seconds", duration: 4},
                {text: " Hold your breath for 7 seconds", duration: 7},
                {text: " Exhale completely through your mouth for 8 seconds", duration: 8},
                {text: " Let's repeat one more time", duration: 1},
                {text: " Breathe in for 4 seconds", duration: 4},
                {text: " Hold for 7 seconds", duration: 7},
                {text: " Exhale for 8 seconds", duration: 8}
            ];
            
            let currentStep = 0;
            
            function runStep() {
                if (currentStep >= steps.length) {
                    chatManager.addMessage(" Great job completing the breathing exercise! How do you feel now?", false);
                    return;
                }
                
                const step = steps[currentStep];
                const messageDiv = chatManager.addMessage(`<div class="breathing-instruction">${step.text}</div>`, false);
                
                // Create enhanced countdown
                const countdownDiv = document.createElement('div');
                countdownDiv.className = 'bot-message message';
                countdownDiv.innerHTML = `<div class="countdown">${step.duration}</div>`;
                document.getElementById('chat').appendChild(countdownDiv);
                
                // Add breathing animation effect
                if (step.text.includes("Breathe in")) {
                    countdownDiv.style.animation = "pulseIn 1s infinite";
                } else if (step.text.includes("Exhale")) {
                    countdownDiv.style.animation = "pulseOut 1s infinite";
                }
                
                let remaining = step.duration;
                const countdown = setInterval(() => {
                    remaining--;
                    countdownDiv.querySelector('.countdown').textContent = remaining;
                    if (remaining <= 0) {
                        clearInterval(countdown);
                        currentStep++;
                        setTimeout(runStep, 1000);
                    }
                }, 1000);
            }
            
            runStep();
        });

        // Add breathing animations to style
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulseIn {
                0% { transform: scale(1); background-color: #f1f1f1; }
                50% { transform: scale(1.05); background-color: #e3f7f1; }
                100% { transform: scale(1); background-color: #f1f1f1; }
            }
            @keyframes pulseOut {
                0% { transform: scale(1); background-color: #f1f1f1; }
                50% { transform: scale(0.95); background-color: #f7e3e3; }
                100% { transform: scale(1); background-color: #f1f1f1; }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    response = get_response(data['message'])
    return jsonify({"response": response})

@app.route('/new_session', methods=['POST'])
def new_session():
    from utils.rag import memory
    memory.clear()  
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)