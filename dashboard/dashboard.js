// Configuration
const API_BASE_URL = 'api/metrics';

// Chart instances
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    loadAllData();
    
    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadAllData();
    });
    
    // Auto-refresh every 60 seconds
    setInterval(loadAllData, 60000);
});

// Load all dashboard data
async function loadAllData() {
    try {
        await Promise.all([
            loadDashboardSummary(),
            loadPeakHours(),
            loadMessageVolume(),
            loadResponseTimeHourly(),
            loadErrorsSummary(),
            loadUserStats(),
            loadUnregisteredPhones(),
            loadRecentErrors()
        ]);
        
        updateLastUpdated();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent = 
        `Last updated: ${now.toLocaleTimeString()}`;
}

// API calls
async function fetchAPI(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
}

// Load dashboard summary
async function loadDashboardSummary() {
    try {
        const data = await fetchAPI('/dashboard');
        
        document.getElementById('total-messages').textContent = 
            data.messages.total_24h.toLocaleString();
        document.getElementById('avg-response').textContent = 
            `${data.response_time.avg_ms} ms`;
        document.getElementById('total-errors').textContent = 
            data.errors.total.toLocaleString();
        document.getElementById('access-denied').textContent = 
            data.access_denied.unique_numbers.toLocaleString();
        
        // Update response time distribution chart
        updateResponseDistributionChart(data.response_time);
    } catch (error) {
        console.error('Error loading dashboard summary:', error);
    }
}

// Load peak hours
async function loadPeakHours() {
    try {
        const data = await fetchAPI('/peak-hours');
        
        // Sort by hour
        data.sort((a, b) => a.hour_of_day - b.hour_of_day);
        
        const labels = data.map(d => `${d.hour_of_day}:00`);
        const interactions = data.map(d => d.interaction_count);
        const users = data.map(d => d.unique_users);
        
        updateChart('peak-hours-chart', {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Interactions',
                        data: interactions,
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Unique Users',
                        data: users,
                        backgroundColor: 'rgba(139, 92, 246, 0.8)',
                        borderColor: 'rgba(139, 92, 246, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading peak hours:', error);
    }
}

// Load message volume
async function loadMessageVolume() {
    try {
        const data = await fetchAPI('/volume?hours=24');
        
        const labels = data.map(d => new Date(d.hour).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        }));
        const counts = data.map(d => d.count);
        
        updateChart('message-volume-chart', {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Messages',
                    data: counts,
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
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
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading message volume:', error);
    }
}

// Load response time hourly
async function loadResponseTimeHourly() {
    try {
        const data = await fetchAPI('/response-time/hourly?hours=24');
        
        const labels = data.map(d => new Date(d.hour).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        }));
        const avgTimes = data.map(d => d.avg_ms);
        
        updateChart('response-time-chart', {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Avg Response Time (ms)',
                    data: avgTimes,
                    borderColor: 'rgba(245, 158, 11, 1)',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4
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
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading response time hourly:', error);
    }
}

// Load errors summary
async function loadErrorsSummary() {
    try {
        const data = await fetchAPI('/errors?days=7');
        
        // Errors by type
        const typeLabels = Object.keys(data.by_type);
        const typeCounts = Object.values(data.by_type);
        
        updateChart('errors-type-chart', {
            type: 'doughnut',
            data: {
                labels: typeLabels,
                datasets: [{
                    data: typeCounts,
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Errors by severity
        const severityLabels = Object.keys(data.by_severity);
        const severityCounts = Object.values(data.by_severity);
        
        updateChart('errors-severity-chart', {
            type: 'bar',
            data: {
                labels: severityLabels,
                datasets: [{
                    label: 'Count',
                    data: severityCounts,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(249, 115, 22, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderWidth: 1
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
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading errors summary:', error);
    }
}

// Update response distribution chart
function updateResponseDistributionChart(data) {
    updateChart('response-distribution-chart', {
        type: 'bar',
        data: {
            labels: ['Min', 'P50', 'Avg', 'P95', 'P99', 'Max'],
            datasets: [{
                label: 'Response Time (ms)',
                data: [
                    data.min_ms,
                    data.p50_ms,
                    data.avg_ms,
                    data.p95_ms,
                    data.p99_ms,
                    data.max_ms
                ],
                backgroundColor: 'rgba(139, 92, 246, 0.8)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 1
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
                    beginAtZero: true
                }
            }
        }
    });
}

// Load user stats
async function loadUserStats() {
    try {
        const data = await fetchAPI('/user-stats');
        
        const tbody = document.querySelector('#user-stats-table tbody');
        tbody.innerHTML = '';
        
        // Show top 10 users by message count
        const topUsers = data
            .sort((a, b) => b.total_messages - a.total_messages)
            .slice(0, 10);
        
        topUsers.forEach(user => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${user.name || 'N/A'}</td>
                <td>${user.phone_number}</td>
                <td>${user.total_messages}</td>
                <td>${user.total_warnings}</td>
            `;
        });
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

// Load unregistered phones
async function loadUnregisteredPhones() {
    try {
        const data = await fetchAPI('/unregistered-phones');
        
        const tbody = document.querySelector('#unregistered-phones-table tbody');
        tbody.innerHTML = '';
        
        // Show top 10
        const topPhones = data.slice(0, 10);
        
        topPhones.forEach(phone => {
            const row = tbody.insertRow();
            const lastAttempt = phone.last_attempt ? 
                new Date(phone.last_attempt).toLocaleString() : 'N/A';
            
            row.innerHTML = `
                <td>${phone.phone_number}</td>
                <td>${phone.attempt_count}</td>
                <td>${phone.channel}</td>
                <td>${lastAttempt}</td>
            `;
        });
        
        if (topPhones.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">No unregistered phones</td></tr>';
        }
    } catch (error) {
        console.error('Error loading unregistered phones:', error);
    }
}

// Load recent errors
async function loadRecentErrors() {
    try {
        const data = await fetchAPI('/errors/recent?limit=20');
        
        const tbody = document.querySelector('#recent-errors-table tbody');
        tbody.innerHTML = '';
        
        data.forEach(error => {
            const row = tbody.insertRow();
            const time = error.created_at ? 
                new Date(error.created_at).toLocaleString() : 'N/A';
            
            row.innerHTML = `
                <td>${time}</td>
                <td>${error.type}</td>
                <td><span class="severity-badge severity-${error.severity}">${error.severity}</span></td>
                <td>${error.message}</td>
                <td>${error.phone_number || 'N/A'}</td>
                <td>${error.channel || 'N/A'}</td>
            `;
        });
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No recent errors</td></tr>';
        }
    } catch (error) {
        console.error('Error loading recent errors:', error);
    }
}

// Initialize all charts
function initializeCharts() {
    const chartIds = [
        'peak-hours-chart',
        'message-volume-chart',
        'response-time-chart',
        'errors-type-chart',
        'errors-severity-chart',
        'response-distribution-chart'
    ];
    
    chartIds.forEach(id => {
        const ctx = document.getElementById(id);
        if (ctx) {
            charts[id] = null;
        }
    });
}

// Update or create chart
function updateChart(chartId, config) {
    const ctx = document.getElementById(chartId);
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts[chartId]) {
        charts[chartId].destroy();
    }
    
    // Create new chart
    charts[chartId] = new Chart(ctx, config);
}
