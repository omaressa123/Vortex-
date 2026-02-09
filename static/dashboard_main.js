// Global variables
let currentTemplate = null;
let currentTheme = 'default';

// Theme Management
function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
    localStorage.setItem('dashboard_theme', theme);
}

// Load saved theme and check local LLM status
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('dashboard_theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
    
    // Check local LLM status
    checkLocalLLMStatus();
    
    // Check authentication status
    checkAuthStatus();
});

// Check local LLM status
async function checkLocalLLMStatus() {
    try {
        const response = await fetch('/api/local-llm/status');
        const data = await response.json();
        
        if (data.available) {
            updateLocalModelDropdown(data.models);
        }
    } catch (error) {
        console.error('Failed to check local LLM status:', error);
    }
}

function updateLocalModelDropdown(models) {
    const select = document.getElementById('localModel');
    select.innerHTML = '';
    
    // Default models
    const defaultModels = ['llama3', 'mistral', 'phi-3', 'qwen2', 'codellama'];
    
    defaultModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model.charAt(0).toUpperCase() + model.slice(1);
        
        // Mark if model is available locally
        if (models.includes(model)) {
            option.textContent += ' (Available)';
        }
        
        select.appendChild(option);
    });
}

// Show local LLM setup instructions
async function showLocalSetup() {
    try {
        const response = await fetch('/api/local-llm/setup');
        const data = await response.json();
        
        // Create modal with setup instructions
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-cog"></i> Local LLM Setup (Ollama)
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${data.instructions}</pre>
                        
                        <div class="mt-3">
                            <button class="btn btn-success" onclick="pullModel('llama3')">
                                <i class="fas fa-download"></i> Pull Llama 3
                            </button>
                            <button class="btn btn-info" onclick="pullModel('mistral')">
                                <i class="fas fa-download"></i> Pull Mistral
                            </button>
                            <button class="btn btn-warning" onclick="pullModel('phi-3')">
                                <i class="fas fa-download"></i> Pull Phi-3
                            </button>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
            // Refresh local LLM status after setup
            setTimeout(checkLocalLLMStatus, 2000);
        });
        
    } catch (error) {
        showNotification('Failed to load setup instructions', 'danger');
    }
}

// Pull a model from Ollama
async function pullModel(modelName) {
    try {
        showNotification(`Pulling ${modelName}...`, 'info');
        
        const response = await fetch('/api/local-llm/pull', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: modelName })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification(result.message, 'success');
            // Refresh model list after a delay
            setTimeout(checkLocalLLMStatus, 5000);
        } else {
            showNotification(result.error || 'Failed to pull model', 'danger');
        }
    } catch (error) {
        showNotification('Error pulling model', 'danger');
    }
}

// Test Local LLM
async function testLocalLLM() {
    const localModel = document.getElementById('localModel').value;
    const resultDiv = document.getElementById('llmTestResult');
    
    updateStatus('apiStatus', 'loading');
    resultDiv.innerHTML = '<div class="spinner-border text-success" role="status"><span class="visually-hidden">Testing Local LLM...</span></div>';
    
    try {
        const response = await fetch('/api/local-llm/status');
        const data = await response.json();
        
        if (response.ok && data.available) {
            updateStatus('apiStatus', 'active');
            updateStatus('ragStatus', 'active');
            resultDiv.innerHTML = `<div class="alert alert-success"><i class="fas fa-check-circle"></i> Local LLM is working! Using ${localModel}</div>`;
            showNotification('Local LLM is ready!', 'success');
        } else {
            updateStatus('apiStatus', 'error');
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Local LLM not available: ${data.message}</div>`;
            showNotification('Local LLM test failed', 'danger');
        }
    } catch (error) {
        updateStatus('apiStatus', 'error');
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Network error: ${error.message}</div>`;
        showNotification('Network error', 'danger');
    }
}

// Load available API providers
async function loadAPIProviders() {
    try {
        const response = await fetch('/api/providers');
        const data = await response.json();
        
        if (response.ok) {
            updateProviderDropdown(data.providers, data.config);
        }
    } catch (error) {
        console.error('Failed to load API providers:', error);
    }
}

function updateProviderDropdown(providers, config) {
    const select = document.getElementById('apiProvider');
    select.innerHTML = '';
    
    providers.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
        
        // Mark if provider has configured key
        if (config[provider].has_key) {
            option.textContent += ' (Configured)';
        }
        
        select.appendChild(option);
    });
    
    // Update provider info
    updateProviderInfo(select.value);
}

