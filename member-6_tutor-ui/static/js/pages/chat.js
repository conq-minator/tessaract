/**
 * Tesseract Ollama-Style Chatbot Client
 */

(function () {
    let chatHistory = [];
    let currentAttachedImage = null; // { name: string, base64: string }
    let isGenerating = false;

    // Elements
    const chatMessages = document.getElementById('chat-messages');
    const chatWelcome = document.getElementById('chat-welcome');
    const chatInput = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-chat-send');
    const modelSelect = document.getElementById('chat-model-select');
    const imageStrip = document.getElementById('attached-image-strip');
    const thumbImg = document.getElementById('attached-thumb-img');
    const filenameLabel = document.getElementById('attached-filename');

    // Initialize
    document.addEventListener('DOMContentLoaded', async () => {
        // Sync models
        try {
            const data = await window.API.getModels();
            if (data && data.available_models && modelSelect) {
                modelSelect.innerHTML = '';
                for (const m of data.available_models) {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m + (m === 'smollm2:1.7b' ? ' (Fast)' : m === 'gemma2:2b' ? ' (Balanced)' : m === 'gemma4:e2b' ? ' (Vision / Deep)' : '');
                    if (m === data.current_model) opt.selected = true;
                    modelSelect.appendChild(opt);
                }
            }
        } catch (e) {
            console.debug("Model load notice:", e);
        }

        // Focus input
        if (chatInput) chatInput.focus();

        // Check pre-filled prompt from Knowledge Graph or other pages
        const prefill = sessionStorage.getItem('tesseract_initial_prompt');
        if (prefill) {
            sessionStorage.removeItem('tesseract_initial_prompt');
            setTimeout(() => {
                window.usePrompt(prefill);
            }, 300);
        }
    });

    window.autoResizeTextarea = function (el) {
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 140) + 'px';
    };

    window.handleChatKeyDown = function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            window.submitChatMessage();
        }
    };

    window.handleChatModelSwitch = async function (modelName) {
        try {
            await window.API.selectModel(modelName);
            if (window.App && window.App.showToast) {
                window.App.showToast(`Switched active model to ${modelName}`, 'success');
            }
        } catch (e) {
            console.error("Model switch failed:", e);
        }
    };

    window.handleImageSelect = function (e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (evt) {
            currentAttachedImage = {
                name: file.name,
                base64: evt.target.result
            };
            thumbImg.src = evt.target.result;
            filenameLabel.textContent = file.name;
            imageStrip.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    };

    window.removeAttachedImage = function () {
        currentAttachedImage = null;
        imageStrip.style.display = 'none';
        document.getElementById('chat-image-input').value = '';
    };

    window.usePrompt = function (text) {
        if (chatInput) {
            chatInput.value = text;
            window.autoResizeTextarea(chatInput);
            chatInput.focus();
            window.submitChatMessage();
        }
    };

    window.clearChatHistory = function () {
        chatHistory = [];
        chatMessages.innerHTML = '';
        if (chatWelcome) {
            chatMessages.appendChild(chatWelcome);
            chatWelcome.style.display = 'block';
        }
        window.removeAttachedImage();
        if (chatInput) chatInput.value = '';
    };

    window.submitChatMessage = async function () {
        if (isGenerating) return;
        const text = (chatInput.value || '').trim();
        if (!text && !currentAttachedImage) return;

        // Hide welcome screen
        if (chatWelcome) chatWelcome.style.display = 'none';

        // Render User Message
        const userMsg = {
            role: 'user',
            content: text,
            image: currentAttachedImage ? currentAttachedImage.base64 : null
        };
        chatHistory.push(userMsg);
        renderUserMessage(userMsg);

        // Reset input field & attachments
        chatInput.value = '';
        chatInput.style.height = 'auto';
        const imageToSend = currentAttachedImage ? currentAttachedImage.base64 : null;
        window.removeAttachedImage();

        // Render Typing Indicator
        isGenerating = true;
        btnSend.disabled = true;
        const typingEl = renderTypingIndicator();
        scrollToBottom();

        const modelUsed = modelSelect ? modelSelect.value : 'smollm2:1.7b';

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    model: modelUsed,
                    image: imageToSend,
                    history: chatHistory.map(m => ({ role: m.role, content: m.content }))
                })
            });

            const data = await resp.json();
            typingEl.remove();

            const replyText = data.reply || data.explanation || "No response received.";
            const assistantMsg = {
                role: 'assistant',
                content: replyText,
                model_used: data.model_used || modelUsed,
                latency_ms: data.latency_ms || 0
            };
            chatHistory.push(assistantMsg);
            renderAssistantMessage(assistantMsg);
        } catch (err) {
            typingEl.remove();
            renderAssistantMessage({
                role: 'assistant',
                content: `⚠️ Failed to get answer: ${err.message}`,
                model_used: modelUsed,
                latency_ms: 0
            });
        } finally {
            isGenerating = false;
            btnSend.disabled = false;
            scrollToBottom();
            chatInput.focus();
        }
    };

    function renderUserMessage(msg) {
        const row = document.createElement('div');
        row.className = 'msg-row user';

        let imageHtml = '';
        if (msg.image) {
            imageHtml = `<img src="${msg.image}" class="msg-image-preview" alt="Attached Image">`;
        }

        row.innerHTML = `
            <div class="msg-bubble">
                ${imageHtml}
                <div>${escapeHtml(msg.content)}</div>
            </div>
            <div class="msg-avatar">👤</div>
        `;
        chatMessages.appendChild(row);
    }

    function renderAssistantMessage(msg) {
        const row = document.createElement('div');
        row.className = 'msg-row assistant';

        const latencySec = (msg.latency_ms / 1000).toFixed(1);
        const formattedBody = formatMarkdown(msg.content);

        row.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble">
                <div class="msg-meta">
                    <span class="badge-model">${escapeHtml(msg.model_used || 'Tesseract')}</span>
                    ${msg.latency_ms > 0 ? `<span>⚡ ${latencySec}s</span>` : ''}
                </div>
                <div class="msg-text">${formattedBody}</div>
            </div>
        `;
        chatMessages.appendChild(row);
        bindCopyButtons(row);
    }

    function renderTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'msg-row assistant typing-indicator-row';
        row.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble" style="padding: 6px 14px;">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(row);
        return row;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Markdown Parser
    function formatMarkdown(raw) {
        if (!raw) return '';
        let text = raw;

        // Code blocks: ```lang ... ```
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function (match, lang, code) {
            const escapedCode = escapeHtml(code.trim());
            return `
                <div style="position: relative;">
                    <pre><code class="language-${lang}">${escapedCode}</code></pre>
                    <button class="copy-btn" onclick="window.copySnippet(this)">Copy</button>
                </div>
            `;
        });

        // Inline code `...`
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Bold **...**
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Bullet lists
        text = text.replace(/^-\s+(.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Newlines to <br> (outside pre)
        const parts = text.split(/(<pre[\s\S]*?<\/pre>)/g);
        for (let i = 0; i < parts.length; i++) {
            if (!parts[i].startsWith('<pre')) {
                parts[i] = parts[i].replace(/\n\n+/g, '<p></p>').replace(/\n/g, '<br>');
            }
        }
        return parts.join('');
    }

    window.copySnippet = function (btn) {
        const pre = btn.previousElementSibling;
        const code = pre ? pre.textContent : '';
        navigator.clipboard.writeText(code).then(() => {
            btn.textContent = 'Copied!';
            setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
        });
    };

    function bindCopyButtons(container) {
        // copySnippet is globally bound
    }

})();
