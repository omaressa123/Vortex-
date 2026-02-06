document.addEventListener("DOMContentLoaded", async () => {
    const fileId = localStorage.getItem('file_id');
    const templateImage = localStorage.getItem('template_image');
    const apiKey = localStorage.getItem('api_key');

    if (!fileId || !templateImage) {
        alert("No file or template selected. Redirecting to home.");
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch('/generate-dashboard', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: fileId,
                template_image: templateImage,
                api_key: apiKey
            })
        });

        const result = await response.json();

        if (response.ok) {
            renderDashboard(result);
        } else {
            alert("Error generating dashboard: " + result.error);
            window.location.href = "/";
        }

    } catch (e) {
        console.error(e);
        alert("Network Error: " + e.message);
    }
});

function renderDashboard(result) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';
    
    const template = result.template;
    const mapping = result.mapping;
    const data = result.data;
    
    document.getElementById('dashboardTitle').innerText = template.name;
    
    const kpiContainer = document.getElementById('kpiContainer');
    const chartContainer = document.getElementById('chartContainer');
    
    // Sort components by type for layout (KPIs first)
    const kpis = template.components.filter(c => c.type === 'kpi');
    const charts = template.components.filter(c => c.type !== 'kpi');
    
    // Render KPIs
    kpis.forEach(kpi => {
        const kpiData = data[kpi.id];
        if (kpiData) {
            const card = document.createElement('div');
            card.className = 'kpi-card';
            card.innerHTML = `
                <div class="kpi-value">${kpiData.value}</div>
                <div class="kpi-label">${kpiData.label || kpi.label}</div>
            `;
            kpiContainer.appendChild(card);
        }
    });
    
    // Render Charts
    charts.forEach(chart => {
        const chartData = data[chart.id];
        if (chartData && !chartData.error) {
            const card = document.createElement('div');
            card.className = 'chart-card';
            
            // Create Canvas
            const canvas = document.createElement('canvas');
            canvas.id = chart.id;
            card.appendChild(canvas);
            chartContainer.appendChild(card);
            
            // Render Chart.js
            new Chart(canvas, {
                type: chartData.type === 'line' ? 'line' : 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: chartData.datasets.map(ds => ({
                        ...ds,
                        backgroundColor: chartData.type === 'line' ? 'rgba(241, 99, 99, 0.2)' : 'rgba(241, 99, 99, 0.7)',
                        borderColor: '#f16363',
                        borderWidth: 2,
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: 'white' } },
                        title: { display: true, text: chart.label, color: 'white' }
                    },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        }
    });
}