// Update provider information
document.getElementById('apiProvider').addEventListener('change', function() {
    updateProviderInfo(this.value);
});

function updateProviderInfo(provider) {
    const infoSpan = document.getElementById('providerInfo');
    const apiKeyInput = document.getElementById('apiKey');
    
    const providerInfo = {
        'openai': 'OpenAI: GPT models, requires sk- prefix',
        'deepseek': 'DeepSeek: Fast AI models via RapidAPI',
        'anthropic': 'Anthropic: Claude models, requires sk-ant- prefix',
        'google': 'Google: Gemini models, requires Google API key'
    };
    
    infoSpan.textContent = providerInfo[provider] || 'Select a provider and enter your API key';
    
    // Update placeholder
    const placeholders = {
        'openai': 'sk-... (OpenAI API key)',
        'deepseek': '... (DeepSeek RapidAPI key)',
        'anthropic': 'sk-ant-... (Anthropic API key)',
        'google': '... (Google API key)'
    };
    
    apiKeyInput.placeholder = placeholders[provider] || 'Enter your API key';
}

// Show API configuration modal
function showAPIConfig() {
    // Create a simple modal for API configuration
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-cog"></i> API Configuration
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <h6>Environment Variables</h6>
                    <p>Configure API keys using environment variables:</p>
                    <ul>
                        <li><strong>OPENAI_API_KEY</strong> - OpenAI API key</li>
                        <li><strong>DEEPSEEK_API_KEY</strong> - DeepSeek RapidAPI key</li>
                        <li><strong>ANTHROPIC_API_KEY</strong> - Anthropic API key</li>
                        <li><strong>GOOGLE_API_KEY</strong> - Google Gemini API key</li>
                    </ul>
                    
                    <h6>Or Use Custom Keys</h6>
                    <p>You can also enter API keys directly in the dashboard interface above.</p>
                    
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> 
                        API keys are validated for format but not stored permanently in the system.
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal (using Bootstrap)
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Remove modal when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// API Management
async function testAPI() {
    const provider = document.getElementById('apiProvider').value;
    const apiKey = document.getElementById('apiKey').value;
    const resultDiv = document.getElementById('apiTestResult');
    
    if (!apiKey) {
        showNotification('Please enter an API key', 'warning');
        return;
    }
    
    updateStatus('apiStatus', 'loading');
    resultDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Testing...</span></div>';
    
    try {
        const response = await fetch('/api/test-provider', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                provider: provider,
                api_key: apiKey 
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateStatus('apiStatus', 'active');
            updateStatus('ragStatus', 'active');
            resultDiv.innerHTML = `<div class="alert alert-success"><i class="fas fa-check-circle"></i> ${result.message}</div>`;
            showNotification(`${provider.charAt(0).toUpperCase() + provider.slice(1)} API key is working`, 'success');
        } else {
            updateStatus('apiStatus', 'error');
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> API test failed: ${result.error}</div>`;
            showNotification('API key test failed', 'danger');
        }
    } catch (error) {
        updateStatus('apiStatus', 'error');
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Network error: ${error.message}</div>`;
        showNotification('Network error', 'danger');
    }
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
            resultDiv.innerHTML = `<div class="alert alert-success"><i class="fas fa-check-circle"></i> File uploaded successfully!</div>`;
            
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
    if (!data || data.length === 0) return '<p>No data to display</p>';
    
    let html = '<div class="table-responsive"><table class="table table-striped table-hover"><thead><tr>';
    
    // Headers
    Object.keys(data[0]).forEach(key => {
        html += `<th>${key}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Rows
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
                <h6><i class="fas fa-database"></i> Dataset Overview</h6>
                <pre>${JSON.stringify(result.overview, null, 2)}</pre>
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

async function cleanData() {
    const provider = document.getElementById('apiProvider').value;
    const apiKey = document.getElementById('apiKey').value;
    
    if (!apiKey) {
        showNotification('API key required for data cleaning', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/dashboard/clean-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                api_key: apiKey,
                provider: provider 
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const resultsDiv = document.getElementById('cleaningResults');
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
                <div class="alert alert-info">
                    <strong>Cleaned file saved as:</strong> ${result.cleaned_filename}
                </div>
            `;
            showNotification('Data cleaning completed', 'success');
        } else {
            showNotification('Data cleaning failed', 'danger');
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
    let html = '<div class="row">';
    let count = 0;
    
    for (const [key, value] of Object.entries(kpis)) {
        if (count > 0 && count % 4 === 0) {
            html += '</div><div class="row">';
        }
        
        if (typeof value === 'number') {
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
                // Multiple figures
                let html = '<div class="row">';
                result.figures.forEach((fig, index) => {
                    html += `
                        <div class="col-md-6 mb-3">
                            <div class="chart-container">
                                <h6>${fig.name}</h6>
                                <canvas id="chart-${index}"></canvas>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
                
                // Create charts
                setTimeout(() => {
                    result.figures.forEach((fig, index) => {
                        createChart(`chart-${index}`, fig);
                    });
                }, 100);
            } else if (result.figure) {
                // Single figure
                resultsDiv.innerHTML = `
                    <div class="chart-container">
                        <canvas id="mainChart"></canvas>
                    </div>
                `;
                setTimeout(() => {
                    createChart('mainChart', result.figure);
                }, 100);
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

function createChart(canvasId, figure) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !figure) return;
    
    // This is a simplified chart creation - in production, you'd use proper chart libraries
    const ctx = canvas.getContext('2d');
    
    // Create a simple bar chart as placeholder
    ctx.fillStyle = '#f16363';
    ctx.fillRect(50, 50, 200, 100);
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px Arial';
    ctx.fillText('Chart visualization', 60, 100);
}

// AI Functions
async function generateInsights() {
    // Use local LLM - no API key needed
    updateStatus('insightsStatus', 'loading');
    showLoading();
    
    try {
        const response = await fetch('/dashboard/generate-insights', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                use_local: true,
                local_model: document.getElementById('localModel').value
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateStatus('insightsStatus', 'active');
            const resultsDiv = document.getElementById('insightsResults');
            
            let html = '<div class="alert alert-success">';
            result.insights.forEach((insight, index) => {
                html += `
                    <div class="mb-2">
                        <h6><i class="fas fa-lightbulb"></i> Insight ${index + 1}</h6>
                        <p>${insight}</p>
                    </div>
                `;
            });
            html += '</div>';
            
            resultsDiv.innerHTML = html;
            showNotification('Local AI insights generated', 'success');
        } else {
            updateStatus('insightsStatus', 'error');
            showNotification('Local AI insights failed', 'danger');
        }
    } catch (error) {
        updateStatus('insightsStatus', 'error');
        showNotification('Error during insights generation', 'danger');
    }
    
    hideLoading();
}

async function askQuestion() {
    const question = document.getElementById('questionInput').value;
    
    if (!question) {
        showNotification('Question required', 'warning');
        return;
    }
    
    // Use local LLM - no API key needed
    updateStatus('chatStatus', 'loading');
    showLoading();
    
    try {
        const response = await fetch('/dashboard/ask-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                use_local: true,
                local_model: document.getElementById('localModel').value,
                question: question 
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            updateStatus('chatStatus', 'active');
            const resultsDiv = document.getElementById('chatResults');
            
            resultsDiv.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-question"></i> Your Question</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>Q:</strong> ${question}</p>
                        <hr>
                        <p><strong>A:</strong> ${result.answer}</p>
                        ${result.relevant_rules.length > 0 ? `
                            <details>
                                <summary><i class="fas fa-book"></i> Relevant Rules</summary>
                                <ul>
                                    ${result.relevant_rules.map(rule => `<li>${rule}</li>`).join('')}
                                </ul>
                            </details>
                        ` : ''}
                    </div>
                </div>
            `;
            
            // Clear question input
            document.getElementById('questionInput').value = '';
            showNotification('Local answer generated', 'success');
        } else {
            updateStatus('chatStatus', 'error');
            showNotification('Failed to generate answer', 'danger');
        }
    } catch (error) {
        updateStatus('chatStatus', 'error');
        showNotification('Network error', 'danger');
    }
    
    hideLoading();
}

// Utility Functions
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function updateStatus(elementId, status) {
    const element = document.getElementById(elementId);
    element.className = 'status-indicator';
    
    switch(status) {
        case 'active':
            element.classList.add('status-active');
            element.classList.remove('status-inactive', 'status-error');
            break;
        case 'loading':
            element.classList.add('status-inactive');
            element.classList.remove('status-active', 'status-error');
            break;
        case 'error':
            element.classList.add('status-error');
            element.classList.remove('status-active', 'status-inactive');
            break;
        default:
            element.classList.add('status-inactive');
            element.classList.remove('status-active', 'status-error');
    }
}

function showNotification(message, type) {
    // Create a simple notification (could be enhanced with a toast library)
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
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
