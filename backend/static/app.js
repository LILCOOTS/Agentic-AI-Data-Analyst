document.addEventListener('DOMContentLoaded', () => {

    let currentSessionId = null;

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
    async function loadAnalysis() {
        setLoading('Analyzing...', 'Running EDA, correlations, and generating LLM insights.');
        try {
            const res = await fetch(`/get_full_analysis?session_id=${currentSessionId}`);
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
