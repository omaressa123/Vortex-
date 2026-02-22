// ============================================
// VORTEX DASHBOARD - Main JavaScript
// ============================================

// Global variables
let currentTemplate = null;
let currentTheme = 'default';
let uploadedDataInfo = null;

// ============================================
// THEME MANAGEMENT
// ============================================
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
    localStorage.setItem('dashboard_theme', theme);

    // Close dropdown
    const dropdown = document.getElementById('themeDropdown');
    if (dropdown) dropdown.classList.remove('show');

    showNotification(`Theme changed to ${theme}`, 'success');
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    // Load saved theme
    const savedTheme = localStorage.getItem('dashboard_theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }

    // Check RAG engine status
    checkRAGStatus();
});

// ============================================
// RAG ENGINE STATUS
// ============================================
async function checkRAGStatus() {
    try {
        const response = await fetch('/api/rag/status');
        const data = await response.json();

        if (data.has_data) {
            updateStatus('engineStatus', 'active');
            updateStatus('ragStatus', 'active');
            document.getElementById('engineInfo').textContent = `Data loaded — ${data.documents_count} knowledge documents ready`;
            const badge = document.getElementById('ragDocsBadge');
            badge.classList.remove('inactive');
            badge.classList.add('active');
            document.getElementById('ragDocsCount').textContent = data.documents_count;
        } else {
            updateStatus('engineStatus', 'inactive');
            document.getElementById('engineInfo').textContent = 'Upload a data file to start analyzing. No API keys required!';
        }
    } catch (error) {
        console.error('Failed to check RAG status:', error);
    }
}

// ============================================
// TEMPLATE SELECTION & DASHBOARD GENERATION
// ============================================
function selectTemplate(templateId, templateName, element) {
    currentTemplate = templateId;

    // Update UI
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('selected');
    });
    element.classList.add('selected');

    showNotification(`Template selected: ${templateName}`, 'success');

    // Auto-generate dashboard if data is already uploaded
    if (uploadedDataInfo) {
        generateTemplateDashboard(templateId, templateName);
    }
}

