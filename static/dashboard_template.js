// Chart defaults
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";

// Data processing functions
function processDataForDashboard(data) {
    console.log('Processing data for dashboard, input:', data);
    
    if (!data || data.length === 0) {
        console.log('No data available, using defaults');
        return generateDefaultData();
    }

    console.log('Data available, processing...');
    console.log('First row:', data[0]);
    console.log('Data length:', data.length);

    // Analyze data structure and extract insights
    const numericColumns = Object.keys(data[0]).filter(key => {
        const value = data[0][key];
        const isNumeric = typeof value === 'number' || !isNaN(parseFloat(value));
        console.log(`Column ${key}: ${value} -> numeric: ${isNumeric}`);
        return isNumeric;
    });
    
    const categoricalColumns = Object.keys(data[0]).filter(key => {
        const value = data[0][key];
        const isString = typeof value === 'string';
        console.log(`Column ${key}: ${value} -> string: ${isString}`);
        return isString;
    });

    console.log('Numeric columns:', numericColumns);
    console.log('Categorical columns:', categoricalColumns);

    const result = {
        kpi: calculateKPIs(data, numericColumns),
        gender: analyzeGender(data, categoricalColumns),
        age: analyzeAge(data, categoricalColumns),
        customers: analyzeCustomers(data, categoricalColumns, numericColumns),
        trends: analyzeTrends(data, categoricalColumns, numericColumns),
        weekday: analyzeWeekday(data, categoricalColumns, numericColumns),
        categories: analyzeCategories(data, categoricalColumns, numericColumns)
    };

    console.log('Processed result:', result);
    return result;
}

function generateDefaultData() {
    return {
        kpi: {
            cogs: 3100000,
            revenue: 5400000,
            profit: 2300000,
            profitMargin: 42.18
        },
        gender: { male: 51.47, female: 48.53 },
        age: { labels: ['0-20', '21-30', '31-40', '41-50', '51+'], data: [41.2, 72.7, 421.5, 504.1, 598.0] },
        customers: { labels: ['John Brown', 'Paul Nash', 'Laura Gross', 'Judith Simmons', 'Kristine Barrett'], data: [8, 8, 7, 7, 7] },
        trends: { labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], data: [7.74, 7.74, 8.90, 8.40, 8.95, 7.95, 9.08, 8.27, 8.29, 8.37, 7.81, 0] },
        weekday: { labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], data: [313.4, 324.3, 324.2, 313.6, 340.7, 319.6, 332.5] },
        categories: [
            { name: 'Soft Drink', value: 216216 },
            { name: 'Sports Drink', value: 317424 },
            { name: 'Tea', value: 67414 },
            { name: 'Water', value: 325210 },
            { name: 'Energy Drink', value: 74073 },
            { name: 'Coffee', value: 142232 },
            { name: 'Alcoholic Beverage', value: 86449 },
            { name: 'Juice', value: 42455 }
        ]
    };
}

function calculateKPIs(data, numericColumns) {
    console.log('Calculating KPIs with numeric columns:', numericColumns);
    
    if (numericColumns.length === 0) {
        console.log('No numeric columns found, using default KPIs');
        return { cogs: 3100000, revenue: 5400000, profit: 2300000, profitMargin: 42.18 };
    }

    // Try to identify common financial columns
    const revenueCol = findColumn(numericColumns, ['revenue', 'sales', 'total', 'amount']);
    const costCol = findColumn(numericColumns, ['cost', 'cogs', 'expense']);
    
    console.log('Found revenue column:', revenueCol);
    console.log('Found cost column:', costCol);
    
    const revenue = revenueCol ? data.reduce((sum, row) => sum + (parseFloat(row[revenueCol]) || 0), 0) : 5400000;
    const cost = costCol ? data.reduce((sum, row) => sum + (parseFloat(row[costCol]) || 0), 0) : 3100000;
    const profit = revenue - cost;
    const margin = revenue > 0 ? (profit / revenue * 100) : 42.18;

    console.log('Calculated - Revenue:', revenue, 'Cost:', cost, 'Profit:', profit, 'Margin:', margin);

    return {
        cogs: cost,
        revenue: revenue,
        profit: profit,
        profitMargin: margin
    };
}

