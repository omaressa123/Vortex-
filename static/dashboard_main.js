// Global variables
let currentTemplate = null;
let currentTheme = 'default';

// Theme Management
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
    localStorage.setItem('dashboard_theme', theme);
}

// Load saved theme and check RAG status
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('dashboard_theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
    
    // Check RAG engine status
    checkRAGStatus();
});

// Check RAG engine status
async function checkRAGStatus() {
    try {
        const response = await fetch('/api/rag/status');
        const data = await response.json();
        
        if (data.has_data) {
            updateStatus('engineStatus', 'active');
            updateStatus('ragStatus', 'active');
            document.getElementById('engineInfo').textContent = `Data loaded - ${data.documents_count} knowledge documents ready`;
            document.getElementById('ragDocsBadge').style.display = 'inline-block';
            document.getElementById('ragDocsCount').textContent = data.documents_count;
        } else {
            updateStatus('engineStatus', 'inactive');
            document.getElementById('engineInfo').textContent = 'Upload a data file to start analyzing. No API keys required!';
        }
    } catch (error) {
        console.error('Failed to check RAG status:', error);
    }
}

// Template Selection
function selectTemplate(templateId, templateName) {
    currentTemplate = templateId;
    
    // Update UI to show selected template
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
    
    showNotification(`Selected: ${templateName}`, 'success');
}

// Data Upload
async function uploadData() {
    const fileInput = document.getElementById('dataFile');
    const resultDiv = document.getElementById('uploadResult');
    
    if (!fileInput.files.length) {
        showNotification('Please select a file', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    updateStatus('uploadStatus', 'loading');
    resultDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Uploading...</span></div>';
    
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
            
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> File uploaded successfully! 
                    ${result.rag_documents ? `<br><small>${result.rag_documents} knowledge documents created for analysis</small>` : ''}
                </div>
            `;
            
            // Update RAG info
            if (result.rag_documents) {
                document.getElementById('engineInfo').textContent = `Data loaded - ${result.rag_documents} knowledge documents ready`;
                document.getElementById('ragDocsBadge').style.display = 'inline-block';
                document.getElementById('ragDocsCount').textContent = result.rag_documents;
            }
            
            // Show data preview
            showDataPreview(result);
            document.getElementById('dataPreviewSection').style.display = 'block';
            document.getElementById('analysisSections').style.display = 'block';
            
            showNotification('Data uploaded and ready for analysis', 'success');
        } else {
            updateStatus('uploadStatus', 'error');
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Upload failed: ${result.error}</div>`;
            showNotification('Upload failed', 'danger');
        }
    } catch (error) {
        updateStatus('uploadStatus', 'error');
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Network error: ${error.message}</div>`;
        showNotification('Network error', 'danger');
    }
}

function showDataPreview(data) {
    const previewDiv = document.getElementById('dataPreview');
    const table = createDataTable(data.data_preview.slice(0, 10));
    previewDiv.innerHTML = `
        <div class="mb-3">
            <h6><i class="fas fa-info-circle"></i> Dataset Info</h6>
            <div class="row">
                <div class="col-md-3">
                    <strong>Shape:</strong> ${data.shape[0]} rows × ${data.shape[1]} columns
                </div>
                <div class="col-md-9">
                    <strong>Columns:</strong> ${data.columns.join(', ')}
                </div>
            </div>
        </div>
        <h6><i class="fas fa-table"></i> Data Preview (First 10 rows)</h6>
        ${table}
    `;
}

function createDataTable(data) {
    if (!data) return '<p>No data to display</p>';
    
    // If data is an object (like column profiles), convert to table format
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
    
    return '<p>No data to display</p>';
}

// Data Analysis Functions
async function profileData() {
    showLoading();
    
    try {
        const response = await fetch('/dashboard/profile-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('profilingResults');
            
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <h6><i class="fas fa-chart-line"></i> Data Quality Score</h6>
                    <div class="progress mb-3">
                        <div class="progress-bar" style="width: ${result.quality_score.score}%">${result.quality_score.score}/100</div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-database"></i> Dataset Overview</h6>
                    </div>
                    <div class="card-body">
                        <pre>${JSON.stringify(result.overview, null, 2)}</pre>
                    </div>
                </div>
                <div class="card mt-3">
                    <div class="card-header">
                        <h6><i class="fas fa-columns"></i> Column Profiles</h6>
                    </div>
                    <div class="card-body">
                        ${createDataTable(result.profile)}
                    </div>
                </div>
            `;
            showNotification('Data profiling completed', 'success');
        } else {
            showNotification('Profiling failed', 'danger');
        }
    } catch (error) {
        showNotification('Error during profiling', 'danger');
    }
    
    hideLoading();
}