function generateTemplateDashboard(templateId, templateName) {
    const container = document.getElementById('generatedDashboard');
    if (!container || !uploadedDataInfo) return;

    const data = uploadedDataInfo;
    const columns = data.columns || [];
    const preview = data.data_preview || data.preview || [];
    const shape = data.shape || [0, 0];

    // Determine numeric and categorical columns from preview
    let numericCols = [];
    let categoricalCols = [];

    if (preview.length > 0) {
        const firstRow = preview[0];
        for (const [key, val] of Object.entries(firstRow)) {
            if (typeof val === 'number') {
                numericCols.push(key);
            } else {
                categoricalCols.push(key);
            }
        }
    }

    // Template-specific config
    const templateConfigs = {
        'executive': { icon: 'fa-chart-pie', color: '#7c3aed', title: 'Executive Dashboard' },
        'sales': { icon: 'fa-chart-line', color: '#10b981', title: 'Sales Analytics' },
        'marketing': { icon: 'fa-bullhorn', color: '#f59e0b', title: 'Marketing Performance' },
        'hr': { icon: 'fa-users', color: '#0ea5e9', title: 'HR Analytics' },
        'operations': { icon: 'fa-cogs', color: '#f43f5e', title: 'Operations Dashboard' },
        'financial': { icon: 'fa-dollar-sign', color: '#06b6d4', title: 'Financial Overview' }
    };

    const config = templateConfigs[templateId] || { icon: 'fa-chart-bar', color: '#7c3aed', title: templateName };

    // Build KPI cards
    let kpiHtml = '';
    const kpiCols = numericCols.slice(0, 4);
    if (kpiCols.length > 0 && preview.length > 0) {
        kpiHtml = '<div class="row g-3 mb-4">';
        kpiCols.forEach(col => {
            let total = 0;
            preview.forEach(row => { total += (parseFloat(row[col]) || 0); });
            const avg = total / preview.length;
            let displayVal;
            if (total > 1000000) displayVal = (total / 1000000).toFixed(1) + 'M';
            else if (total > 1000) displayVal = (total / 1000).toFixed(1) + 'K';
            else displayVal = total.toFixed(1);

            kpiHtml += `
                <div class="col-md-3 col-sm-6">
                    <div class="metric-card">
                        <h4>${col}</h4>
                        <h2>${displayVal}</h2>
                    </div>
                </div>
            `;
        });
        kpiHtml += '</div>';
    }

    // Build dashboard HTML
    container.innerHTML = `
        <div class="dashboard-generated-header">
            <h3><i class="fas ${config.icon}" style="color: ${config.color};"></i> ${config.title}</h3>
            <span style="color: var(--text-muted); font-size: 0.85rem;">
                ${shape[0].toLocaleString()} rows × ${shape[1]} columns
            </span>
        </div>
        
        ${kpiHtml}
        
        <div class="row g-4">
            ${numericCols.length > 0 ? `
            <div class="col-md-6">
                <div class="chart-container">
                    <h6><i class="fas fa-chart-bar" style="color: var(--primary-light);"></i> Distribution Overview</h6>
                    <canvas id="dashChart1"></canvas>
                </div>
            </div>
            ` : ''}
            ${numericCols.length >= 2 ? `
            <div class="col-md-6">
                <div class="chart-container">
                    <h6><i class="fas fa-chart-line" style="color: var(--accent);"></i> Comparison</h6>
                    <canvas id="dashChart2"></canvas>
                </div>
            </div>
            ` : ''}
            ${categoricalCols.length > 0 && numericCols.length > 0 ? `
            <div class="col-md-6">
                <div class="chart-container">
                    <h6><i class="fas fa-chart-pie" style="color: var(--emerald);"></i> Category Breakdown</h6>
                    <canvas id="dashChart3"></canvas>
                </div>
            </div>
            ` : ''}
            ${numericCols.length >= 2 ? `
            <div class="col-md-6">
                <div class="chart-container">
                    <h6><i class="fas fa-braille" style="color: var(--amber);"></i> Scatter Analysis</h6>
                    <canvas id="dashChart4"></canvas>
                </div>
            </div>
            ` : ''}
        </div>
    `;

    container.style.display = 'block';

    // Render charts with Chart.js
    setTimeout(() => renderDashboardCharts(preview, numericCols, categoricalCols, config), 100);

    showNotification(`${config.title} generated successfully!`, 'success');
}

