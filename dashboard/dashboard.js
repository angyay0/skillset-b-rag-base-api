// Configuration
const API_BASE_URL = 'https://blinky-base-api-202115206437.us-east4.run.app/api/metrics';

// Chart instances
let charts = {};

// Current language
let currentLanguage = localStorage.getItem('dashboardLanguage') || 'en';

// Current date filter
let currentFromDate = null;

// Translations
const translations = {
    en: {
        dashboard: {
            title: '📊 Blinky Metrics Dashboard',
            lastUpdated: 'Last updated:',
            refresh: '🔄 Refresh',
            fromDate: 'From:',
            clearDate: 'Clear',
            logout: '🚪 Logout'
        },
        cards: {
            totalMessages: 'Total Messages (24h)',
            last24h: 'Last 24 hours',
            avgResponse: 'Avg Response Time',
            milliseconds: 'Milliseconds',
            totalErrors: 'Total Errors (7d)',
            last7days: 'Last 7 days',
            accessDenied: 'Access Denied',
            uniqueNumbers: 'Unique numbers'
        },
        charts: {
            peakHours: 'Peak Interaction Hours',
            messageVolume: 'Message Volume (24h)',
            responseTime: 'Response Time by Hour',
            errorsByType: 'Errors by Type',
            errorsBySeverity: 'Errors by Severity',
            responseDistribution: 'Response Time Distribution'
        },
        tables: {
            userStats: '👥 User Statistics',
            unregisteredPhones: '📱 Unregistered Phone Numbers',
            recentErrors: '🔴 Recent Errors',
            frequentQuestions: '❓ Most Frequent Questions'
        },
        table: {
            name: 'Name',
            phoneNumber: 'Phone Number',
            messages: 'Messages',
            warnings: 'Warnings',
            attempts: 'Attempts',
            channel: 'Channel',
            lastAttempt: 'Last Attempt',
            time: 'Time',
            type: 'Type',
            severity: 'Severity',
            message: 'Message',
            phone: 'Phone',
            question: 'Question',
            frequency: 'Frequency',
            uniqueUsers: 'Unique Users',
            firstAsked: 'First Asked',
            lastAsked: 'Last Asked'
        }
    },
    es: {
        dashboard: {
            title: '📊 Panel de Métricas Blinky',
            lastUpdated: 'Última actualización:',
            refresh: '🔄 Actualizar',
            fromDate: 'Desde:',
            clearDate: 'Limpiar',
            logout: '🚪 Cerrar Sesión'
        },
        cards: {
            totalMessages: 'Mensajes Totales (24h)',
            last24h: 'Últimas 24 horas',
            avgResponse: 'Tiempo de Respuesta Promedio',
            milliseconds: 'Milisegundos',
            totalErrors: 'Errores Totales (7d)',
            last7days: 'Últimos 7 días',
            accessDenied: 'Acceso Denegado',
            uniqueNumbers: 'Números únicos'
        },
        charts: {
            peakHours: 'Horas Pico de Interacción',
            messageVolume: 'Volumen de Mensajes (24h)',
            responseTime: 'Tiempo de Respuesta por Hora',
            errorsByType: 'Errores por Tipo',
            errorsBySeverity: 'Errores por Severidad',
            responseDistribution: 'Distribución de Tiempo de Respuesta'
        },
        tables: {
            userStats: '👥 Estadísticas de Usuarios',
            unregisteredPhones: '📱 Números de Teléfono No Registrados',
            recentErrors: '🔴 Errores Recientes',
            frequentQuestions: '❓ Preguntas Más Frecuentes'
        },
        table: {
            name: 'Nombre',
            phoneNumber: 'Número de Teléfono',
            messages: 'Mensajes',
            warnings: 'Advertencias',
            attempts: 'Intentos',
            channel: 'Canal',
            lastAttempt: 'Último Intento',
            time: 'Hora',
            type: 'Tipo',
            severity: 'Severidad',
            message: 'Mensaje',
            phone: 'Teléfono',
            question: 'Pregunta',
            frequency: 'Frecuencia',
            uniqueUsers: 'Usuarios Únicos',
            firstAsked: 'Primera Vez',
            lastAsked: 'Última Vez'
        }
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    loadAllData();
    
    // Set up language selector
    const languageSelector = document.getElementById('language-selector');
    languageSelector.value = currentLanguage;
    languageSelector.addEventListener('change', (e) => {
        currentLanguage = e.target.value;
        localStorage.setItem('dashboardLanguage', currentLanguage);
        applyTranslations();
    });
    
    // Set up date filter
    const fromDateInput = document.getElementById('from-date');
    fromDateInput.addEventListener('change', (e) => {
        currentFromDate = e.target.value || null;
        loadAllData();
    });
    
    // Set up clear date button
    document.getElementById('clear-date-btn').addEventListener('click', () => {
        fromDateInput.value = '';
        currentFromDate = null;
        loadAllData();
    });
    
    // Apply initial translations
    applyTranslations();
    
    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadAllData();
    });
    
    // Set up logout button
    document.getElementById('logout-btn').addEventListener('click', () => {
        if (confirm(currentLanguage === 'es' ? '¿Estás seguro de que quieres cerrar sesión?' : 'Are you sure you want to logout?')) {
            logout();
        }
    });
    
    // Auto-refresh every 60 seconds
    setInterval(loadAllData, 60000);
});

// Apply translations to all elements with data-i18n attribute
function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const keys = key.split('.');
        let translation = translations[currentLanguage];
        
        for (const k of keys) {
            translation = translation[k];
            if (!translation) break;
        }
        
        if (translation) {
            element.textContent = translation;
        }
    });
    
    // Update last updated text
    updateLastUpdated();
}

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
            loadRecentErrors(),
            loadFrequentQuestions()
        ]);
        
        updateLastUpdated();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    const prefix = translations[currentLanguage].dashboard.lastUpdated;
    document.getElementById('last-updated').textContent = 
        `${prefix} ${now.toLocaleTimeString()}`;
}

// API calls
async function fetchAPI(endpoint) {
    // Add from_date parameter if set
    let url = `${API_BASE_URL}${endpoint}`;
    if (currentFromDate) {
        const separator = endpoint.includes('?') ? '&' : '?';
        url += `${separator}from_date=${currentFromDate}`;
    }
    
    const response = await fetch(url);
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

// Load frequent questions
async function loadFrequentQuestions() {
    try {
        const data = await fetchAPI('/frequent-questions?limit=15');
        
        const tbody = document.querySelector('#frequent-questions-table tbody');
        tbody.innerHTML = '';
        
        data.forEach(item => {
            const row = tbody.insertRow();
            const firstAsked = item.first_asked ? 
                new Date(item.first_asked).toLocaleDateString() : 'N/A';
            const lastAsked = item.last_asked ? 
                new Date(item.last_asked).toLocaleDateString() : 'N/A';
            
            // Truncate long questions
            const questionText = item.question_text.length > 100 ? 
                item.question_text.substring(0, 100) + '...' : 
                item.question_text;
            
            row.innerHTML = `
                <td title="${item.question_text}">${questionText}</td>
                <td>${item.frequency}</td>
                <td>${item.unique_users}</td>
                <td>${firstAsked}</td>
                <td>${lastAsked}</td>
            `;
        });
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No frequent questions found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading frequent questions:', error);
        const tbody = document.querySelector('#frequent-questions-table tbody');
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Error loading data</td></tr>';
    }
}