function analyzeGender(data, categoricalColumns) {
    console.log('Analyzing gender with categorical columns:', categoricalColumns);
    
    const genderCol = findColumn(categoricalColumns, ['gender', 'sex']);
    console.log('Found gender column:', genderCol);
    
    if (!genderCol) {
        console.log('No gender column found, using defaults');
        return { male: 51.47, female: 48.53 };
    }

    const counts = {};
    data.forEach(row => {
        const gender = (row[genderCol] || '').toLowerCase();
        console.log('Processing gender:', gender);
        if (gender.includes('m') || gender.includes('male')) counts.male = (counts.male || 0) + 1;
        else if (gender.includes('f') || gender.includes('female')) counts.female = (counts.female || 0) + 1;
    });

    const total = (counts.male || 0) + (counts.female || 0);
    const result = {
        male: total > 0 ? ((counts.male || 0) / total * 100) : 51.47,
        female: total > 0 ? ((counts.female || 0) / total * 100) : 48.53
    };
    
    console.log('Gender analysis result:', result);
    return result;
}

function analyzeAge(data, categoricalColumns) {
    const ageCol = findColumn(categoricalColumns, ['age']);
    if (!ageCol) {
        return { labels: ['0-20', '21-30', '31-40', '41-50', '51+'], data: [41.2, 72.7, 421.5, 504.1, 598.0] };
    }

    const ageGroups = { '0-20': 0, '21-30': 0, '31-40': 0, '41-50': 0, '51+': 0 };
    
    data.forEach(row => {
        const age = parseInt(row[ageCol]) || 0;
        if (age <= 20) ageGroups['0-20']++;
        else if (age <= 30) ageGroups['21-30']++;
        else if (age <= 40) ageGroups['31-40']++;
        else if (age <= 50) ageGroups['41-50']++;
        else ageGroups['51+']++;
    });

    return {
        labels: Object.keys(ageGroups),
        data: Object.values(ageGroups)
    };
}

function analyzeCustomers(data, categoricalColumns, numericColumns) {
    const customerCol = findColumn(categoricalColumns, ['customer', 'name', 'client']);
    const valueCol = findColumn(numericColumns, ['revenue', 'sales', 'total', 'amount', 'profit']);
    
    if (!customerCol || !valueCol) {
        return { labels: ['John Brown', 'Paul Nash', 'Laura Gross', 'Judith Simmons', 'Kristine Barrett'], data: [8, 8, 7, 7, 7] };
    }

    const customerValues = {};
    data.forEach(row => {
        const customer = row[customerCol];
        const value = parseFloat(row[valueCol]) || 0;
        if (customer) {
            customerValues[customer] = (customerValues[customer] || 0) + value;
        }
    });

    const sorted = Object.entries(customerValues)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    return {
        labels: sorted.map(item => item[0]),
        data: sorted.map(item => item[1] / 100000) // Scale down for display
    };
}

function analyzeTrends(data, categoricalColumns, numericColumns) {
    const dateCol = findColumn(categoricalColumns, ['date', 'time', 'month']);
    const valueCol = findColumn(numericColumns, ['revenue', 'sales', 'total', 'amount']);
    
    if (!dateCol || !valueCol) {
        return { labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], data: [7.74, 7.74, 8.90, 8.40, 8.95, 7.95, 9.08, 8.27, 8.29, 8.37, 7.81, 0] };
    }

    // Simple month aggregation
    const monthlyData = {};
    data.forEach(row => {
        const date = new Date(row[dateCol]);
        if (!isNaN(date)) {
            const month = date.toLocaleString('default', { month: 'short' });
            monthlyData[month] = (monthlyData[month] || 0) + (parseFloat(row[valueCol]) || 0);
        }
    });

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return {
        labels: months,
        data: months.map(month => monthlyData[month] || 0)
    };
}

function analyzeWeekday(data, categoricalColumns, numericColumns) {
    const dateCol = findColumn(categoricalColumns, ['date', 'time']);
    const valueCol = findColumn(numericColumns, ['revenue', 'sales', 'total', 'amount']);
    
    if (!dateCol || !valueCol) {
        return { labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], data: [313.4, 324.3, 324.2, 313.6, 340.7, 319.6, 332.5] };
    }

    const weekdayData = { 'Sun': 0, 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0 };
    
    data.forEach(row => {
        const date = new Date(row[dateCol]);
        if (!isNaN(date)) {
            const weekday = date.toLocaleString('default', { weekday: 'short' });
            weekdayData[weekday] = (weekdayData[weekday] || 0) + (parseFloat(row[valueCol]) || 0);
        }
    });

    return {
        labels: Object.keys(weekdayData),
        data: Object.values(weekdayData)
    };
}