function renderDashboardCharts(preview, numericCols, categoricalCols, config) {
    const chartColors = {
        primary: 'rgba(124, 58, 237, 0.7)',
        primaryBg: 'rgba(124, 58, 237, 0.15)',
        accent: 'rgba(6, 182, 212, 0.7)',
        accentBg: 'rgba(6, 182, 212, 0.15)',
        emerald: 'rgba(16, 185, 129, 0.7)',
        emeraldBg: 'rgba(16, 185, 129, 0.15)',
        amber: 'rgba(245, 158, 11, 0.7)',
        amberBg: 'rgba(245, 158, 11, 0.15)',
        rose: 'rgba(244, 63, 94, 0.7)',
        roseBg: 'rgba(244, 63, 94, 0.15)',
        sky: 'rgba(14, 165, 233, 0.7)',
        skyBg: 'rgba(14, 165, 233, 0.15)'
    };

    const chartDefaults = {
        color: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.05)',
        font: { family: 'Inter, sans-serif' }
    };

    // Chart 1: Bar chart for first numeric column
    if (numericCols.length > 0) {
        const ctx1 = document.getElementById('dashChart1');
        if (ctx1) {
            const col = numericCols[0];
            const labels = preview.slice(0, 15).map((_, i) => `Row ${i + 1}`);
            const values = preview.slice(0, 15).map(r => parseFloat(r[col]) || 0);

            new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: col,
                        data: values,
                        backgroundColor: chartColors.primary,
                        borderColor: 'rgba(124, 58, 237, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { labels: { color: chartDefaults.color, font: chartDefaults.font } }
                    },
                    scales: {
                        x: { ticks: { color: chartDefaults.color, font: { size: 10 } }, grid: { color: chartDefaults.borderColor } },
                        y: { ticks: { color: chartDefaults.color }, grid: { color: chartDefaults.borderColor } }
                    }
                }
            });
        }
    }

    // Chart 2: Line chart comparing two numeric columns
    if (numericCols.length >= 2) {
        const ctx2 = document.getElementById('dashChart2');
        if (ctx2) {
            const labels = preview.slice(0, 15).map((_, i) => `${i + 1}`);

            new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: numericCols[0],
                            data: preview.slice(0, 15).map(r => parseFloat(r[numericCols[0]]) || 0),
                            borderColor: 'rgba(124, 58, 237, 1)',
                            backgroundColor: chartColors.primaryBg,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3
                        },
                        {
                            label: numericCols[1],
                            data: preview.slice(0, 15).map(r => parseFloat(r[numericCols[1]]) || 0),
                            borderColor: 'rgba(6, 182, 212, 1)',
                            backgroundColor: chartColors.accentBg,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { labels: { color: chartDefaults.color, font: chartDefaults.font } }
                    },
                    scales: {
                        x: { ticks: { color: chartDefaults.color }, grid: { color: chartDefaults.borderColor } },
                        y: { ticks: { color: chartDefaults.color }, grid: { color: chartDefaults.borderColor } }
                    }
                }
            });
        }
    }

    // Chart 3: Doughnut chart for categorical breakdown
    if (categoricalCols.length > 0 && numericCols.length > 0) {
        const ctx3 = document.getElementById('dashChart3');
        if (ctx3) {
            const catCol = categoricalCols[0];
            const numCol = numericCols[0];

            // Aggregate by category
            const aggData = {};
            preview.forEach(row => {
                const cat = String(row[catCol] || 'Unknown');
                aggData[cat] = (aggData[cat] || 0) + (parseFloat(row[numCol]) || 0);
            });

            const sorted = Object.entries(aggData).sort((a, b) => b[1] - a[1]).slice(0, 8);
            const pieColors = [
                'rgba(124, 58, 237, 0.8)',
                'rgba(6, 182, 212, 0.8)',
                'rgba(16, 185, 129, 0.8)',
                'rgba(245, 158, 11, 0.8)',
                'rgba(244, 63, 94, 0.8)',
                'rgba(14, 165, 233, 0.8)',
                'rgba(167, 139, 250, 0.8)',
                'rgba(52, 211, 153, 0.8)'
            ];

            new Chart(ctx3, {
                type: 'doughnut',
                data: {
                    labels: sorted.map(s => s[0]),
                    datasets: [{
                        data: sorted.map(s => s[1]),
                        backgroundColor: pieColors.slice(0, sorted.length),
                        borderWidth: 2,
                        borderColor: 'rgba(10, 10, 26, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: chartDefaults.color, font: chartDefaults.font, padding: 12 }
                        }
                    }
                }
            });
        }
    }

    // Chart 4: Scatter plot
    if (numericCols.length >= 2) {
        const ctx4 = document.getElementById('dashChart4');
        if (ctx4) {
            const scatterData = preview.slice(0, 50).map(r => ({
                x: parseFloat(r[numericCols[0]]) || 0,
                y: parseFloat(r[numericCols[1]]) || 0
            }));

            new Chart(ctx4, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: `${numericCols[0]} vs ${numericCols[1]}`,
                        data: scatterData,
                        backgroundColor: 'rgba(245, 158, 11, 0.6)',
                        borderColor: 'rgba(245, 158, 11, 1)',
                        pointRadius: 5,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { labels: { color: chartDefaults.color, font: chartDefaults.font } }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: numericCols[0], color: chartDefaults.color },
                            ticks: { color: chartDefaults.color },
                            grid: { color: chartDefaults.borderColor }
                        },
                        y: {
                            title: { display: true, text: numericCols[1], color: chartDefaults.color },
                            ticks: { color: chartDefaults.color },
                            grid: { color: chartDefaults.borderColor }
                        }
                    }
                }
            });
        }
    }
}

