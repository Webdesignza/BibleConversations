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
                    width: 90%;
                    max-width: 500px;
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
                    margin-bottom: 20px;
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
                
                .bible-avatar {
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 5px solid #1E3A8A;
                    transition: box-shadow 0.3s ease;
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
                    margin: 20px 0;
                    padding: 15px;
                    background: #f0f9ff;
                    border-radius: 10px;
                    min-height: 50px;
                }
                
                .bible-controls {
                    display: flex;
                    gap: 10px;
                    justify-content: center;
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
                    margin-top: 20px;
                    max-height: 200px;
                    overflow-y: auto;
                    text-align: left;
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
                        <img id="bible-avatar" class="bible-avatar"
                             src="${this.apiBase}/static/images/bible-avatar.png" 
                             alt="Bible AI">
                        <div id="bible-status" class="bible-status">
                            Select a translation and click Start
                        </div>
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
        addTranscript(role, text) {
            const transcript = document.getElementById('bible-transcript');
            transcript.style.display = 'block';
            const msg = document.createElement('div');
            msg.className = `transcript-msg ${role}`;
            msg.innerHTML = `<strong>${role === 'user' ? 'You' : 'Bible AI'}:</strong> ${text}`;
            transcript.appendChild(msg);
            transcript.scrollTop = transcript.scrollHeight;
        },
        
        async startConversation() {
            console.log('=== Starting Conversation ===');
            
            // Get translation from dropdown
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
            
            console.log('Starting with:', this.currentTranslation);
            
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
                    
                    // Switch to selected translation using THIS session token
                    await this.switchTranslation(this.currentTranslation.id, this.sessionToken);
                }
                
                this.conversationActive = true;
                document.getElementById('start-btn').disabled = true;
                document.getElementById('end-btn').disabled = false;
                document.getElementById('translation-select').disabled = true;
                
                // Bible AI introduces itself
                const greeting = `Hello! I'm your Bible study assistant. You're currently studying from the ${this.currentTranslation.name}. What would you like to know about the Bible today?`;
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
            // Better state checking
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
                    console.error('Chat failed:', resp.status);
                    throw new Error('Chat request failed');
                }
                
                const data = await resp.json();
                
                if (data.success) {
                    this.addTranscript('agent', data.answer);
                    await this.speak(data.answer);
                } else {
                    throw new Error('No response');
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                this.updateStatus('Error getting response');
                this.isProcessing = false;
                setTimeout(() => this.startListening(), 2000);
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
            
            document.getElementById('start-btn').disabled = false;
            document.getElementById('end-btn').disabled = true;
            document.getElementById('translation-select').disabled = false;
            this.updateStatus('Conversation ended');
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