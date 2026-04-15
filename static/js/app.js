// API base URL
const API_BASE = '/api';

// Current session state
let currentSessionId = null;
let currentConversationData = null;

// Load stats and conversations on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadConversations();
    newConversation();
    setupKeyboardShortcuts();
    loadThemePreference();
});

// ============ TOAST NOTIFICATIONS ============

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ DARK MODE ============

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
    
    const icon = document.querySelector('.theme-icon');
    icon.textContent = isDark ? '☀️' : '🌙';
    
    showToast(isDark ? 'Dark mode enabled' : 'Light mode enabled', 'success');
}

function loadThemePreference() {
    const isDark = localStorage.getItem('darkMode') === 'true';
    if (isDark) {
        document.body.classList.add('dark-mode');
        document.querySelector('.theme-icon').textContent = '☀️';
    }
}

// ============ KEYBOARD SHORTCUTS ============

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            askQuestion();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            newConversation();
        }
        if (e.key === 'Escape') {
            document.getElementById('questionInput').value = '';
        }
    });
}

// ============ CONVERSATION SEARCH ============

function filterConversations() {
    const searchTerm = document.getElementById('searchConversations').value.toLowerCase();
    const conversations = document.querySelectorAll('.conversation-item');
    
    conversations.forEach(conv => {
        const title = conv.querySelector('.conversation-item-title').textContent.toLowerCase();
        conv.style.display = title.includes(searchTerm) ? 'block' : 'none';
    });
}

// ============ COPY TO CLIPBOARD ============

function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = '✓ Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copied');
        }, 2000);
        
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

// ============ CONVERSATION MANAGEMENT ============

async function newConversation() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = data.session_id;
            currentConversationData = { messages: [] };
            document.getElementById('conversationHistory').innerHTML = '';
            document.getElementById('welcomeScreen').style.display = 'flex';
            loadConversations();
            showToast('New conversation started', 'success');
        }
    } catch (error) {
        console.error('Error creating conversation:', error);
        showToast('Failed to create conversation', 'error');
    }
}

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/conversations`);
        const data = await response.json();
        
        if (data.success) {
            displayConversations(data.conversations);
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

function displayConversations(conversations) {
    const listDiv = document.getElementById('conversationList');
    
    if (conversations.length === 0) {
        listDiv.innerHTML = '<p class="loading-text">No conversations yet</p>';
        return;
    }
    
    listDiv.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.session_id === currentSessionId ? 'active' : ''}" 
             onclick="loadConversation('${conv.session_id}')">
            <div class="conversation-item-title">${conv.title}</div>
            <div class="conversation-item-meta">
                <span>${conv.message_count} messages</span>
                <span>${formatDate(conv.created_at)}</span>
            </div>
            <div class="conversation-item-actions" onclick="event.stopPropagation()">
                <button class="btn-delete" onclick="deleteConversation('${conv.session_id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function loadConversation(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/conversations/${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = sessionId;
            currentConversationData = data.conversation;
            displayConversationHistory(data.conversation.messages);
            loadConversations();
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        showToast('Failed to load conversation', 'error');
    }
}

function displayConversationHistory(messages) {
    const historyDiv = document.getElementById('conversationHistory');
    
    if (!messages || messages.length === 0) {
        historyDiv.innerHTML = '';
        return;
    }

    // Hide welcome screen if there are messages
    document.getElementById('welcomeScreen').style.display = 'none';
    
    historyDiv.innerHTML = messages.map(msg => `
        <div class="message-pair">
            <div class="message user">
                <div class="message-header">
                    <span>👤 You</span>
                    <span class="message-timestamp">${formatTimestamp(msg.timestamp)}</span>
                </div>
                <div class="message-content">${escapeHtml(msg.question)}</div>
            </div>
            <div class="message assistant">
                <div class="message-header">
                    <span>🔥 Ember</span>
                    <button class="copy-btn" onclick="copyToClipboard(\`${escapeHtml(msg.answer).replace(/`/g, '\\`')}\`, this)" title="Copy answer">
                        📋 Copy
                    </button>
                </div>
                <div class="message-content">${escapeHtml(msg.answer)}</div>
            </div>
        </div>
    `).join('');
    
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

async function deleteConversation(sessionId) {
    if (!confirm('Delete this conversation?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/conversations/${sessionId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            if (sessionId === currentSessionId) {
                newConversation();
            }
            loadConversations();
            showToast('Conversation deleted', 'success');
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        showToast('Failed to delete conversation', 'error');
    }
}

async function clearAllConversations() {
    if (!confirm('Delete ALL conversations? This cannot be undone!')) return;
    
    try {
        const response = await fetch(`${API_BASE}/conversations/clear-all`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            newConversation();
            loadConversations();
            showToast('All conversations cleared', 'success');
        }
    } catch (error) {
        console.error('Error clearing conversations:', error);
        showToast('Failed to clear conversations', 'error');
    }
}

async function exportCurrentConversation() {
    if (!currentSessionId) {
        showToast('No conversation to export', 'error');
        return;
    }
    const format = confirm('Export as Markdown? (Cancel for Plain Text)') ? 'md' : 'txt';
    window.open(`${API_BASE}/conversations/${currentSessionId}/export?format=${format}`, '_blank');
    showToast('Exporting conversation...', 'info');
}

// ============ STATS ============

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        if (data.success) {
            displayStats(data.stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function displayStats(stats) {
    const statsDiv = document.getElementById('stats');
    if (!statsDiv) return;
    statsDiv.innerHTML = `
        <div class="stat-item">
            <div class="stat-label">Documents</div>
            <div class="stat-value">${stats.total_documents}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Conversations</div>
            <div class="stat-value">${stats.total_conversations}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Embedding</div>
            <div class="stat-value">${stats.embedding_model.split('-')[0]}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">LLM</div>
            <div class="stat-value">${stats.llm_provider}</div>
        </div>
    `;
}

// ============ DOCUMENT UPLOAD — FIXED ============

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    
    if (files.length === 0) {
        showToast('Please select a file', 'error');
        return;
    }
    
    for (let file of files) {
        showToast(`Uploading "${file.name}"...`, 'info');

        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast(`✅ "${file.name}" uploaded!`, 'success');
                loadStats();
            } else {
                showToast(`❌ Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showToast(`❌ Upload failed: ${error.message}`, 'error');
        }
    }
    
    // Reset so the same file can be re-uploaded if needed
    fileInput.value = '';
}