// ============================================
// DATA UPLOAD
// ============================================
async function uploadData() {
    const fileInput = document.getElementById('dataFile');
    const resultDiv = document.getElementById('uploadResult');

    if (!fileInput.files.length) {
        showNotification('Please select a file first', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    updateStatus('uploadStatus', 'loading');
    resultDiv.innerHTML = '<div style="text-align:center; padding:1rem;"><div class="spinner-ring" style="margin:0 auto;"></div><p style="margin-top:0.5rem; color:var(--text-muted);">Uploading...</p></div>';

    try {
        const response = await fetch('/dashboard/upload-data', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            updateStatus('uploadStatus', 'active');
            updateStatus('engineStatus', 'active');
            updateStatus('ragStatus', 'active');

            // Store uploaded data info globally
            uploadedDataInfo = result;

            resultDiv.innerHTML = `
                <div class="alert-vortex success">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        File uploaded successfully!
                        ${result.rag_documents ? `<br><small>${result.rag_documents} knowledge documents created</small>` : ''}
                    </div>
                </div>
            `;

            // Update RAG badge
            if (result.rag_documents) {
                document.getElementById('engineInfo').textContent = `Data loaded — ${result.rag_documents} knowledge documents ready`;
                const badge = document.getElementById('ragDocsBadge');
                badge.classList.remove('inactive');
                badge.classList.add('active');
                document.getElementById('ragDocsCount').textContent = result.rag_documents;
            }

            // Show preview
            showDataPreview(result);
            document.getElementById('dataPreviewSection').style.display = 'block';
            document.getElementById('analysisSections').style.display = 'block';

            // Auto-generate dashboard if template is selected
            if (currentTemplate) {
                const templateConfigs = {
                    'executive': 'Executive Dashboard',
                    'sales': 'Sales Analytics',
                    'marketing': 'Marketing Performance',
                    'hr': 'HR Analytics',
                    'operations': 'Operations Dashboard',
                    'financial': 'Financial Overview'
                };
                generateTemplateDashboard(currentTemplate, templateConfigs[currentTemplate] || currentTemplate);
            }

            showNotification('Data uploaded and ready for analysis!', 'success');
        } else {
            updateStatus('uploadStatus', 'error');
            resultDiv.innerHTML = `<div class="alert-vortex danger"><i class="fas fa-exclamation-circle"></i> Upload failed: ${result.error}</div>`;
            showNotification('Upload failed', 'danger');
        }
    } catch (error) {
        updateStatus('uploadStatus', 'error');
        resultDiv.innerHTML = `<div class="alert-vortex danger"><i class="fas fa-exclamation-circle"></i> Network error: ${error.message}</div>`;
        showNotification('Network error', 'danger');
    }
}

function showDataPreview(data) {
    const previewDiv = document.getElementById('dataPreview');
    const table = createDataTable(data.data_preview ? data.data_preview.slice(0, 10) : (data.preview || []));
    previewDiv.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <div class="row g-3">
                <div class="col-md-4">
                    <div style="padding: 10px 16px; background: var(--bg-glass); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
                        <small style="color: var(--text-muted);">Shape</small>
                        <div style="font-weight: 600; color: var(--text-primary);">${data.shape[0].toLocaleString()} rows × ${data.shape[1]} columns</div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div style="padding: 10px 16px; background: var(--bg-glass); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
                        <small style="color: var(--text-muted);">Columns</small>
                        <div style="font-weight: 500; color: var(--text-secondary); font-size: 0.85rem;">${data.columns.join(', ')}</div>
                    </div>
                </div>
            </div>
        </div>
        <h6 style="color: var(--text-primary); font-weight: 600; margin-bottom: 0.5rem;">
            <i class="fas fa-table" style="color: var(--accent);"></i> Preview (first 10 rows)
        </h6>
        ${table}
    `;
}

function createDataTable(data) {
    if (!data) return '<p style="color: var(--text-muted);">No data to display</p>';

    // If data is an object (like column profiles)
    if (typeof data === 'object' && !Array.isArray(data)) {
        let html = '<div class="table-responsive"><table class="table table-striped table-hover"><thead><tr>';
        html += '<th>Column</th><th>Property</th><th>Value</th>';
        html += '</tr></thead><tbody>';

        Object.entries(data).forEach(([colName, colData]) => {
            if (typeof colData === 'object' && colData !== null) {
                Object.entries(colData).forEach(([prop, value]) => {
                    let displayValue = value;
                    if (typeof value === 'object' && value !== null) {
                        displayValue = JSON.stringify(value, null, 2);
                    }
                    html += `<tr><td>${colName}</td><td>${prop}</td><td>${displayValue !== null ? displayValue : 'N/A'}</td></tr>`;
                });
            } else {
                html += `<tr><td>${colName}</td><td>-</td><td>${colData !== null ? colData : 'N/A'}</td></tr>`;
            }
        });

        html += '</tbody></table></div>';
        return html;
    }

    // If data is an array of objects
    if (Array.isArray(data) && data.length > 0) {
        let html = '<div class="table-responsive"><table class="table table-striped table-hover"><thead><tr>';

        Object.keys(data[0]).forEach(key => {
            html += `<th>${key}</th>`;
        });
        html += '</tr></thead><tbody>';

        data.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value !== null ? value : 'N/A'}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        return html;
    }

    return '<p style="color: var(--text-muted);">No data to display</p>';
}

// ============================================
// DATA ANALYSIS FUNCTIONS
// ============================================
async function profileData() {
    showLoading();

    try {
        const response = await fetch('/dashboard/profile-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('profilingResults');

            resultsDiv.innerHTML = `
                <div style="margin-bottom: 1rem;">
                    <h6 style="color: var(--text-primary); margin-bottom: 0.5rem;">
                        <i class="fas fa-tachometer-alt" style="color: var(--accent);"></i> Data Quality Score
                    </h6>
                    <div class="progress" style="height: 16px;">
                        <div class="progress-bar" style="width: ${result.quality_score.score}%">${result.quality_score.score}/100</div>
                    </div>
                </div>
                <div class="glass-card" style="margin-bottom: 1rem;">
                    <div class="card-header-vortex"><h5><i class="fas fa-database"></i> Dataset Overview</h5></div>
                    <div class="card-body-vortex"><pre style="color: var(--text-secondary); font-size: 0.85rem;">${JSON.stringify(result.overview, null, 2)}</pre></div>
                </div>
                <div class="glass-card">
                    <div class="card-header-vortex"><h5><i class="fas fa-columns"></i> Column Profiles</h5></div>
                    <div class="card-body-vortex" style="overflow-x: auto;">${createDataTable(result.profile)}</div>
                </div>
            `;
            showNotification('Data profiling completed', 'success');
        } else {
            showNotification('Profiling failed: ' + (result.error || ''), 'danger');
        }
    } catch (error) {
        showNotification('Error during profiling', 'danger');
    }

    hideLoading();
}

function getCleaningMethods() {
    return {
        'handle_missing': document.getElementById('method_handle_missing').checked,
        'remove_duplicates': document.getElementById('method_remove_duplicates').checked,
        'knn_impute': document.getElementById('method_knn_impute').checked,
        'statistical_outliers': document.getElementById('method_statistical_outliers').checked,
        'isolation_forest': document.getElementById('method_isolation_forest').checked,
        'linear_regression_outliers': document.getElementById('method_linear_regression').checked,
        'z_score_threshold': 3.0,
        'iqr_multiplier': 1.5,
        'isolation_contamination': 0.01
    };
}

async function cleanData() {
    showLoading();

    try {
        const cleaningMethods = getCleaningMethods();

        const response = await fetch('/dashboard/clean-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cleaning_methods: cleaningMethods })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('cleaningResults');

            // Build cleaning report HTML
            let reportHtml = '';
            if (result.cleaning_report && result.cleaning_report.steps) {
                reportHtml = '<h6 style="margin-top:1rem; color:var(--text-primary);"><i class="fas fa-list-ol" style="color:var(--accent);"></i> Cleaning Steps:</h6>';
                result.cleaning_report.steps.forEach((step, idx) => {
                    reportHtml += `
                        <div class="cleaning-method-card">
                            <strong>${idx + 1}. ${step.method}</strong>
                            ${step.rows_removed !== undefined ? `<br><small style="color:var(--text-muted);">Rows removed: ${step.rows_removed}</small>` : ''}
                            ${step.columns_dropped ? `<br><small style="color:var(--text-muted);">Columns dropped: ${step.columns_dropped.join(', ')}</small>` : ''}
                            ${step.columns_filled ? `<br><small style="color:var(--text-muted);">Columns filled: ${step.columns_filled.join(', ')}</small>` : ''}
                            ${step.columns_imputed ? `<br><small style="color:var(--text-muted);">Columns imputed: ${step.columns_imputed.join(', ')}</small>` : ''}
                            ${step.error ? `<br><small style="color:var(--amber);">Note: ${step.error}</small>` : ''}
                        </div>
                    `;
                });
            }

            resultsDiv.innerHTML = `
                <div class="alert-vortex success" style="margin-bottom:1rem;">
                    <i class="fas fa-broom"></i>
                    <div>
                        <strong>Data Cleaning Complete</strong>
                        <div class="row mt-2">
                            <div class="col-6"><small>Original: ${result.original_shape[0]} × ${result.original_shape[1]}</small></div>
                            <div class="col-6"><small>Cleaned: ${result.cleaned_shape[0]} × ${result.cleaned_shape[1]}</small></div>
                        </div>
                        <div class="row">
                            <div class="col-6"><small>Rows removed: ${result.rows_removed}</small></div>
                            <div class="col-6"><small>Columns removed: ${result.columns_removed}</small></div>
                        </div>
                    </div>
                </div>
                ${reportHtml}
                <div class="alert-vortex info" style="margin-top:1rem;">
                    <i class="fas fa-file-alt"></i> Cleaned file saved as: ${result.cleaned_filename}
                </div>
            `;
            showNotification('Data cleaning completed', 'success');
        } else {
            showNotification('Data cleaning failed: ' + (result.error || ''), 'danger');
        }
    } catch (error) {
        showNotification('Error during cleaning', 'danger');
    }

    hideLoading();
}

async function generateEDA() {
    showLoading();

    try {
        const response = await fetch('/dashboard/generate-eda', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('edaResults');

            resultsDiv.innerHTML = `
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="glass-card">
                            <div class="card-header-vortex"><h5><i class="fas fa-calculator"></i> Numeric Summary</h5></div>
                            <div class="card-body-vortex" style="overflow-x:auto;">${createDataTable(result.numeric_summary)}</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="glass-card">
                            <div class="card-header-vortex"><h5><i class="fas fa-tags"></i> Categorical Summary</h5></div>
                            <div class="card-body-vortex" style="overflow-x:auto;">${createDataTable(result.categorical_summary)}</div>
                        </div>
                    </div>
                </div>
                <div class="glass-card" style="margin-top:1rem;">
                    <div class="card-header-vortex"><h5><i class="fas fa-chart-bar"></i> Key Performance Indicators</h5></div>
                    <div class="card-body-vortex">${createKPICards(result.kpis)}</div>
                </div>
            `;
            showNotification('EDA completed', 'success');
        } else {
            showNotification('EDA generation failed', 'danger');
        }
    } catch (error) {
        showNotification('Error during EDA', 'danger');
    }

    hideLoading();
}

function createKPICards(kpis) {
    if (!kpis) return '<p style="color: var(--text-muted);">No KPIs to display</p>';

    let html = '<div class="row g-3">';
    let count = 0;

    for (const [key, value] of Object.entries(kpis)) {
        if (typeof value === 'object' && value !== null) {
            html += `
                <div class="col-md-4 col-sm-6">
                    <div class="glass-card" style="padding: 1rem; text-align:center;">
                        <h6 style="color: var(--primary-light); font-size: 0.85rem; margin-bottom: 0.5rem;">${key}</h6>
                        <div style="font-size: 0.85rem;">
                            ${Object.entries(value).map(([k, v]) =>
                `<div><small style="color:var(--text-muted);">${k}:</small> <strong style="color:var(--text-primary);">${typeof v === 'number' ? v.toLocaleString() : v}</strong></div>`
            ).join('')}
                        </div>
                    </div>
                </div>
            `;
        } else if (typeof value === 'number') {
            html += `
                <div class="col-md-3 col-sm-6">
                    <div class="metric-card">
                        <h4>${key}</h4>
                        <h2>${value.toLocaleString()}</h2>
                    </div>
                </div>
            `;
        }
        count++;
    }

    html += '</div>';
    return html;
}

// ============================================
// VISUALIZATION FUNCTIONS
// ============================================
async function generateVisualization() {
    const vizType = document.getElementById('vizType').value;
    const column = document.getElementById('vizColumn').value;

    showLoading();

    try {
        const response = await fetch('/dashboard/generate-visualization', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ viz_type: vizType, column: column })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('visualizationResults');

            if (vizType === 'auto' && result.figures) {
                let html = '<div class="viz-grid">';
                result.figures.forEach((fig) => {
                    html += `
                        <div class="viz-card">
                            <h6 style="color:var(--text-primary); margin-bottom:0.5rem;">${fig.name}</h6>
                            ${fig.img ? `<img src="${fig.img.startsWith('data:image') ? fig.img : 'data:image/png;base64,' + fig.img}" alt="${fig.name}" />` : '<span style="color:var(--text-muted);">No image</span>'}
                        </div>
                    `;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
            } else if (result.figure) {
                if (typeof result.figure === 'string') {
                    resultsDiv.innerHTML = `
                        <div class="viz-card">
                            <img src="${result.figure.startsWith('data:image') ? result.figure : 'data:image/png;base64,' + result.figure}" alt="Visualization" />
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = '<div class="viz-card"><p style="color:var(--text-muted);">Visualization generated</p></div>';
                }
            }

            showNotification('Visualization generated', 'success');
        } else {
            showNotification('Visualization failed', 'danger');
        }
    } catch (error) {
        showNotification('Error during visualization', 'danger');
    }

    hideLoading();
}

