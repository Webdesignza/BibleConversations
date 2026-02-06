/**
 * Bible Study Widget - Multi-Translation Voice AI Assistant
 * Embeddable voice agent for Bible translation conversations
 */

(function() {
    'use strict';
    
    console.log('=== Bible Study Widget Loading ===');
    
    const BibleWidget = {
        // Configuration
        apiBase: 'http://127.0.0.1:8009',
        
        // State
        isOpen: false,
        conversationActive: false,
        isProcessing: false,
        isSpeaking: false,
        isRecording: false,
        audioStream: null,
        mediaRecorder: null,
        audioChunks: [],
        sessionToken: null,
        analyser: null,
        silenceStart: null,
        recordingStartTime: 0,
        recordingTimeout: null,
        currentAudio: null,
        availableTranslations: [],
        currentTranslation: null,
        compareMode: false,
        selectedTranslationsForCompare: [],
        textMode: false,  // NEW: Toggle between voice and text input
        
        // Initialize
        init() {
            console.log('Initializing Bible Study Widget...');
            this.injectStyles();
            this.createButton();
            this.createPopup();
            this.loadTranslations();
            console.log('✓ Widget initialized');
        },
        
        // Load available translations
        async loadTranslations() {
            try {
                console.log('Loading translations...');
                const agentResp = await fetch(`${this.apiBase}/agent`);
                const html = await agentResp.text();
                const match = html.match(/SESSION_TOKEN.*?"([^"]+)"/);
                
                if (match) {
                    const tempToken = match[1];
                    const transResp = await fetch(`${this.apiBase}/api/translations/list`, {
                        headers: { 'Authorization': `Bearer ${tempToken}` }
                    });
                    
                    const data = await transResp.json();
                    
                    if (data.success && data.translations) {
                        this.availableTranslations = data.translations;
                        this.populateTranslationSelector();
                        
                        // Auto-select first translation
                        if (this.availableTranslations.length > 0) {
                            const firstTrans = this.availableTranslations[0];
                            this.currentTranslation = {
                                id: firstTrans.id,
                                name: firstTrans.name
                            };
                            
                            const select = document.getElementById('translation-select');
                            if (select) select.value = firstTrans.id;
                            
                            this.updateStatus(`Ready: ${firstTrans.name}. Click Start.`);
                            console.log('✓ Selected:', firstTrans.name);
                        }
                    }
                }
            } catch (error) {
                console.error('Failed to load translations:', error);
            }
        },
        
        // Populate translation dropdown
        populateTranslationSelector() {
            const select = document.getElementById('translation-select');
            if (!select) return;
            
            select.innerHTML = '';
            
            if (this.availableTranslations.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No translations available';
                select.appendChild(option);
                select.disabled = true;
                return;
            }
            
            this.availableTranslations.forEach(trans => {
                const option = document.createElement('option');
                option.value = trans.id;
                option.textContent = `${trans.name} (${trans.chunks} verses)`;
                select.appendChild(option);
            });
            
            select.disabled = false;
        },
        
        // Switch translation
        async switchTranslation(translationId = null, token = null) {
            const useToken = token || this.sessionToken;
            
            if (!useToken) {
                console.error('No session token available');
                return;
            }
            
            // Get translation ID from selector if not provided
            if (!translationId) {
                const select = document.getElementById('translation-select');
                translationId = select.value;
            }
            
            if (!translationId) return;
            
            try {
                console.log('Switching to translation:', translationId);
                
                const resp = await fetch(`${this.apiBase}/api/translations/switch`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${useToken}`
                    },
                    body: JSON.stringify({ translation_id: translationId })
                });
                
                const data = await resp.json();
                
                if (data.success) {
                    this.currentTranslation = {
                        id: data.translation_id,
                        name: data.translation_name
                    };
                    console.log('✓ Switched to:', data.translation_name);
                    
                    // Update selector if widget is open
                    const select = document.getElementById('translation-select');
                    if (select) {
                        select.value = translationId;
                    }
                } else {
                    console.error('Switch failed:', data.message);
                }
            } catch (error) {
                console.error('Failed to switch translation:', error);
            }
        },
        
        // Inject CSS
        injectStyles() {
            const styles = `
                #bible-btn {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                    color: white;
                    border: none;
                    border-radius: 50px;
                    padding: 15px 25px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(30, 58, 138, 0.4);
                    z-index: 9998;
                    transition: transform 0.3s;
                    font-family: 'Segoe UI', sans-serif;
                }
                
                #bible-btn:hover {
                    transform: translateY(-2px);
                }
                
                #bible-overlay {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 9999;
                    backdrop-filter: blur(5px);
                    align-items: center;
                    justify-content: center;
                }
                
                #bible-overlay.active {
                    display: flex;
                    animation: fadeIn 0.3s;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                #bible-popup {
                    background: white;
                    border-radius: 20px;
                    width: 80%;
                    max-width: 1400px;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                    animation: slideUp 0.3s;
                }
                
                @keyframes slideUp {
                    from { transform: translateY(50px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                
                .bible-header {
                    background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 20px 20px 0 0;
                    position: relative;
                }
                
                .bible-header h2 {
                    margin: 0;
                    font-size: 24px;
                }
                
                .bible-close {
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 20px;
                }
                
                .bible-content {
                    padding: 30px;
                    text-align: center;
                }
                
                .translation-selector {
                    margin-bottom: 15px;
                    text-align: left;
                }
                
                .translation-selector label {
                    display: block;
                    font-weight: 600;
                    color: #1E3A8A;
                    margin-bottom: 8px;
                    font-size: 14px;
                }
                
                #translation-select {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 14px;
                    background: white;
                    cursor: pointer;
                }
                
                #translation-select:focus {
                    outline: none;
                    border-color: #1E3A8A;
                }
                
                #compare-mode-btn {
                    width: 100%;
                    margin-bottom: 15px;
                }
                
                .bible-btn-action.active {
                    background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
                }
                
                #compare-selections {
                    text-align: left;
                    max-height: 200px;
                    overflow-y: auto;
                }
                
                #compare-selections label {
                    display: block;
                    padding: 8px;
                    margin-bottom: 5px;
                    border-radius: 5px;
                    transition: background 0.2s;
                    cursor: pointer;
                }
                
                #compare-selections label:hover {
                    background: rgba(30, 58, 138, 0.1);
                }
                
                #compare-selections input[type="checkbox"] {
                    margin-right: 8px;
                    cursor: pointer;
                }
                
                .bible-avatar {
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 5px solid #1E3A8A;
                    transition: box-shadow 0.3s ease;
                    margin: 15px 0;
                }

                .bible-avatar.listening {
                    border-color: #10b981;
                    animation: listeningGlow 2s ease-in-out infinite;
                }

                .bible-avatar.talking {
                    border-color: #D97706;
                    animation: talkingGlow 0.6s ease-in-out infinite;
                }

                @keyframes listeningGlow {
                    0%, 100% { 
                        box-shadow: 0 0 20px rgba(16, 185, 129, 0.4),
                                    0 0 40px rgba(16, 185, 129, 0.2);
                    }
                    50% { 
                        box-shadow: 0 0 30px rgba(16, 185, 129, 0.6),
                                    0 0 60px rgba(16, 185, 129, 0.3);
                    }
                }

                @keyframes talkingGlow {
                    0%, 100% { 
                        box-shadow: 0 0 25px rgba(217, 119, 6, 0.5),
                                    0 0 50px rgba(217, 119, 6, 0.3);
                    }
                    50% { 
                        box-shadow: 0 0 35px rgba(217, 119, 6, 0.7),
                                    0 0 70px rgba(217, 119, 6, 0.4);
                    }
                }
                
                .bible-status {
                    margin: 15px 0;
                    padding: 15px;
                    background: #f0f9ff;
                    border-radius: 10px;
                    min-height: 50px;
                }
                
                .bible-controls {
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                    margin-bottom: 15px;
                }
                
                .bible-btn-action {
                    background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: transform 0.3s;
                }
                
                .bible-btn-action:hover {
                    transform: translateY(-2px);
                }
                
                .bible-btn-action:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .bible-btn-action.secondary {
                    background: #e5e7eb;
                    color: #333;
                }
                
                .bible-transcript {
                    margin-top: 15px;
                    max-height: 200px;
                    overflow-y: auto;
                    text-align: left;
                }
                
                #bible-comparison-display {
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                
                #bible-comparison-display .comparison-summary {
                    font-size: 14px;
                    color: #374151;
                    margin-bottom: 15px;
                    padding: 10px;
                    background: #f0f9ff;
                    border-radius: 8px;
                    border-left: 4px solid #1E3A8A;
                }
                
                .transcript-msg {
                    margin: 10px 0;
                    padding: 10px;
                    border-radius: 8px;
                }
                
                .transcript-msg.user {
                    background: #dbeafe;
                    text-align: right;
                }
                
                .transcript-msg.agent {
                    background: #fef3c7;
                }
                
                .comparison-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                    font-size: 13px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    background: white;
                }
                
                .comparison-table th {
                    background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    border: 1px solid #ddd;
                    vertical-align: top;
                }
                
                .comparison-table td {
                    padding: 10px 12px;
                    border: 1px solid #ddd;
                    vertical-align: top;
                    line-height: 1.6;
                    text-align: left;
                }
                
                .comparison-table tr:nth-child(even) {
                    background: #f9fafb;
                }
                
                .comparison-table tr:hover {
                    background: #f0f9ff;
                }
                
                .comparison-table td:first-child {
                    font-weight: 600;
                    color: #1E3A8A;
                    white-space: nowrap;
                    width: 120px;
                }
                
                .comparison-table td:not(:first-child) {
                    width: auto;
                    min-width: 200px;
                }
                
                .input-mode-toggle {
                    display: flex;
                    gap: 5px;
                    justify-content: center;
                    margin-bottom: 15px;
                    padding: 5px;
                    background: #f3f4f6;
                    border-radius: 10px;
                }
                
                .mode-btn {
                    flex: 1;
                    padding: 8px 15px;
                    border: none;
                    background: transparent;
                    color: #6b7280;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s;
                }
                
                .mode-btn.active {
                    background: white;
                    color: #1E3A8A;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .mode-btn:hover:not(.active) {
                    background: rgba(255,255,255,0.5);
                }
                
                .text-input-container {
                    display: none;
                    margin-bottom: 15px;
                }
                
                .text-input-container.active {
                    display: block;
                }
                
                #bible-text-input {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 14px;
                    font-family: 'Segoe UI', sans-serif;
                    resize: vertical;
                    min-height: 60px;
                }
                
                #bible-text-input:focus {
                    outline: none;
                    border-color: #1E3A8A;
                }
                
                .text-send-btn {
                    margin-top: 10px;
                    width: 100%;
                }
            `;
            
            const style = document.createElement('style');
            style.textContent = styles;
            document.head.appendChild(style);
        },
        
        // Create button
        createButton() {
            const btn = document.createElement('button');
            btn.id = 'bible-btn';
            btn.textContent = '📖 Talk to Bible AI';
            btn.onclick = () => this.open();
            document.body.appendChild(btn);
        },
        
        // Create popup
        createPopup() {
            const overlay = document.createElement('div');
            overlay.id = 'bible-overlay';
            overlay.innerHTML = `
                <div id="bible-popup">
                    <div class="bible-header">
                        <h2>📖 Bible Study Assistant</h2>
                        <button class="bible-close" onclick="BibleWidget.close()">×</button>
                    </div>
                    <div class="bible-content">
                        <div class="translation-selector">
                            <label for="translation-select">Select Translation:</label>
                            <select id="translation-select" onchange="BibleWidget.onTranslationChange()">
                                <option value="">Loading translations...</option>
                            </select>
                        </div>
                        
                        <button id="compare-mode-btn" 
                                class="bible-btn-action secondary" 
                                onclick="BibleWidget.toggleCompareMode()">
                            🔄 Compare Translations
                        </button>
                        
                        <div id="compare-selections" style="display:none;"></div>
                        
                        <div class="input-mode-toggle">
                            <button class="mode-btn active" onclick="BibleWidget.toggleInputMode('voice')">
                                🎤 Voice
                            </button>
                            <button class="mode-btn" onclick="BibleWidget.toggleInputMode('text')">
                                ⌨️ Text
                            </button>
                        </div>
                        
                        <div class="text-input-container" id="text-input-container">
                            <textarea id="bible-text-input" placeholder="Type your Bible question here..."></textarea>
                            <button class="bible-btn-action text-send-btn" onclick="BibleWidget.sendTextQuestion()">
                                📤 Send Question
                            </button>
                        </div>
                        
                        <img id="bible-avatar" class="bible-avatar"
                             src="https://bible-conversations-production.up.railway.app/static/images/bible-comparisons.png" 
                             alt="Bible AI">
                        <div id="bible-status" class="bible-status">
                            Select a translation and click Start
                        </div>
                        <div id="bible-comparison-display" style="display:none; margin-bottom: 15px;"></div>
                        <div class="bible-controls">
                            <button id="start-btn" class="bible-btn-action" 
                                    onclick="BibleWidget.startConversation()">
                                🎤 Start
                            </button>
                            <button id="end-btn" class="bible-btn-action secondary" 
                                    onclick="BibleWidget.endConversation()" disabled>
                                🛑 End
                            </button>
                        </div>
                        <div id="bible-transcript" class="bible-transcript" style="display:none;"></div>
                    </div>
                </div>
            `;
            
            overlay.onclick = (e) => {
                if (e.target === overlay) this.close();
            };
            
            document.body.appendChild(overlay);
        },
        
        // Handle translation dropdown change
        onTranslationChange() {
            const select = document.getElementById('translation-select');
            const selectedId = select.value;
            
            if (selectedId) {
                const selectedTrans = this.availableTranslations.find(t => t.id === selectedId);
                if (selectedTrans) {
                    this.currentTranslation = {
                        id: selectedTrans.id,
                        name: selectedTrans.name
                    };
                    this.updateStatus(`Ready: ${selectedTrans.name}. Click Start.`);
                }
            }
        },
        
        // Open popup
        open() {
            console.log('Opening Bible Study Assistant...');
            this.isOpen = true;
            document.getElementById('bible-overlay').classList.add('active');
            document.getElementById('bible-btn').style.display = 'none';
        },
        
        // Close popup
        close() {
            console.log('Closing Bible Study Assistant...');
            this.isOpen = false;
            document.getElementById('bible-overlay').classList.remove('active');
            document.getElementById('bible-btn').style.display = 'block';
            if (this.conversationActive) {
                this.endConversation();
            }
        },
        
        // Update status
        updateStatus(text, state = '') {
            document.getElementById('bible-status').textContent = text;
            const avatar = document.getElementById('bible-avatar');
            avatar.className = 'bible-avatar ' + state;
            console.log('Status:', text, state);
        },
        
        // Add transcript
        addTranscript(role, text, tableHtml = null) {
            const transcript = document.getElementById('bible-transcript');
            transcript.style.display = 'block';
            const msg = document.createElement('div');
            msg.className = `transcript-msg ${role}`;
            
            if (role === 'agent' && tableHtml) {
                // For comparison responses with table
                msg.innerHTML = `<strong>Bible AI:</strong> ${text}<br><br>${tableHtml}`;
            } else {
                // For regular messages
                msg.innerHTML = `<strong>${role === 'user' ? 'You' : 'Bible AI'}:</strong> ${text}`;
            }
            
            transcript.appendChild(msg);
            transcript.scrollTop = transcript.scrollHeight;
        },
        
        async startConversation() {
            console.log('=== Starting Conversation ===');
            
            if (this.compareMode) {
                // Compare mode - need multiple translations
                if (this.selectedTranslationsForCompare.length < 2) {
                    this.updateStatus('Please select at least 2 translations to compare');
                    return;
                }
            } else {
                // Single mode - need one translation
                const select = document.getElementById('translation-select');
                const selectedId = select?.value;
                
                if (!selectedId) {
                    this.updateStatus('Please select a Bible translation first');
                    return;
                }
                
                // Update current translation
                const selectedTrans = this.availableTranslations.find(t => t.id === selectedId);
                if (selectedTrans) {
                    this.currentTranslation = {
                        id: selectedTrans.id,
                        name: selectedTrans.name
                    };
                }
            }
            
            console.log('Starting with:', this.compareMode ? this.selectedTranslationsForCompare : this.currentTranslation);
            
            // TEXT MODE: Just activate session without microphone
            if (this.textMode) {
                try {
                    // Create session
                    const resp = await fetch(`${this.apiBase}/agent`);
                    const html = await resp.text();
                    const match = html.match(/SESSION_TOKEN.*?"([^"]+)"/);
                    if (match) {
                        this.sessionToken = match[1];
                        console.log('✓ Session created for text mode');
                        
                        // Only switch translation if in single mode
                        if (!this.compareMode) {
                            await this.switchTranslation(this.currentTranslation.id, this.sessionToken);
                        }
                    }
                    
                    this.conversationActive = true;
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('end-btn').disabled = false;
                    document.getElementById('translation-select').disabled = true;
                    document.getElementById('compare-mode-btn').disabled = true;
                    
                    // Update status for text mode
                    if (this.compareMode) {
                        const transNames = this.selectedTranslationsForCompare
                            .map(id => this.availableTranslations.find(t => t.id === id)?.name)
                            .join(', ');
                        this.updateStatus(`Comparing: ${transNames}. Type your question.`);
                    } else {
                        this.updateStatus(`Ready: ${this.currentTranslation.name}. Type your question.`);
                    }
                    
                } catch (error) {
                    console.error('Session creation error:', error);
                    this.updateStatus('Failed to start session');
                }
                return;
            }
            
            // VOICE MODE: Original microphone logic
            try {
                // Request microphone
                this.updateStatus('Requesting microphone...');
                this.audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        sampleRate: 48000,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                console.log('✓ Microphone granted');
                
                // Initialize audio analyser for VAD
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                this.analyser = audioContext.createAnalyser();
                const source = audioContext.createMediaStreamSource(this.audioStream);
                source.connect(this.analyser);
                this.analyser.fftSize = 2048;
                console.log('✓ Audio analyser initialized');
                
                // Create NEW session for this conversation
                const resp = await fetch(`${this.apiBase}/agent`);
                const html = await resp.text();
                const match = html.match(/SESSION_TOKEN.*?"([^"]+)"/);
                if (match) {
                    this.sessionToken = match[1];
                    console.log('✓ Session created');
                    
                    // Only switch translation if in single mode
                    if (!this.compareMode) {
                        await this.switchTranslation(this.currentTranslation.id, this.sessionToken);
                    }
                }
                
                this.conversationActive = true;
                document.getElementById('start-btn').disabled = true;
                document.getElementById('end-btn').disabled = false;
                document.getElementById('translation-select').disabled = true;
                document.getElementById('compare-mode-btn').disabled = true;
                
                // Bible AI introduces itself
                let greeting;
                if (this.compareMode) {
                    const transNames = this.selectedTranslationsForCompare
                        .map(id => this.availableTranslations.find(t => t.id === id)?.name)
                        .join(', ');
                    greeting = `Hello! I'm your Bible study assistant. You're comparing these translations: ${transNames}. What passage would you like to compare?`;
                } else {
                    greeting = `Hello! I'm your Bible study assistant. You're currently studying from the ${this.currentTranslation.name}. What would you like to know about the Bible today?`;
                }
                
                await this.speak(greeting);
                
                // Start listening after greeting
                setTimeout(() => this.startListening(), 1000);
                
            } catch (error) {
                console.error('Conversation start error:', error);
                this.updateStatus('Microphone access denied');
            }
        },
        
        // Start listening with Voice Activity Detection
        startListening() {
            if (!this.conversationActive) {
                console.log('Conversation not active, stopping');
                return;
            }
            
            if (this.isProcessing) {
                console.log('Still processing, will retry...');
                setTimeout(() => this.startListening(), 500);
                return;
            }
            
            if (this.isRecording) {
                console.log('Already recording, skipping');
                return;
            }
            
            if (this.isSpeaking) {
                console.log('Still speaking, will retry...');
                setTimeout(() => this.startListening(), 500);
                return;
            }
            
            console.log('=== Starting to listen ===');
            this.isRecording = true;
            this.audioChunks = [];
            this.recordingStartTime = Date.now();
            this.updateStatus('Listening...', 'listening');
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, { mimeType: 'audio/webm' });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                console.log('Recording stopped');
                this.isRecording = false;
                this.processAudio();
            };
            
            this.mediaRecorder.start();
            console.log('✓ Recording started');
            
            this.monitorSilence();
        },

        monitorSilence() {
            if (!this.conversationActive || !this.mediaRecorder || this.mediaRecorder.state !== 'recording') {
                return;
            }
            
            const volume = this.detectVoiceActivity();
            const SILENCE_THRESHOLD = 0.05;
            const SILENCE_DURATION = 1500;
            const MIN_RECORDING_TIME = 800;
            const elapsedTime = Date.now() - this.recordingStartTime;
            
            if (volume > SILENCE_THRESHOLD) {
                this.silenceStart = null;
            } else {
                if (!this.silenceStart && elapsedTime > MIN_RECORDING_TIME) {
                    this.silenceStart = Date.now();
                } else if (this.silenceStart) {
                    const silenceDuration = Date.now() - this.silenceStart;
                    if (silenceDuration > SILENCE_DURATION) {
                        this.mediaRecorder.stop();
                        return;
                    }
                }
            }
            
            requestAnimationFrame(() => this.monitorSilence());
        },

        detectVoiceActivity() {
            if (!this.analyser) return 0;
            
            const bufferLength = this.analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            this.analyser.getByteTimeDomainData(dataArray);
            
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                const normalized = (dataArray[i] - 128) / 128;
                sum += normalized * normalized;
            }
            return Math.sqrt(sum / bufferLength);
        },
        
        async processAudio() {
            if (this.isProcessing || this.audioChunks.length === 0) {
                if (this.conversationActive && !this.isProcessing && !this.isSpeaking) {
                    setTimeout(() => this.startListening(), 500);
                }
                return;
            }
            
            this.isProcessing = true;
            this.updateStatus('Processing...');
            
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            this.audioChunks = [];
            
            if (audioBlob.size < 1000) {
                this.isProcessing = false;
                if (this.conversationActive && !this.isSpeaking) {
                    setTimeout(() => this.startListening(), 500);
                }
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');
                
                const sttResp = await fetch(`${this.apiBase}/api/chat/stt`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${this.sessionToken}` },
                    body: formData
                });
                
                if (!sttResp.ok) {
                    console.error('STT failed:', sttResp.status);
                    throw new Error('STT request failed');
                }
                
                const sttData = await sttResp.json();
                
                if (sttData.success && sttData.text && sttData.text.trim()) {
                    const userText = sttData.text.trim();
                    this.addTranscript('user', userText);
                    await this.getChatResponse(userText);
                } else {
                    this.isProcessing = false;
                    if (this.conversationActive && !this.isSpeaking) {
                        setTimeout(() => this.startListening(), 500);
                    }
                }
                
            } catch (error) {
                console.error('STT error:', error);
                this.updateStatus('Error processing audio');
                this.isProcessing = false;
                if (this.conversationActive && !this.isSpeaking) {
                    setTimeout(() => this.startListening(), 2000);
                }
            }
        },
        
        async getChatResponse(userText) {
            this.updateStatus('Thinking...');
            
            try {
                if (this.compareMode && this.selectedTranslationsForCompare.length >= 2) {
                    // Comparison mode
                    const resp = await fetch(`${this.apiBase}/api/chat/compare`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.sessionToken}`
                        },
                        body: JSON.stringify({
                            question: userText,
                            translation_ids: this.selectedTranslationsForCompare,
                            k: 1,  // CHANGE FROM 3 TO 1 for single verse comparisons
                            include_chunks: false
                        })
                    });
                    
                    if (!resp.ok) {
                        const errorText = await resp.text();
                        console.error('Compare failed:', resp.status, errorText);
                        throw new Error(`Comparison request failed: ${resp.status}`);
                    }
                    
                    const data = await resp.json();
                    console.log('Comparison response:', data);
                    
                    // Check for various response formats
                    const answer = data.answer || data.analysis || data.comparison || '';
                    const tableHtml = data.table_html || '';
                    
                    if (!answer && !tableHtml) {
                        throw new Error('Empty response from comparison API');
                    }
                    
                    // Display comparison in dedicated area above transcript
                    if (tableHtml) {
                        const comparisonDisplay = document.getElementById('bible-comparison-display');
                        comparisonDisplay.style.display = 'block';
                        comparisonDisplay.innerHTML = `
                            <div class="comparison-summary">
                                <strong>📊 Comparison Result:</strong> ${answer}
                            </div>
                            ${tableHtml}
                        `;
                    }
                    
                    // Add to transcript
                    this.addTranscript('agent', answer || 'Comparison table displayed above.');
                    
                    // Speak in voice mode
                    if (!this.textMode) {
                        await this.speak(answer);
                    }
                    
                } else {
                    // Single translation mode
                    const resp = await fetch(`${this.apiBase}/api/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${this.sessionToken}`
                        },
                        body: JSON.stringify({
                            question: userText,
                            k: 3,
                            include_sources: false
                        })
                    });
                    
                    if (!resp.ok) {
                        const errorText = await resp.text();
                        console.error('Chat failed:', resp.status, errorText);
                        throw new Error(`Chat request failed: ${resp.status}`);
                    }
                    
                    const data = await resp.json();
                    console.log('Chat response:', data);
                    
                    // Check for answer in various formats
                    const answer = data.answer || data.response || data.text || '';
                    
                    if (!answer) {
                        throw new Error('Empty response from chat API');
                    }
                    
                    this.addTranscript('agent', answer);
                    
                    // Speak in voice mode
                    if (!this.textMode) {
                        await this.speak(answer);
                    }
                }
                
                // Success - ready for next input
                this.isProcessing = false;
                
                if (this.textMode) {
                    this.updateStatus('Ready for next question');
                } else if (this.conversationActive && !this.isRecording) {
                    setTimeout(() => this.startListening(), 1000);
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                this.updateStatus('Error getting response: ' + error.message);
                this.addTranscript('agent', 'Sorry, I encountered an error: ' + error.message);
                this.isProcessing = false;
                
                if (!this.textMode && this.conversationActive && !this.isRecording) {
                    setTimeout(() => this.startListening(), 2000);
                }
            }
        },
        
        async speak(text) {
            if (this.isSpeaking) {
                console.log('Already speaking, queuing or skipping');
                return;
            }
            
            this.isSpeaking = true;
            this.updateStatus('Speaking...', 'talking');
            
            try {
                console.log('Speaking:', text.substring(0, 50) + '...');
                
                if (this.currentAudio) {
                    this.currentAudio.pause();
                    this.currentAudio = null;
                }
                
                const resp = await fetch(`${this.apiBase}/api/chat/tts`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.sessionToken}`
                    },
                    body: JSON.stringify({
                        text: text,
                        voice: 'en-US-JennyNeural',
                        rate: '+0%',
                        pitch: '+0Hz'
                    })
                });
                
                if (!resp.ok) {
                    const errorText = await resp.text();
                    console.error('TTS failed:', resp.status, errorText);
                    throw new Error(`TTS request failed: ${resp.status}`);
                }
                
                const audioBlob = await resp.blob();
                
                if (audioBlob.size === 0) {
                    throw new Error('TTS returned empty audio');
                }
                
                console.log('Got audio blob:', audioBlob.size, 'bytes');
                
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                this.currentAudio = audio;
                
                await new Promise((resolve, reject) => {
                    audio.onended = () => {
                        this.currentAudio = null;
                        URL.revokeObjectURL(audioUrl);
                        resolve();
                    };
                    audio.onerror = (e) => {
                        console.error('Audio playback error:', e);
                        this.currentAudio = null;
                        URL.revokeObjectURL(audioUrl);
                        reject(new Error('Audio playback failed'));
                    };
                    audio.play().catch(err => {
                        console.error('Audio play error:', err);
                        reject(err);
                    });
                });
                
                console.log('✓ Finished speaking');
                
            } catch (error) {
                console.error('TTS error:', error);
                this.updateStatus('Speech error, continuing...');
                this.currentAudio = null;
            }
            
            this.isSpeaking = false;
            this.isProcessing = false;
            
            if (this.conversationActive && !this.isRecording) {
                console.log('Continuing conversation...');
                setTimeout(() => this.startListening(), 1000);
            }
        },
        
        endConversation() {
            console.log('=== Ending Conversation ===');
            this.conversationActive = false;
            this.isProcessing = false;
            this.isRecording = false;
            this.isSpeaking = false;
            
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
            
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
            
            if (this.recordingTimeout) {
                clearTimeout(this.recordingTimeout);
            }
            
            // Clear comparison display
            const comparisonDisplay = document.getElementById('bible-comparison-display');
            if (comparisonDisplay) {
                comparisonDisplay.style.display = 'none';
                comparisonDisplay.innerHTML = '';
            }
            
            document.getElementById('start-btn').disabled = false;
            document.getElementById('end-btn').disabled = true;
            document.getElementById('translation-select').disabled = false;
            document.getElementById('compare-mode-btn').disabled = false;
            this.updateStatus('Conversation ended');
        },

        // Toggle between voice and text input modes
        toggleInputMode(mode) {
            this.textMode = (mode === 'text');
            
            const voiceBtn = document.querySelector('.mode-btn:first-child');
            const textBtn = document.querySelector('.mode-btn:last-child');
            const textContainer = document.getElementById('text-input-container');
            const startBtn = document.getElementById('start-btn');
            const endBtn = document.getElementById('end-btn');
            const avatar = document.getElementById('bible-avatar');
            const controls = document.querySelector('.bible-controls');
            
            if (this.textMode) {
                // Switch to text mode - hide voice elements
                voiceBtn.classList.remove('active');
                textBtn.classList.add('active');
                textContainer.classList.add('active');
                controls.style.display = 'none';  // Hide Start/End buttons
                avatar.style.display = 'none';  // Hide avatar
                this.updateStatus('Type your question and click Send');
            } else {
                // Switch to voice mode - hide text elements
                voiceBtn.classList.add('active');
                textBtn.classList.remove('active');
                textContainer.classList.remove('active');
                controls.style.display = 'flex';  // Show Start/End buttons
                avatar.style.display = 'block';  // Show avatar
                if (this.currentTranslation) {
                    this.updateStatus(`Ready: ${this.currentTranslation.name}. Click Start.`);
                }
            }
        },

        // Send text question (text mode)
        async sendTextQuestion() {
            const input = document.getElementById('bible-text-input');
            const question = input.value.trim();
            
            if (!question) {
                this.updateStatus('Please type a question first');
                return;
            }
            
            // Check if session exists
            if (!this.sessionToken) {
                // Create session if needed
                const resp = await fetch(`${this.apiBase}/agent`);
                const html = await resp.text();
                const match = html.match(/SESSION_TOKEN.*?"([^"]+)"/);
                if (match) {
                    this.sessionToken = match[1];
                    
                    // Switch translation if in single mode
                    if (!this.compareMode && this.currentTranslation) {
                        await this.switchTranslation(this.currentTranslation.id, this.sessionToken);
                    }
                }
            }
            
            // Add user's question to transcript
            this.addTranscript('user', question);
            
            // Clear input
            input.value = '';
            
            // Get response
            await this.getChatResponse(question);
        },

        toggleCompareMode() {
            this.compareMode = !this.compareMode;
            
            const compareBtn = document.getElementById('compare-mode-btn');
            const translationSelect = document.getElementById('translation-select');
            const selectorDiv = document.querySelector('.translation-selector');
            const compareContainer = document.getElementById('compare-selections');
            const comparisonDisplay = document.getElementById('bible-comparison-display');
            const transcript = document.getElementById('bible-transcript');
            
            if (this.compareMode) {
                // Entering compare mode
                compareBtn.textContent = '📖 Single Mode';
                compareBtn.classList.add('active');
                selectorDiv.style.display = 'none';
                compareContainer.style.display = 'block';
                this.updateCompareUI();
                this.updateStatus('Select 2-4 translations and click Start');
                
                // Clear any existing content
                if (comparisonDisplay) {
                    comparisonDisplay.style.display = 'none';
                    comparisonDisplay.innerHTML = '';
                }
                if (transcript) {
                    transcript.innerHTML = '';
                    transcript.style.display = 'none';
                }
            } else {
                // Exiting compare mode
                compareBtn.textContent = '🔄 Compare Translations';
                compareBtn.classList.remove('active');
                selectorDiv.style.display = 'block';
                compareContainer.style.display = 'none';
                this.selectedTranslationsForCompare = [];
                
                // CRITICAL: Clear comparison display and transcript
                if (comparisonDisplay) {
                    comparisonDisplay.style.display = 'none';
                    comparisonDisplay.innerHTML = '';
                }
                if (transcript) {
                    transcript.innerHTML = '';
                    transcript.style.display = 'none';
                }
                
                // Restore single mode status
                if (this.currentTranslation) {
                    this.updateStatus(`Ready: ${this.currentTranslation.name}. Click Start.`);
                } else {
                    this.updateStatus('Select a translation and click Start');
                }
            }
        },

        updateCompareUI() {
            const container = document.getElementById('compare-selections');
            container.innerHTML = '<p style="margin-bottom: 10px; font-weight: 600; color: #1E3A8A;">Select 2-4 translations to compare:</p>';
            
            this.availableTranslations.forEach(trans => {
                const isSelected = this.selectedTranslationsForCompare.includes(trans.id);
                
                const label = document.createElement('label');
                label.style.display = 'block';
                label.style.marginBottom = '8px';
                label.style.cursor = 'pointer';
                label.innerHTML = `
                    <input type="checkbox" 
                           value="${trans.id}" 
                           ${isSelected ? 'checked' : ''}
                           onchange="BibleWidget.toggleTranslationForCompare('${trans.id}')"
                           ${this.selectedTranslationsForCompare.length >= 4 && !isSelected ? 'disabled' : ''}>
                    ${trans.name} (${trans.chunks} verses)
                `;
                
                container.appendChild(label);
            });
        },

        toggleTranslationForCompare(translationId) {
            const index = this.selectedTranslationsForCompare.indexOf(translationId);
            
            if (index > -1) {
                this.selectedTranslationsForCompare.splice(index, 1);
            } else {
                if (this.selectedTranslationsForCompare.length < 4) {
                    this.selectedTranslationsForCompare.push(translationId);
                }
            }
            
            this.updateCompareUI();
            
            // Update status
            const count = this.selectedTranslationsForCompare.length;
            if (count === 0) {
                this.updateStatus('Select 2-4 translations and click Start');
            } else if (count === 1) {
                this.updateStatus('Select at least 1 more translation');
            } else {
                this.updateStatus(`${count} translations selected. Click Start to compare.`);
            }
        }
    };
    
    window.BibleWidget = BibleWidget;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => BibleWidget.init());
    } else {
        BibleWidget.init();
    }
    
    console.log('=== Bible Study Widget Ready ===');
    
})();