function analyzeCategories(data, categoricalColumns, numericColumns) {
    const categoryCol = findColumn(categoricalColumns, ['category', 'product', 'type']);
    const valueCol = findColumn(numericColumns, ['revenue', 'sales', 'total', 'amount']);
    
    if (!categoryCol || !valueCol) {
        return [
            { name: 'Soft Drink', value: 216216 },
            { name: 'Sports Drink', value: 317424 },
            { name: 'Tea', value: 67414 },
            { name: 'Water', value: 325210 },
            { name: 'Energy Drink', value: 74073 },
            { name: 'Coffee', value: 142232 },
            { name: 'Alcoholic Beverage', value: 86449 },
            { name: 'Juice', value: 42455 }
        ];
    }

    const categoryValues = {};
    data.forEach(row => {
        const category = row[categoryCol];
        const value = parseFloat(row[valueCol]) || 0;
        if (category) {
            categoryValues[category] = (categoryValues[category] || 0) + value;
        }
    });

    return Object.entries(categoryValues)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 8);
}

function findColumn(columns, possibleNames) {
    for (const name of possibleNames) {
        const found = columns.find(col => col.toLowerCase().includes(name.toLowerCase()));
        if (found) return found;
    }
    return null;
}

// Initialize dashboard with data
let dashboardData;

// Load data from localStorage or use defaults
function loadDashboardData() {
    const storedData = localStorage.getItem('uploadedData');
    console.log('Loading dashboard data from localStorage:', storedData ? 'Found data' : 'No data found');
    
    if (storedData) {
        try {
            const parsedData = JSON.parse(storedData);
            console.log('Parsed data:', parsedData);
            console.log('Data length:', parsedData.length);
            console.log('Sample row:', parsedData[0]);
            
            dashboardData = processDataForDashboard(parsedData);
            console.log('Processed dashboard data:', dashboardData);
        } catch (e) {
            console.error('Error parsing stored data:', e);
            dashboardData = generateDefaultData();
        }
    } else {
        console.log('No stored data found, trying to fetch auto-visualization');
        // Try to fetch auto-visualization from server
        fetchAutoVisualization();
        return;
    }
    updateDashboard();
}

// Fetch auto-visualization from server
async function fetchAutoVisualization() {
    try {
        const response = await fetch('http://localhost:8000/visualize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                viz_type: 'auto'
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Auto-visualization result:', result);
            
            if (result.success && result.figures) {
                displayAutoFigures(result.figures);
            }
        }
    } catch (e) {
        console.error('Error fetching auto-visualization:', e);
        dashboardData = generateDefaultData();
        updateDashboard();
    }
}

// Display auto-generated figures
function displayAutoFigures(figures) {
    console.log('Displaying auto figures:', figures);
    
    // Create a section for auto figures if it doesn't exist
    let autoFiguresSection = document.getElementById('autoFiguresSection');
    if (!autoFiguresSection) {
        autoFiguresSection = document.createElement('div');
        autoFiguresSection.id = 'autoFiguresSection';
        autoFiguresSection.className = 'auto-figures-section';
        autoFiguresSection.innerHTML = '<h2 class="section-title">🔍 Auto-Generated Visualizations</h2>';
        
        // Insert after KPI cards
        const kpiCards = document.querySelector('.kpi-cards');
        kpiCards.parentNode.insertBefore(autoFiguresSection, kpiCards.nextSibling);
    }

    // Create figure containers
    let figuresHtml = '<div class="auto-figures-grid">';
    figures.forEach((fig, index) => {
        figuresHtml += `
            <div class="auto-figure-card">
                <h3 class="figure-title">Figure ${index + 1}</h3>
                <div class="chart-container" id="auto-chart-${index}">
                    <canvas id="auto-canvas-${index}"></canvas>
                </div>
            </div>
        `;
    });
    figuresHtml += '</div>';
    
    autoFiguresSection.innerHTML += figuresHtml;
    
    // Create charts
    setTimeout(() => {
        figures.forEach((fig, index) => {
            createAutoChart(`auto-canvas-${index}`, fig);
        });
    }, 100);
}