async function indexAll() {
    if (!confirm('This will re-index all documents in the documents folder. Continue?')) return;
    
    showToast('Indexing all documents...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/index-all`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadStats();
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Indexing error:', error);
        showToast(`Indexing failed: ${error.message}`, 'error');
    }
}

async function clearIndex() {
    if (!confirm('This will delete all indexed documents. Are you sure?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/clear`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadStats();
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Clear error:', error);
        showToast(`Clear failed: ${error.message}`, 'error');
    }
}

// ============ QUERY ============

async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        showToast('Please enter a question', 'error');
        return;
    }

    hideWelcomeScreen();
    
    const topK = parseInt(document.getElementById('topK').value);
    const useHistory = document.getElementById('useHistoryToggle').checked;
    
    document.getElementById('typingIndicator').style.display = 'flex';
    addMessageToDisplay(question, 'user');
    questionInput.value = '';
    questionInput.style.height = 'auto';
    
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                session_id: currentSessionId,
                top_k: topK,
                use_history: useHistory
            })
        });
        
        const data = await response.json();
        document.getElementById('typingIndicator').style.display = 'none';
        
        if (data.success) {
            currentSessionId = data.session_id;
            // Pass null for sources so they are never shown
            addMessageToDisplay(data.answer, 'assistant', null);
            loadConversation(currentSessionId);
            loadStats();
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        document.getElementById('typingIndicator').style.display = 'none';
        console.error('Query error:', error);
        showToast(`Query failed: ${error.message}`, 'error');
    }
}

function addMessageToDisplay(content, role, sources = null) {
    const historyDiv = document.getElementById('conversationHistory');
    const timestamp = new Date().toISOString();
    
    const messageHTML = role === 'user' ? `
        <div class="message-pair">
            <div class="message user">
                <div class="message-header">
                    <span>👤 You</span>
                    <span class="message-timestamp">${formatTimestamp(timestamp)}</span>
                </div>
                <div class="message-content">${escapeHtml(content)}</div>
            </div>
        </div>
    ` : `
        <div class="message assistant">
            <div class="message-header">
                <span>🔥 Ember</span>
                <button class="copy-btn" onclick="copyToClipboard(\`${escapeHtml(content).replace(/`/g, '\\`')}\`, this)" title="Copy answer">
                    📋 Copy
                </button>
            </div>
            <div class="message-content">${escapeHtml(content)}</div>
        </div>
    `;
    
    if (role === 'user') {
        historyDiv.innerHTML += messageHTML;
    } else {
        const lastPair = historyDiv.querySelector('.message-pair:last-child');
        if (lastPair) {
            lastPair.innerHTML += messageHTML;
        } else {
            historyDiv.innerHTML += `<div class="message-pair">${messageHTML}</div>`;
        }
    }
    
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

function askExampleQuestion(question) {
    document.getElementById('questionInput').value = question;
    askQuestion();
}

// ============ UTILITIES ============

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    if (diffMins < 10080) return `${Math.floor(diffMins / 1440)}d ago`;
    return date.toLocaleDateString();
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleTextareaKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        askQuestion();
    }
}

// Auto-resize textarea
document.getElementById('questionInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

function hideWelcomeScreen() {
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) {
        welcome.style.display = 'none';
    }
}

function closeModal() {
    document.getElementById('statsModal').style.display = 'none';
}