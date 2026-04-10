// currentSessionId at global scope so chat functions outside DOMContentLoaded can read it
let currentSessionId = null;

document.addEventListener('DOMContentLoaded', () => {


    // currentSessionId is declared globally above — do not re-declare here

    // Elements
    const fileInput       = document.getElementById('file-input');
    const dropZone        = document.getElementById('drop-zone');
    const uploadSection   = document.getElementById('upload-section');
    const loadingSection  = document.getElementById('loading-section');
    const dashboardSection= document.getElementById('dashboard-section');
    const loadingLabel    = document.getElementById('loading-label');
    const loadingSub      = document.getElementById('loading-sub');

    // Tab Elements
    const tabBtns    = document.querySelectorAll('.tab-btn');
    const tabContents= document.querySelectorAll('.tab-content');

    // Action Buttons
    const btnClean = document.getElementById('btn-clean');
    const btnModel = document.getElementById('btn-model');

    // ── Fix #3: Restore session from localStorage ─────────────────────────
    const savedSession = localStorage.getItem('ai_analyst_session_id');
    if (savedSession) {
        currentSessionId = savedSession;
        document.getElementById('session-input').value = savedSession;
    }

    // ── Drag & Drop ────────────────────────────────────────────────────────
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#1f2687';
        dropZone.style.background = 'rgba(255,255,255,0.9)';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'rgba(74, 0, 224, 0.3)';
        dropZone.style.background = 'rgba(255,255,255,0.4)';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) handleUpload(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleUpload(e.target.files[0]);
    });

    // ── Fix #2: Loading helper with dynamic text ───────────────────────────
    function setLoading(title, sub) {
        loadingLabel.textContent = title;
        loadingSub.textContent   = sub;
        switchView(loadingSection);
    }

    // ── Upload Logic ───────────────────────────────────────────────────────
    async function handleUpload(file) {
        if (!file.name.endsWith('.csv')) { alert('Please upload a CSV file.'); return; }

        setLoading('Uploading...', 'Reading the CSV and creating your session.');

        // 1. Create Session
        const sessionRes = await fetch('/create_session', { method: 'POST' });
        const sessionData = await sessionRes.json();
        currentSessionId = sessionData.session_id;

        // Fix #3: Persist session ID
        localStorage.setItem('ai_analyst_session_id', currentSessionId);
        document.getElementById('session-input').value = currentSessionId;

        // 2. Upload File
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', currentSessionId);

        try {
            const res = await fetch('/upload_dataset', { method: 'POST', body: formData });
            if (!res.ok) throw new Error("Upload failed — check file format.");
            await loadAnalysis();
        } catch (e) {
            alert('Error: ' + e.message);
            switchView(uploadSection);
        }
    }

    // ── Load Analysis ──────────────────────────────────────────────────────
    async function loadAnalysis(forceRefresh = false) {
        setLoading('Analyzing...', 'Running EDA, correlations, and generating LLM insights.');
        try {
            const url = `/get_full_analysis?session_id=${currentSessionId}${forceRefresh ? '&refresh=true' : ''}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("Analysis failed — try refreshing.");
            const data = await res.json();
            populateDashboard(data);
            switchView(dashboardSection);
            window.dispatchEvent(new Event('resize'));
        } catch (e) {
            alert(e.message);
            switchView(uploadSection);
        }
    }

    // Expose to global scope so chat widget (outside this closure) can call it
    window._agentRefresh = (forceRefresh) => loadAnalysis(forceRefresh);

    // ── Populate Dashboard (Summary + Insights + Charts) ──────────────────
    function populateDashboard(data) {
        const general = data.insights?.general || {};

        // Summary card
        document.getElementById('general-summary').innerHTML =
            `<p style="font-size:1.1rem">${general.summary || 'Summary unavailable'}</p>`;

        // Key Findings
        const keyList = document.querySelector('#key-findings ul');
        keyList.innerHTML = '';
        (data.insights?.key_findings || []).forEach(f => keyList.innerHTML += `<li>${f}</li>`);

        // Correlation Ranking — {feature, correlation} objects
        const corrList = document.querySelector('#correlation-ranking ul');
        corrList.innerHTML = '';
        (data.insights?.correlation_ranking || []).forEach(item => {
            const pct   = (Math.abs(item.correlation) * 100).toFixed(1);
            const dir   = item.correlation >= 0 ? '▲' : '▼';
            const level = Math.abs(item.correlation) >= 0.4 ? 'strong'
                        : Math.abs(item.correlation) >= 0.2 ? 'moderate' : 'weak';
            corrList.innerHTML +=
                `<li><strong>${item.feature}</strong> &nbsp;<span class="corr-badge corr-${level}">${dir} ${pct}%</span></li>`;
        });

        // Insights tab
        const tList = document.getElementById('target-analysis-list');
        tList.innerHTML = '';
        (data.insights?.target_analysis || []).forEach(t => tList.innerHTML += `<li>${t}</li>`);

        const rList = document.getElementById('recommendations-list');
        rList.innerHTML = '';
        (data.insights?.recommendations || []).forEach(r => rList.innerHTML += `<li>${r}</li>`);

        const llmRaw = data.insights?.llm || '*(LLM Summary not available)*';
        document.getElementById('llm-insights-text').innerHTML = marked.parse(llmRaw);

        // EDA Charts
        renderCharts(data.eda || {});
    }

    // ── Fix #1 & #6: Populate Modeling Tab ────────────────────────────────
    function populateModelingTab(m) {
        document.getElementById('no-model-msg').classList.add('hidden');
        document.getElementById('model-results').classList.remove('hidden');
        document.getElementById('model-badge').classList.remove('hidden');

        const isClassification = m.problem_type === 'classification';

        let metrics;
        if (isClassification) {
            metrics = [
                { label: 'Ensemble Accuracy', value: fmt(m.metric_value),         note: 'Hold-out test set' },
                { label: 'CV Score',           value: fmt(m.cv_score_mean),        note: `± ${fmt(m.cv_score_std)} variance` },
                { label: 'ROC-AUC',            value: fmt(m.extra_metrics?.roc_auc),  note: 'Discrimination power' },
                { label: 'F1 Score',           value: fmt(m.extra_metrics?.f1_score), note: 'Precision / Recall balance' },
                { label: 'PR-AUC',             value: fmt(m.extra_metrics?.pr_auc),   note: 'Imbalance-robust' },
                { label: 'Best Base Model', value: m.best_model?.replace(/_/g, ' '), note: m.model_architecture, isText: true },
            ];
        } else {
            // For regression: metric_value = RMSE, extra_metrics = {r2_score}
            const primaryLabel = (m.metric_name || 'metric').toUpperCase().replace('_', ' ');
            metrics = [
                { label: primaryLabel,  value: fmtRaw(m.metric_value),                note: `Primary metric (${m.metric_name})` },
                { label: 'R² Score',    value: fmt(m.extra_metrics?.r2_score),         note: 'Explained variance (1 = perfect)' },
                { label: 'CV Score',    value: fmt(m.cv_score_mean),                   note: `± ${fmt(m.cv_score_std)} variance` },
                { label: 'Train Rows',  value: m.rows_trained?.toLocaleString(),       note: 'Samples used for training', isText: true },
                { label: 'Test Rows',   value: m.rows_tested?.toLocaleString(),        note: 'Hold-out evaluation set', isText: true },
                { label: 'Best Base Model', value: m.best_model?.replace(/_/g, ' '), note: m.model_architecture, isText: true },
            ];
        }

        const metricCards = document.getElementById('metric-cards');
        metricCards.innerHTML = '';
        metrics.forEach(({ label, value, note, isText }) => {
            metricCards.innerHTML += `
              <div class="metric-card">
                <span class="metric-value ${isText ? 'metric-text' : ''}">${value ?? 'N/A'}</span>
                <span class="metric-label">${label}</span>
                <span class="metric-note">${note}</span>
              </div>`;
        });

        // ── Model Comparison Bars ─────────────────────────────────────
        const modelBars = document.getElementById('model-bars');
        modelBars.innerHTML = '';
        const perf = m.models_performance || {};
        const allScores = Object.values(perf);
        const maxScore = Math.max(...allScores);
        Object.entries(perf)
            .sort(([,a],[,b]) => b - a)
            .forEach(([name, score]) => {
                const barPct = (score / maxScore * 100).toFixed(1);
                const isBest = name === m.best_model;
                modelBars.innerHTML += `
                  <div class="bar-row">
                    <span class="bar-name ${isBest ? 'bar-best' : ''}">${name.replace(/_/g,' ')} ${isBest ? '⭐' : ''}</span>
                    <div class="bar-track">
                      <div class="bar-fill ${isBest ? 'bar-fill-best' : ''}" style="width:${barPct}%"></div>
                    </div>
                    <span class="bar-score">${fmt(score)}</span>
                  </div>`;
            });

        // ── Feature Importance Bars ───────────────────────────────────
        document.getElementById('fi-source').textContent = `via ${m.feature_importance_source}`;
        const featureBars = document.getElementById('feature-bars');
        featureBars.innerHTML = '';
        const features = (m.feature_importance || []);
        const maxImp = features[0]?.importance || 1;
        features.forEach(({ feature, importance }) => {
            const barPct = (importance / maxImp * 100).toFixed(1);
            featureBars.innerHTML += `
              <div class="bar-row">
                <span class="bar-name">${feature}</span>
                <div class="bar-track">
                  <div class="bar-fill bar-fill-feature" style="width:${barPct}%"></div>
                </div>
                <span class="bar-score">${(importance * 100).toFixed(1)}%</span>
              </div>`;
        });

        // Auto-switch to modeling tab
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        document.querySelector('[data-target="tab-modeling"]').classList.add('active');
        document.getElementById('tab-modeling').classList.add('active');
    }

    // fmt: shows as % only when value is 0–1 (accuracy, R², AUC scores)
    function fmt(val) {
        if (val === undefined || val === null) return 'N/A';
        if (val >= 0 && val <= 1) return (val * 100).toFixed(2) + '%';
        return val.toFixed ? val.toFixed(4) : String(val);
    }

    // fmtRaw: display large numbers cleanly (RMSE, MAE)
    function fmtRaw(val) {
        if (val === undefined || val === null) return 'N/A';
        return val >= 1000 ? val.toLocaleString('en-US', { maximumFractionDigits: 0 })
                           : val.toFixed(4);
    }

    // ── Plotly Rendering ───────────────────────────────────────────────────
    function renderCharts(eda) {
        const container = document.getElementById('chart-container');
        container.innerHTML = '';

        function addSectionLabel(text) {
            const label = document.createElement('h3');
            label.className = 'chart-section-label';
            label.textContent = text;
            container.appendChild(label);
        }

        function addChart(jsonStr, idx, heightPx = 380) {
            const figure = JSON.parse(jsonStr);
            const divId  = `plot-${idx}`;

            const wrapper = document.createElement('div');
            wrapper.className = 'chart-wrapper';

            const plotDiv = document.createElement('div');
            plotDiv.id = divId;
            plotDiv.style.width  = '100%';
            plotDiv.style.height = `${heightPx}px`;

            wrapper.appendChild(plotDiv);
            container.appendChild(wrapper);

            figure.layout = Object.assign({}, figure.layout, {
                autosize: true,
                margin: { l: 60, r: 20, t: 50, b: 65 },
                xaxis: Object.assign({}, figure.layout?.xaxis, { automargin: true }),
                yaxis: Object.assign({}, figure.layout?.yaxis, { automargin: true })
            });

            Plotly.newPlot(divId, figure.data, figure.layout, { responsive: true, displayModeBar: false });
        }

        let idx = 0;

        if ((eda.target_analysis || []).length > 0) {
            addSectionLabel('📦 Feature vs Target (Churn Splits)');
            eda.target_analysis.forEach(p => addChart(p, idx++));
        }
        if ((eda.univariate || []).length > 0) {
            addSectionLabel('📊 Univariate Distributions');
            eda.univariate.forEach(p => addChart(p, idx++));
        }
        if ((eda.bivariate || []).length > 0) {
            addSectionLabel('🔗 Bivariate Relationships');
            eda.bivariate.forEach(p => addChart(p, idx++));
        }
        if (eda.correlation) {
            addSectionLabel('🌡️ Correlation Matrix');
            addChart(eda.correlation, idx++, 560);
        }
    }

    // ── Tabs ───────────────────────────────────────────────────────────────
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
            if (btn.dataset.target === 'tab-eda') window.dispatchEvent(new Event('resize'));
        });
    });

    // ── Action Buttons ─────────────────────────────────────────────────────
    btnClean.addEventListener('click', async () => {
        if (!currentSessionId) { alert('Upload a dataset first.'); return; }
        if (!confirm('Auto-clean the dataset? This will drop ID columns and encode categoricals.')) return;
        setLoading('Cleaning Data...', 'Dropping IDs, encoding categoricals, imputing missing values.');
        try {
            await fetch(`/cleaning?session_id=${currentSessionId}`, { method: 'POST' });
            await loadAnalysis();
        } catch {
            alert('Cleaning error — check backend logs.');
            switchView(dashboardSection);
        }
    });

    // Fix #1 & #2: btnModel now shows proper loading label and renders results
    btnModel.addEventListener('click', async () => {
        if (!currentSessionId) { alert('Upload a dataset first.'); return; }
        setLoading('Training AutoML...', 'Running 5-fold CV on Logistic Regression, Random Forest, and Gradient Boosting.');
        try {
            const res = await fetch(`/modeling?session_id=${currentSessionId}`, { method: 'POST' });
            if (!res.ok) throw new Error("Modeling failed — run /get_full_analysis first.");
            const modelData = await res.json();
            switchView(dashboardSection);
            populateModelingTab(modelData);
        } catch (e) {
            alert(e.message);
            switchView(dashboardSection);
        }
    });

    // ── Util ───────────────────────────────────────────────────────────────
    function switchView(target) {
        [uploadSection, loadingSection, dashboardSection].forEach(el => el.classList.add('hidden'));
        target.classList.remove('hidden');
    }

});

// ── Chat Widget ───────────────────────────────────────────────────────────────
// Lives OUTSIDE DOMContentLoaded so confirmAction() is globally accessible
// from the onclick attributes in index.html.
//
// KEY CONCEPT — Why fetch() instead of EventSource for SSE:
//   The browser's native EventSource API only supports GET requests.
//   Our /chat endpoint is POST (it needs a request body with session_id + message).
//   So we use fetch() + ReadableStream manually:
//     response.body.getReader() → ReadableStream of raw bytes
//     TextDecoder → converts chunks to strings
//     Buffer logic → handles partial SSE events split across multiple read() calls

let _chatOpen    = false;
let _chatPending = false;   // true while streaming/waiting for confirmation
let _aiRawText   = '';      // accumulates markdown tokens for current AI message
let _currentAIBubble  = null;
let _typingIndicator  = null;

// ── Toggle ────────────────────────────────────────────────────────────────────
function toggleChat() {
    _chatOpen = !_chatOpen;
    const panel  = document.getElementById('chat-panel');
    const bubble = document.getElementById('chat-bubble');

    if (_chatOpen) {
        panel.classList.add('open');
        document.getElementById('chat-bubble-label').textContent = '✕ Close';

        // Show welcome message the very first time the dashboard is open
        const msgs = document.getElementById('chat-messages');
        if (msgs.children.length === 0 && typeof currentSessionId !== 'undefined' && currentSessionId) {
            _appendAIMessage(
                "👋 **Welcome!** I've finished profiling your dataset.\n\n" +
                "You can ask me to:\n" +
                "- **Clean the data** — I'll remove ID columns, encode categoricals, impute missing values\n" +
                "- **Train a model** — AutoML VotingEnsemble with 5-fold CV\n" +
                "- **Predict** — Give me feature values and I'll predict the target\n" +
                "- **Ask anything** — correlations, features, model results, next steps\n\n" +
                "What would you like to explore?"
            );
        }
    } else {
        panel.classList.remove('open');
        document.getElementById('chat-bubble-label').textContent = 'Ask AI';
    }
}

// ── Message Helpers ───────────────────────────────────────────────────────────
function _appendUserMessage(text) {
    const msgs = document.getElementById('chat-messages');
    const div  = document.createElement('div');
    div.className = 'chat-msg user';
    div.innerHTML = `<div class="chat-bubble-msg">${text}</div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function _appendAIMessage(markdownText) {
    const msgs = document.getElementById('chat-messages');
    const div  = document.createElement('div');
    div.className = 'chat-msg ai';
    div.innerHTML = `<div class="chat-bubble-msg ai-text">${marked.parse(markdownText)}</div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function _showTyping() {
    const msgs = document.getElementById('chat-messages');
    _typingIndicator = document.createElement('div');
    _typingIndicator.className = 'chat-msg ai';
    _typingIndicator.innerHTML = '<div class="chat-bubble-msg typing"><span></span><span></span><span></span></div>';
    msgs.appendChild(_typingIndicator);
    msgs.scrollTop = msgs.scrollHeight;
}

function _hideTyping() {
    if (_typingIndicator) { _typingIndicator.remove(); _typingIndicator = null; }
}

function _beginAIBubble() {
    _hideTyping();
    _aiRawText = '';
    const msgs = document.getElementById('chat-messages');
    _currentAIBubble = document.createElement('div');
    _currentAIBubble.className = 'chat-msg ai';
    _currentAIBubble.innerHTML = '<div class="chat-bubble-msg ai-text"></div>';
    msgs.appendChild(_currentAIBubble);
}

function _appendToken(token) {
    _aiRawText += token;
    if (_currentAIBubble) {
        _currentAIBubble.querySelector('.ai-text').innerHTML = marked.parse(_aiRawText);
        document.getElementById('chat-messages').scrollTop = 999999;
    }
}

function _finalizeAIBubble() {
    _currentAIBubble = null;
    _aiRawText = '';
}

// ── Input State ───────────────────────────────────────────────────────────────
function _setInputEnabled(enabled) {
    _chatPending = !enabled;
    const input = document.getElementById('chat-input');
    const btn   = document.getElementById('chat-send-btn');
    const status = document.getElementById('chat-status');
    if (input) input.disabled   = !enabled;
    if (btn)   btn.disabled     = !enabled;
    if (status) status.innerHTML = enabled
        ? '<span class="status-dot"></span> Ready'
        : '<span class="status-dot" style="background:#f59e0b"></span> Thinking...';
}

// ── Confirmation Gate ─────────────────────────────────────────────────────────
function _showConfirmation(markdownMessage) {
    const bar = document.getElementById('chat-confirm-bar');
    document.getElementById('confirm-content').innerHTML = marked.parse(markdownMessage);
    bar.classList.remove('hidden');
    document.getElementById('chat-status').innerHTML =
        '<span class="status-dot" style="background:#f59e0b"></span> Waiting for confirmation...';
}

function _hideConfirmation() {
    document.getElementById('chat-confirm-bar').classList.add('hidden');
}

async function confirmAction(confirmed) {
    _hideConfirmation();

    if (!confirmed) {
        _appendAIMessage('❌ **Action cancelled.** Nothing was changed.');
        _setInputEnabled(true);
        return;
    }

    _setInputEnabled(false);
    _showTyping();

    try {
        const res = await fetch('/chat/confirm', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ session_id: currentSessionId, confirmed: true }),
        });
        if (!res.ok) throw new Error(`Server ${res.status}`);
        await _processStream(res);
    } catch (e) {
        _hideTyping();
        _appendAIMessage(`❌ **Error:** ${e.message}`);
        _finalizeAIBubble();
    }

    _setInputEnabled(true);
}

// ── Core: SSE Stream Processor ────────────────────────────────────────────────
async function _processStream(response) {
    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';
    let   aiStarted = false;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE events are delimited by "\n\n"
        // A single read() call may contain multiple events, or a partial event
        const parts = buffer.split('\n\n');
        buffer = parts.pop();   // keep the incomplete trailing fragment

        for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith('data: ')) continue;

            let data;
            try { data = JSON.parse(line.slice(6)); } catch { continue; }

            if (data.type === 'token') {
                if (!aiStarted) { _beginAIBubble(); aiStarted = true; }
                _appendToken(data.content);

            } else if (data.type === 'confirmation_required') {
                _hideTyping();
                _showConfirmation(data.message);
                _finalizeAIBubble();
                return;   // leave input disabled until confirmAction()

            } else if (data.type === 'done') {
                // Fallback: entire response in one shot (no streaming tokens)
                if (!aiStarted && data.response) {
                    _beginAIBubble();
                    _appendToken(data.response);
                }
                _finalizeAIBubble();

                // Refresh dashboard if agent ran a tool that changed the session state
                // run_clean: busts analysis cache → force refresh=true to re-run EDA
                // profile:   refreshed cache in session → re-fetch (no re-run needed)
                if (data.refresh_needed && window._agentRefresh) {
                    setTimeout(() => window._agentRefresh(data.action === 'run_clean'), 800);
                }

            } else if (data.type === 'error') {
                _hideTyping();
                _appendAIMessage(`❌ **Error:** ${data.message}`);
                _finalizeAIBubble();
            }
        }
    }
}

// ── Send Message ──────────────────────────────────────────────────────────────
async function sendChatMessage() {
    if (_chatPending) return;

    // currentSessionId is defined in the DOMContentLoaded closure above
    const sessionId = typeof currentSessionId !== 'undefined' ? currentSessionId : null;
    if (!sessionId) {
        _appendAIMessage('⚠️ Please upload a dataset first to start chatting.');
        return;
    }

    const input   = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    _appendUserMessage(message);
    _setInputEnabled(false);
    _showTyping();

    try {
        const res = await fetch('/chat', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ session_id: sessionId, message }),
        });
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        await _processStream(res);
    } catch (e) {
        _hideTyping();
        _appendAIMessage(`❌ **Could not reach the server:** ${e.message}`);
        _finalizeAIBubble();
    }

    // Re-enable input unless we're waiting for confirmation
    const confirmBar = document.getElementById('chat-confirm-bar');
    if (confirmBar && confirmBar.classList.contains('hidden')) {
        _setInputEnabled(true);
    }
}