// Create chart for auto-generated figures
function createAutoChart(canvasId, fig) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Simple placeholder for matplotlib figures
    ctx.fillStyle = '#f16363';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Auto-Generated Chart', canvas.width / 2, canvas.height / 2);
    ctx.fillText(`${fig.type || 'Visualization'}`, canvas.width / 2, canvas.height / 2 + 30);
}

// Cash Flow Prediction Functions
async function addFinancialData() {
    const month = document.getElementById('monthInput').value;
    const income = parseFloat(document.getElementById('incomeInput').value) || 0;
    const expenses = parseFloat(document.getElementById('expensesInput').value) || 0;
    
    if (!month || income <= 0 || expenses <= 0) {
        alert('Please fill in all fields with valid values');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8001/financial/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                month: month,
                income: income,
                expenses: expenses
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear inputs
            document.getElementById('monthInput').value = '';
            document.getElementById('incomeInput').value = '';
            document.getElementById('expensesInput').value = '';
            
            // Refresh data and prediction
            await loadFinancialData();
            await getPrediction();
            
            console.log('✅ Financial data added successfully');
        } else {
            alert('Error adding financial data: ' + result.error);
        }
    } catch (error) {
        console.error('❌ Error adding financial data:', error);
        alert('Error adding financial data. Please try again.');
    }
}

async function loadFinancialData() {
    try {
        const response = await fetch('http://localhost:8001/financial/data');
        const result = await response.json();
        
        if (result.success) {
            displayHistoricalData(result.data);
        }
    } catch (error) {
        console.error('❌ Error loading financial data:', error);
    }
}

