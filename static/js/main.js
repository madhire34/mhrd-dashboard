$(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('.filter-control').on('change', updateDashboard);
    // Only initialize if relevant elements exist on the page
    const hasAny = document.getElementById('map') || document.getElementById('enrollmentChart') || document.getElementById('scholarshipChart') || document.getElementById('filter-year');
    if (hasAny) {
        initializeDashboard();
    }
});

function initializeDashboard() {
    initializeMap();
    initializeEnrollmentChart();
    initializeScholarshipChart();
    updateDashboard();
}

function updateDashboard() {
    // If there are no dashboard controls on this page, skip
    if (!document.getElementById('filter-year')) return;
    const filters = getCurrentFilters();
    $('.dashboard-content').addClass('loading');
    
    $.ajax({
        url: '/api/data/',
        data: filters,
        dataType: 'json',
        success: function(data) {
            updateKPICards(data.summary);
            updateEnrollmentChart(data.trends);
            updateScholarshipChart(data.scholarships);
            updateInitiativesTable(data.initiatives);
            updateMap(data.map);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching dashboard data:', error);
            alert('Error loading dashboard data. Please try again.');
        },
        complete: function() {
            $('.dashboard-content').removeClass('loading');
        }
    });
}

function getCurrentFilters() {
    return {
        year: $('#filter-year').val(),
        state: $('#filter-state').val(),
        scheme: $('#filter-scheme').val(),
        category: $('#filter-category').val()
    };
}

function updateKPICards(data) {
    if (!data) return;
    $('.kpi-schools h3').text(data.schools.toLocaleString());
    $('.kpi-students h3').text(data.students.toLocaleString());
    $('.kpi-scholarships h3').text(data.scholarships.toLocaleString());
    $('.kpi-progress h3').text(data.avg_progress_pct + '%');
    $('.kpi-progress .progress-bar').css('width', data.avg_progress_pct + '%');
}

function initializeMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;
    const map = L.map(mapEl).setView([20.5937, 78.9629], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    window.dashboardMap = map;
    updateMap([]);
}

function updateMap(mapData) {
    const map = window.dashboardMap;
    if (!map) return; // no map on this page
    if (window.mapMarkers) {
        window.mapMarkers.forEach(marker => map.removeLayer(marker));
    }
    window.mapMarkers = [];
    
    mapData.forEach(item => {
        const popupContent = `
            <div class="map-popup">
                <h6>${item.state}</h6>
                <p>Schools: ${item.schools.toLocaleString()}</p>
                <p>Students: ${item.students.toLocaleString()}</p>
                <p>Scholarships: ${item.scholarships.toLocaleString()}</p>
                <div class="progress mt-2">
                    <div class="progress-bar" style="width: ${item.avg_progress}%"></div>
                </div>
                <small>Progress: ${item.avg_progress.toFixed(1)}%</small>
            </div>`;
        
        const marker = L.marker([item.lat, item.lng])
            .addTo(map)
            .bindPopup(popupContent);
        window.mapMarkers.push(marker);
    });
}

function initializeEnrollmentChart() {
    const canvas = document.getElementById('enrollmentChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    window.enrollmentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Primary',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Secondary',
                    data: [],
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Students' }
                },
                x: { title: { display: true, text: 'Month' } }
            }
        }
    });
}

function updateEnrollmentChart(data) {
    if (!data || !window.enrollmentChart) return;
    window.enrollmentChart.data.labels = data.labels;
    window.enrollmentChart.data.datasets[0].data = data.primary;
    window.enrollmentChart.data.datasets[1].data = data.secondary;
    window.enrollmentChart.update();
}

function initializeScholarshipChart() {
    const canvas = document.getElementById('scholarshipChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    window.scholarshipChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Number of Beneficiaries',
                data: [],
                backgroundColor: '#9b59b6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `Beneficiaries: ${ctx.raw.toLocaleString()}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Beneficiaries' },
                    ticks: { callback: v => v.toLocaleString() }
                },
                x: { title: { display: true, text: 'State' } }
            }
        }
    });
}

function updateScholarshipChart(data) {
    if (!data || !window.scholarshipChart) return;
    window.scholarshipChart.data.labels = data.states;
    window.scholarshipChart.data.datasets[0].data = data.values;
    window.scholarshipChart.update();
}

function updateInitiativesTable(initiatives) {
    const tbody = $('#initiativesTable tbody');
    tbody.empty();
    
    initiatives.forEach(initiative => {
        tbody.append(`
            <tr>
                <td>${initiative.name}</td>
                <td>${initiative.state}</td>
                <td>${initiative.scheme}</td>
                <td>${initiative.year}</td>
                <td>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${initiative.progress_pct}%" 
                             aria-valuenow="${initiative.progress_pct}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                    <small>${initiative.progress_pct}%</small>
                </td>
                <td>${initiative.schools_impacted.toLocaleString()}</td>
                <td>${initiative.students_impacted.toLocaleString()}</td>
            </tr>`);
    });
}

function exportToCSV() {
    const filters = getCurrentFilters();
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
    });
    
    window.location.href = `/reports/download/${params.toString() ? '?' + params.toString() : ''}`;
}
