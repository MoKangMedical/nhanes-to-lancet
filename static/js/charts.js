
// NHANES Charts Module
function initCharts() {
    // Initialize Chart.js charts if present
    document.querySelectorAll('canvas[data-chart]').forEach(canvas => {
        const type = canvas.dataset.chart;
        const data = JSON.parse(canvas.dataset.chartData || '{}');
        if (typeof Chart !== 'undefined') {
            new Chart(canvas, { type, data, options: { responsive: true } });
        }
    });
}
document.addEventListener('DOMContentLoaded', initCharts);