function displayHistoricalData(data) {
    const dataList = document.getElementById('dataList');
    
    if (data.length === 0) {
        dataList.innerHTML = '<p style="color: #666; text-align: center;">No historical data available. Add at least 2 months of data to enable predictions.</p>';
        return;
    }
    
    dataList.innerHTML = data.map(item => `
        <div class="data-item">
            <div class="data-month">${item.month}</div>
            <div class="data-values">
                <div class="data-value">
                    <span class="data-label">Income</span>
                    <span class="data-amount">$${item.income.toLocaleString()}</span>
                </div>
                <div class="data-value">
                    <span class="data-label">Expenses</span>
                    <span class="data-amount">$${item.expenses.toLocaleString()}</span>
                </div>
                <div class="data-value">
                    <span class="data-label">Profit</span>
                    <span class="data-amount ${item.profit >= 0 ? 'positive' : 'negative'}">
                        $${item.profit.toLocaleString()}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

async function getPrediction() {
    try {
        const response = await fetch('http://localhost:8001/financial/predict');
        const result = await response.json();
        
        if (result.success) {
            displayPrediction(result.prediction, result.insight);
        } else {
            // Hide prediction if not enough data
            document.getElementById('predictionResult').style.display = 'none';
            console.log('⚠️', result.error);
        }
    } catch (error) {
        console.error('❌ Error getting prediction:', error);
        document.getElementById('predictionResult').style.display = 'none';
    }
}

function displayPrediction(prediction, insight) {
    // Show prediction section
    document.getElementById('predictionResult').style.display = 'block';
    
    // Update prediction values
    document.getElementById('predIncome').textContent = `$${prediction.income.toLocaleString()}`;
    document.getElementById('predExpenses').textContent = `$${prediction.expenses.toLocaleString()}`;
    document.getElementById('predProfit').textContent = `$${prediction.profit.toLocaleString()}`;
    
    // Update change indicators
    document.getElementById('predIncomeChange').textContent = `${prediction.income_growth >= 0 ? '+' : ''}${prediction.income_growth}%`;
    document.getElementById('predExpensesChange').textContent = `${prediction.expense_growth >= 0 ? '+' : ''}${prediction.expense_growth}%`;
    document.getElementById('predProfitChange').textContent = `${prediction.profit >= 0 ? '+' : ''}${((prediction.profit / prediction.income) * 100).toFixed(1)}%`;
    
    // Update AI insight
    document.getElementById('insightText').textContent = insight;
    
    console.log('📈 Prediction displayed:', prediction);
    console.log('🤖 AI Insight:', insight);
}

// Initialize Cash Flow Prediction on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load existing financial data
    loadFinancialData();
    
    // Get prediction if data exists
    setTimeout(() => {
        getPrediction();
    }, 1000);
});

// Update dashboard UI with data
function updateDashboard() {
    // Update KPI cards
    updateKPIs();
    
    // Update charts
    updateCharts();
    
    // Update categories
    updateCategories();
    
    // Display file summary if available
    displayFileSummary();
}

// Display file summary information
function displayFileSummary() {
    if (!dashboardData || !dashboardData.file_summary) {
        return;
    }
    
    const summary = dashboardData.file_summary;
    console.log('📁 File summary:', summary);
    
    // Create or update file summary section
    let summarySection = document.getElementById('fileSummarySection');
    if (!summarySection) {
        summarySection = document.createElement('div');
        summarySection.id = 'fileSummarySection';
        summarySection.className = 'file-summary-section';
        summarySection.innerHTML = '<h3 class="section-title">📁 Data Sources</h3>';
        
        // Insert at the top of dashboard content
        const dashboardContent = document.querySelector('.dashboard-content');
        if (dashboardContent) {
            dashboardContent.insertBefore(summarySection, dashboardContent.firstChild);
        }
    }
    
    // Update summary content
    summarySection.innerHTML += `
        <div class="file-summary-content">
            <div class="summary-stats">
                <div class="stat-item">
                    <span class="stat-label">Total Files:</span>
                    <span class="stat-value">${summary.total_files}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Processed:</span>
                    <span class="stat-value">${summary.processed_files}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Rows:</span>
                    <span class="stat-value">${summary.total_rows.toLocaleString()}</span>
                </div>
            </div>
            <div class="file-list">
                <h4>Source Files:</h4>
                ${summary.files.map(file => `
                    <div class="file-item">
                        <span class="file-icon">📄</span>
                        <span class="file-name">${file}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function updateKPIs() {
    const kpi = dashboardData.kpi;
    
    // Update KPI values
    const kpiElements = document.querySelectorAll('.kpi-value');
    if (kpiElements.length >= 4) {
        kpiElements[0].textContent = formatCurrency(kpi.cogs);
        kpiElements[1].textContent = formatCurrency(kpi.revenue);
        kpiElements[2].textContent = formatCurrency(kpi.profit);
        kpiElements[3].textContent = kpi.profitMargin.toFixed(2) + '%';
    }
}

function updateCharts() {
    // Update Gender Chart
    updateGenderChart();
    
    // Update Age Chart
    updateAgeChart();
    
    // Update Customer Chart
    updateCustomerChart();
    
    // Update Trend Chart
    updateTrendChart();
    
    // Update Weekday Chart
    updateWeekdayChart();
}

function updateGenderChart() {
    const chart = Chart.getChart('genderChart');
    if (chart && dashboardData.gender) {
        const maleData = Array(8).fill(null).map(() => ({
            x: Math.random() * 100,
            y: Math.random() * 100,
            r: 8
        }));
        
        const femaleData = Array(8).fill(null).map(() => ({
            x: Math.random() * 100,
            y: Math.random() * 100,
            r: 8
        }));
        
        chart.data.datasets[0].data = maleData;
        chart.data.datasets[1].data = femaleData;
        chart.update();
        
        // Update legend
        const legends = document.querySelectorAll('.heatmap-legend span:last-child');
        if (legends.length >= 2) {
            legends[0].textContent = dashboardData.gender.male.toFixed(2) + '%';
            legends[1].textContent = dashboardData.gender.female.toFixed(2) + '%';
        }
    }
}

function updateAgeChart() {
    const chart = Chart.getChart('ageChart');
    if (chart && dashboardData.age) {
        chart.data.labels = dashboardData.age.labels;
        chart.data.datasets[0].data = dashboardData.age.data;
        chart.update();
    }
}

function updateCustomerChart() {
    const chart = Chart.getChart('topCustomerChart');
    if (chart && dashboardData.customers) {
        chart.data.labels = dashboardData.customers.labels;
        chart.data.datasets[0].data = dashboardData.customers.data;
        chart.update();
    }
}

function updateTrendChart() {
    const chart = Chart.getChart('trendChart');
    if (chart && dashboardData.trends) {
        chart.data.labels = dashboardData.trends.labels;
        chart.data.datasets[0].data = dashboardData.trends.data;
        chart.update();
    }
}

function updateWeekdayChart() {
    const chart = Chart.getChart('weekdayChart');
    if (chart && dashboardData.weekday) {
        chart.data.labels = dashboardData.weekday.labels;
        chart.data.datasets[0].data = dashboardData.weekday.data;
        chart.update();
    }
}

function updateCategories() {
    const categoryList = document.querySelector('.category-list');
    if (categoryList && dashboardData.categories) {
        categoryList.innerHTML = dashboardData.categories.map(cat => `
            <div class="category-item">
                <span class="category-name">${cat.name}</span>
                <span class="category-value">${formatCurrency(cat.value)}</span>
            </div>
        `).join('');
    }
}

function formatCurrency(value) {
    if (value >= 1000000) {
        return '$' + (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return '$' + (value / 1000).toFixed(0) + 'K';
    }
    return '$' + value.toFixed(0);
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', loadDashboardData);

// 1. Gender Distribution (as a simple heatmap representation)
const genderCtx = document.getElementById('genderChart').getContext('2d');
const genderChart = new Chart(genderCtx, {
    type: 'bubble',
    data: {
        datasets: [
            {
                label: 'Male',
                data: Array(8).fill(null).map(() => ({
                    x: Math.random() * 100,
                    y: Math.random() * 100,
                    r: 8
                })),
                backgroundColor: '#0066cc',
                opacity: 0.7
            },
            {
                label: 'Female',
                data: Array(8).fill(null).map(() => ({
                    x: Math.random() * 100,
                    y: Math.random() * 100,
                    r: 8
                })),
                backgroundColor: '#666666',
                opacity: 0.7
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                display: false,
                min: 0,
                max: 100
            },
            y: {
                display: false,
                min: 0,
                max: 100
            }
        }
    }
});

// 2. Profit by Customer Age
const ageCtx = document.getElementById('ageChart').getContext('2d');
const ageChart = new Chart(ageCtx, {
    type: 'bar',
    data: {
        labels: ['0-20', '21-30', '31-40', '41-50', '51+'],
        datasets: [{
            label: 'Profit',
            data: [41.2, 72.7, 421.5, 504.1, 598.0],
            backgroundColor: '#0066cc',
            borderRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        indexAxis: 'y',
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999'
                }
            },
            y: {
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#666'
                }
            }
        }
    }
});

// 3. Top-5 Profitable Customers
const topCustomerCtx = document.getElementById('topCustomerChart').getContext('2d');
const topCustomerChart = new Chart(topCustomerCtx, {
    type: 'bar',
    data: {
        labels: ['John Brown', 'Paul Nash', 'Laura Gross', 'Judith Simmons', 'Kristine Barrett'],
        datasets: [{
            label: 'Profit',
            data: [8, 8, 7, 7, 7],
            backgroundColor: '#0066cc',
            borderRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        indexAxis: 'y',
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                max: 10,
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999'
                }
            },
            y: {
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#666'
                }
            }
        }
    }
});

// 4. Profit Trend by Month
const trendCtx = document.getElementById('trendChart').getContext('2d');
const trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'Profit Rate %',
            data: [7.74, 7.74, 8.90, 8.40, 8.95, 7.95, 9.08, 8.27, 8.29, 8.37, 7.81, 0],
            borderColor: '#0066cc',
            backgroundColor: 'rgba(0, 102, 204, 0.05)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#0066cc',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#e0e0e0'
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999',
                    callback: function(value) {
                        return value + '%';
                    }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999'
                }
            }
        }
    }
});

// 5. Profit by WeekDay
const weekdayCtx = document.getElementById('weekdayChart').getContext('2d');
const weekdayChart = new Chart(weekdayCtx, {
    type: 'bar',
    data: {
        labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        datasets: [{
            label: 'Profit',
            data: [313.4, 324.3, 324.2, 313.6, 340.7, 319.6, 332.5],
            backgroundColor: '#0066cc',
            borderRadius: 4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#e0e0e0'
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999'
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 },
                    color: '#999'
                }
            }
        }
    }
});