// Get selected cleaning methods from checkboxes
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
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                cleaning_methods: cleaningMethods 
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('cleaningResults');
            
            // Build cleaning report HTML
            let reportHtml = '';
            if (result.cleaning_report && result.cleaning_report.steps) {
                reportHtml = '<h6 class="mt-3"><i class="fas fa-list"></i> Cleaning Steps:</h6>';
                result.cleaning_report.steps.forEach((step, idx) => {
                    reportHtml += `
                        <div class="cleaning-method-card">
                            <strong>${idx + 1}. ${step.method}</strong>
                            ${step.rows_removed !== undefined ? `<br><small>Rows removed: ${step.rows_removed}</small>` : ''}
                            ${step.columns_dropped ? `<br><small>Columns dropped: ${step.columns_dropped.join(', ')}</small>` : ''}
                            ${step.columns_filled ? `<br><small>Columns filled: ${step.columns_filled.join(', ')}</small>` : ''}
                            ${step.columns_imputed ? `<br><small>Columns imputed: ${step.columns_imputed.join(', ')}</small>` : ''}
                            ${step.error ? `<br><small class="text-warning">Note: ${step.error}</small>` : ''}
                        </div>
                    `;
                });
            }
            
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-broom"></i> Data Cleaning Complete</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Original Shape:</strong> ${result.original_shape[0]} × ${result.original_shape[1]}
                        </div>
                        <div class="col-md-6">
                            <strong>Cleaned Shape:</strong> ${result.cleaned_shape[0]} × ${result.cleaned_shape[1]}
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <strong>Rows Removed:</strong> ${result.rows_removed}
                        </div>
                        <div class="col-md-6">
                            <strong>Columns Removed:</strong> ${result.columns_removed}
                        </div>
                    </div>
                </div>
                ${reportHtml}
                <div class="alert alert-info mt-3">
                    <strong>Cleaned file saved as:</strong> ${result.cleaned_filename}
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
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('edaResults');
            
            resultsDiv.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-calculator"></i> Numeric Summary</h6>
                            </div>
                            <div class="card-body">
                                ${createDataTable(result.numeric_summary)}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-tags"></i> Categorical Summary</h6>
                            </div>
                            <div class="card-body">
                                ${createDataTable(result.categorical_summary)}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card mt-3">
                    <div class="card-header">
                        <h6><i class="fas fa-chart-bar"></i> Key Performance Indicators</h6>
                    </div>
                    <div class="card-body">
                        ${createKPICards(result.kpis)}
                    </div>
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
    if (!kpis) return '<p>No KPIs to display</p>';
    
    let html = '<div class="row">';
    let count = 0;
    
    for (const [key, value] of Object.entries(kpis)) {
        if (count > 0 && count % 4 === 0) {
            html += '</div><div class="row">';
        }
        
        if (typeof value === 'object' && value !== null) {
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h6 class="card-title">${key}</h6>
                            <div class="card-text">
                                ${Object.entries(value).map(([k, v]) => 
                                    `<div><strong>${k}:</strong> ${typeof v === 'number' ? v.toLocaleString() : v}</div>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (typeof value === 'number') {
            html += `
                <div class="col-md-3 mb-3">
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

// Visualization Functions
async function generateVisualization() {
    const vizType = document.getElementById('vizType').value;
    const column = document.getElementById('vizColumn').value;
    
    showLoading();
    
    try {
        const response = await fetch('/dashboard/generate-visualization', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                viz_type: vizType,
                column: column 
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('visualizationResults');
            
            if (vizType === 'auto' && result.figures) {
                let html = '<div class="row">';
                result.figures.forEach((fig) => {
                    html += `
                        <div class="col-md-6 mb-3">
                            <div class="chart-container">
                                <h6>${fig.name}</h6>
                                ${fig.img ? `<img src="${fig.img.startsWith('data:image') ? fig.img : 'data:image/png;base64,' + fig.img}" style="max-width: 100%; height: auto;" />` : '<span style="color:#fff">No image</span>'}
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
            } else if (result.figure) {
                if (typeof result.figure === 'string') {
                    resultsDiv.innerHTML = `
                        <div class="chart-container">
                            <img src="${result.figure.startsWith('data:image') ? result.figure : 'data:image/png;base64,' + result.figure}" style="max-width: 100%; height: auto;" />
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `<div class="chart-container"><p>Visualization generated</p></div>`;
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

// ===== Conversational Data RAG =====

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
    
    // Add user message to chat
    addChatMessage(question, 'user');
    document.getElementById('questionInput').value = '';
    
    try {
        const response = await fetch('/dashboard/ask-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateStatus('chatStatus', 'active');
            
            // Add assistant response to chat
            addChatMessage(result.answer, 'assistant');
            
            // Show sources if available
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
    
    // Convert markdown-like formatting to HTML
    const formattedMsg = message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    msgEl.innerHTML = `<pre>${formattedMsg}</pre>`;
    chatDiv.appendChild(msgEl);
    
    // Scroll to bottom
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

// Handle Enter key in question input
document.getElementById('questionInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});

// ===== Utility Functions =====

function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function updateStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.className = 'status-indicator';
    
    switch(status) {
        case 'active':
            element.classList.add('status-active');
            break;
        case 'loading':
            element.classList.add('status-inactive');
            break;
        case 'error':
            element.classList.add('status-error');
            break;
        default:
            element.classList.add('status-inactive');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed`;
    notification.style.cssText = 'top: 20px; right: 80px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
    
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

// Handle visualization type changes
document.getElementById('vizType').addEventListener('change', function() {
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