// ============================================
// CONVERSATIONAL DATA RAG
// ============================================
function askQuickQuestion(question) {
    document.getElementById('questionInput').value = question;
    askQuestion();
}

async function askQuestion() {
    const question = document.getElementById('questionInput').value.trim();

    if (!question) {
        showNotification('Please enter a question', 'warning');
        return;
    }

    updateStatus('chatStatus', 'loading');
    addChatMessage(question, 'user');
    document.getElementById('questionInput').value = '';

    try {
        const response = await fetch('/dashboard/ask-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            updateStatus('chatStatus', 'active');
            addChatMessage(result.answer, 'assistant');

            if (result.sources && result.sources.length > 0) {
                const sourceText = '📚 Sources: ' + result.sources.map(s => s.title).join(', ');
                addChatMessage(sourceText, 'assistant');
            }
        } else {
            updateStatus('chatStatus', 'error');
            addChatMessage('❌ Error: ' + (result.error || 'Failed to get answer'), 'assistant');
        }
    } catch (error) {
        updateStatus('chatStatus', 'error');
        addChatMessage('❌ Network error: ' + error.message, 'assistant');
    }
}

function addChatMessage(message, type) {
    const chatDiv = document.getElementById('chatMessages');

    const msgEl = document.createElement('div');
    msgEl.className = `chat-message ${type}`;

    const formattedMsg = message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    msgEl.innerHTML = `<pre>${formattedMsg}</pre>`;
    chatDiv.appendChild(msgEl);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

// Enter key
document.getElementById('questionInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});

// ============================================
// UTILITY FUNCTIONS
// ============================================
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('show');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('show');
}

function updateStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.className = 'status-dot';

    switch (status) {
        case 'active': element.classList.add('active'); break;
        case 'loading': element.classList.add('loading'); break;
        case 'error': element.classList.add('error'); break;
        default: element.classList.add('inactive');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `toast-notification ${type}`;

    const icons = {
        success: 'fa-check-circle',
        danger: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    notification.innerHTML = `<i class="fas ${icons[type] || 'fa-info-circle'}"></i> ${message}`;
    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

function logout() {
    fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/login')
        .catch(() => window.location.href = '/login');
}

// Viz type change handler
document.getElementById('vizType').addEventListener('change', function () {
    const vizType = this.value;
    const columnSelect = document.getElementById('vizColumn');

    if (vizType === 'distribution' || vizType === 'time_series') {
        columnSelect.style.display = 'block';
        columnSelect.required = true;
    } else {
        columnSelect.style.display = 'none';
        columnSelect.required = false;
    }
});
