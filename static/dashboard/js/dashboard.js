const numberFormatter = new Intl.NumberFormat("en-IN");

function parseInitialData() {
    const script = document.getElementById("initial-dashboard-data");
    if (!script) return null;
    try {
        return JSON.parse(script.textContent);
    } catch (error) {
        console.error("Initial data parse error", error);
        return null;
    }
}

function colorScale(val, max) {
    const t = max > 0 ? val / max : 0;
    const c = Math.floor(200 * t) + 30;
    return `rgb(30, ${60 + Math.floor(100 * t)}, ${c})`;
}

function normalizeStateName(name) {
    return (name || '').toLowerCase().replace(/[^a-z]/g, '');
}

document.addEventListener("DOMContentLoaded", () => {
    const initialPayload = parseInitialData();
    if (!initialPayload) return;

    const form = document.getElementById("filters-form");
    const selects = form?.querySelectorAll("select") || [];
    const downloadLink = document.getElementById("download-report");
    const enrollmentCtx = document.getElementById("enrollment-chart")?.getContext("2d");
    const scholarshipCtx = document.getElementById("scholarship-chart")?.getContext("2d");
    
    if (!enrollmentCtx || !scholarshipCtx) return;

    const enrollmentChart = new Chart(enrollmentCtx, {
        type: "line",
        data: {
            labels: initialPayload.trends.labels,
            datasets: [{
                label: "Primary",
                data: initialPayload.trends.primary,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                tension: 0.4,
                fill: true,
                pointRadius: 4
            }, {
                label: "Secondary",
                data: initialPayload.trends.secondary,
                borderColor: "#22c55e",
                backgroundColor: "rgba(34, 197, 94, 0.15)",
                tension: 0.4,
                fill: true,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { callback: v => numberFormatter.format(v) } } },
            plugins: { legend: { display: false } }
        }
    });

    const scholarshipChart = new Chart(scholarshipCtx, {
        type: "bar",
        data: {
            labels: initialPayload.scholarships.states,
            datasets: [{
                label: "Beneficiaries",
                data: initialPayload.scholarships.values,
                backgroundColor: "#3b82f6",
                borderRadius: 12,
                barThickness: 38
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { callback: v => numberFormatter.format(v) } } },
            plugins: { legend: { display: false } }
        }
    });

    const mapEl = document.getElementById("state-map");
    if (!mapEl) {
        console.warn('state-map container not found; skipping map init');
        return; // prevent Leaflet error on pages without the container
    }
    const map = L.map(mapEl, {
        center: [21.1458, 79.0882],
        zoom: 5,
        scrollWheelZoom: false,
        attributionControl: false
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18 }).addTo(map);
    const markersLayer = L.layerGroup().addTo(map);
    let geoLayer = null;

    async function populateChoropleth(metric = "students") {
        try {
            const loadGeo = async () => {
                try {
                    const resp = await fetch("/static/geo/india_states.geojson");
                    if (resp.ok) return await resp.json();
                } catch (_) {}
                try {
                    const resp2 = await fetch("/static/geo/india_states_demo.geojson");
                    if (resp2.ok) return await resp2.json();
                } catch (_) {}
                return null; // trigger marker fallback
            };

            const [geo, data] = await Promise.all([
                loadGeo(),
                fetch(`/api/v1/map?${buildQueryString()}`).then(r => r.json())
            ]);

            if (!geo) {
                // Fallback: draw circle markers using payload.map points
                try {
                    const payload = await fetch(`/api/data/?${buildQueryString()}`).then(r => r.json());
                    populateMap(payload.map || []);
                } catch(err) {
                    console.warn('Map fallback failed', err);
                }
                return;
            }

            const valuesByState = {};
            let max = 0;
            
            (data.choropleth || []).forEach(row => {
                const val = {
                    schools: row.schools,
                    scholarships: row.scholarships,
                    progress: row.avg_progress,
                    students: row.students
                }[metric] || 0;
                
                valuesByState[normalizeStateName(row.state)] = val;
                if (val > max) max = val;
            });

            if (geoLayer) {
                map.removeLayer(geoLayer);
                geoLayer = null;
            }

            geoLayer = L.geoJSON(geo, {
                style: feature => {
                    const props = feature.properties || {};
                    const st = props.state || props.NAME_1 || props.st_nm || props.State_Name || '';
                    const val = valuesByState[normalizeStateName(st)] || 0;
                    return {
                        fillColor: colorScale(val, max),
                        weight: 1,
                        color: '#ffffff',
                        fillOpacity: 0.7
                    };
                },
                onEachFeature: (feature, layer) => {
                    const props = feature.properties || {};
                    const st = props.state || props.NAME_1 || props.st_nm || props.State_Name || '';
                    const val = valuesByState[normalizeStateName(st)] || 0;
                    layer.bindPopup(`<strong>${st}</strong><br>${metric}: ${numberFormatter.format(val)}`);
                }
            }).addTo(map);

            try {
                map.fitBounds(geoLayer.getBounds(), { padding: [30, 30] });
            } catch (e) {}
        } catch (e) {
            console.warn("Choropleth error", e);
            // Last resort: try points
            try {
                const payload = await fetch(`/api/data/?${buildQueryString()}`).then(r => r.json());
                populateMap(payload.map || []);
            } catch(_) {}
        }
    }

    function populateMap(points = []) {
        if (geoLayer) {
            map.removeLayer(geoLayer);
            geoLayer = null;
        }
        
        markersLayer.clearLayers();
        if (!points.length) return;

        points.forEach(point => {
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 14,
                fillColor: "#3b82f6",
                fillOpacity: 0.75,
                color: "#1d4ed8",
                weight: 2
            });
            
            marker.bindPopup(`
                <strong>${point.state}</strong><br>
                Schools: ${numberFormatter.format(point.schools)}<br>
                Students: ${numberFormatter.format(point.students)}<br>
                Scholarships: ${numberFormatter.format(point.scholarships)}<br>
                Avg Progress: ${(point.avg_progress * 100).toFixed(0)}%
            `).addTo(markersLayer);
        });

        const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]));
        if (bounds.isValid()) {
            map.fitBounds(bounds.pad(0.35));
        }
    }

    function updateKpis(summary) {
        const kpiContainer = document.getElementById("kpi-cards");
        if (!kpiContainer) return;
        
        const updateKPI = (id, value) => {
            const el = kpiContainer.querySelector(`[data-kpi="${id}"]`);
            if (el) el.textContent = id === 'progress' 
                ? `${Number(value).toFixed(2)}%` 
                : numberFormatter.format(value);
        };
        
        updateKPI('schools', summary.schools);
        updateKPI('students', summary.students);
        updateKPI('scholarships', summary.scholarships);
        updateKPI('progress', summary.avg_progress_pct);
    }

    function updateInitiativesTable(initiatives = []) {
        const tbody = document.getElementById("initiatives-body");
        if (!tbody) return;
        
        tbody.innerHTML = initiatives.length ? initiatives.map(item => `
            <tr>
                <td>${item.name}</td>
                <td>${item.state}</td>
                <td>${item.scheme}</td>
                <td>${item.category}</td>
                <td>${item.year}</td>
                <td><span class="status status--${String(item.status).toLowerCase().replace(/\s+/g, "-")}">${item.status}</span></td>
                <td>${Number(item.progress_pct).toFixed(2)}%</td>
            </tr>`).join('') : 
            '<tr><td colspan="7" class="empty">No initiatives match the current filters.</td></tr>';
    }

    function buildQueryString() {
        const params = new URLSearchParams();
        selects.forEach(select => {
            if (select.value) params.append(select.name, select.value);
        });
        return params.toString();
    }

    function updateDownloadLink() {
        if (!downloadLink) return;
        const baseUrl = downloadLink.dataset.baseUrl || downloadLink.href.split("?")[0];
        const query = buildQueryString();
        downloadLink.dataset.baseUrl = baseUrl;
        downloadLink.href = query ? `${baseUrl}?${query}` : baseUrl;
    }

    async function refreshDashboard() {
        const query = buildQueryString();
        const url = `/api/data/${query ? `?${query}` : ''}`;
        
        try {
            const response = await fetch(url, { headers: { Accept: "application/json" } });
            if (!response.ok) throw new Error(`Failed to fetch data (${response.status})`);
            
            const payload = await response.json();
            updateKpis(payload.summary);
            
            enrollmentChart.data.labels = payload.trends.labels;
            enrollmentChart.data.datasets[0].data = payload.trends.primary;
            enrollmentChart.data.datasets[1].data = payload.trends.secondary;
            enrollmentChart.update();

            scholarshipChart.data.labels = payload.scholarships.states;
            scholarshipChart.data.datasets[0].data = payload.scholarships.values;
            scholarshipChart.update();

            const metric = document.getElementById('map-metric')?.value || 'students';
            await populateChoropleth(metric);
            updateInitiativesTable(payload.initiatives);
            updateDownloadLink();
        } catch (error) {
            console.error("Dashboard refresh error:", error);
        }
    }

    selects.forEach(select => select.addEventListener("change", refreshDashboard));
    
    const metricSel = document.getElementById('map-metric');
    if (metricSel) {
        metricSel.addEventListener('change', () => populateChoropleth(metricSel.value));
    }

    (async () => {
        const metric = document.getElementById('map-metric')?.value || 'students';
        await populateChoropleth(metric);
        updateDownloadLink();
    })();
});

