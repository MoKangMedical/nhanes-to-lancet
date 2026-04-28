/**
 * NHANES to Lancet - Chart Utilities
 * Professional data visualization for epidemiological research
 */

const LancetColors = {
    primary: '#A51C30',
    secondary: '#1E40AF',
    accent1: '#047857',
    accent2: '#D97706',
    accent3: '#7C3AED',
    gray: '#6B7280',
    light: '#F3F4F6',
    palette: ['#A51C30', '#1E40AF', '#047857', '#D97706', '#7C3AED', '#DC2626', '#0891B2', '#059669']
};

/**
 * Create a weighted bar chart
 */
function createBarChart(canvasId, labels, data, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: options.label || 'Percentage',
                data: data,
                backgroundColor: LancetColors.palette.slice(0, data.length),
                borderColor: LancetColors.palette.slice(0, data.length),
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: options.showLegend || false },
                title: {
                    display: !!options.title,
                    text: options.title,
                    font: { size: 14, weight: 'bold' },
                    color: '#0F172A'
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.parsed.y.toFixed(1)}%`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: v => v + '%', font: { size: 11 } },
                    grid: { color: '#F1F5F9' }
                },
                x: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Create a forest plot for regression results
 */
function createForestPlot(canvasId, results, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;
    
    const labels = results.map(r => r.variable);
    const estimates = results.map(r => r.estimate);
    const ciLow = results.map(r => r.ci_low);
    const ciHigh = results.map(r => r.ci_high);
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: options.measure || 'Odds Ratio',
                data: estimates,
                backgroundColor: LancetColors.primary,
                borderColor: LancetColors.primary,
                borderWidth: 0,
                barThickness: 12,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: {
                    display: !!options.title,
                    text: options.title,
                    font: { size: 14, weight: 'bold' }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const i = ctx.dataIndex;
                            return `${estimates[i].toFixed(2)} (${ciLow[i].toFixed(2)}-${ciHigh[i].toFixed(2)})`;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        refLine: {
                            type: 'line',
                            xMin: 1,
                            xMax: 1,
                            borderColor: '#94A3B8',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: options.measure || 'Odds Ratio (95% CI)', font: { size: 12 } },
                    grid: { color: '#F1F5F9' }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11, weight: 'bold' } }
                }
            }
        }
    });
}

/**
 * Create a distribution histogram
 */
function createHistogram(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;
    
    // Create bins
    const min = Math.min(...data);
    const max = Math.max(...data);
    const nBins = options.bins || 20;
    const binWidth = (max - min) / nBins;
    const bins = Array(nBins).fill(0);
    const binLabels = [];
    
    for (let i = 0; i < nBins; i++) {
        binLabels.push((min + i * binWidth).toFixed(0));
    }
    
    data.forEach(v => {
        const idx = Math.min(Math.floor((v - min) / binWidth), nBins - 1);
        bins[idx]++;
    });
    
    const pcts = bins.map(b => (b / data.length * 100));
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: options.label || 'Frequency',
                data: pcts,
                backgroundColor: LancetColors.primary + '80',
                borderColor: LancetColors.primary,
                borderWidth: 1,
                barPercentage: 1.0,
                categoryPercentage: 1.0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: !!options.title, text: options.title, font: { size: 14, weight: 'bold' } },
                tooltip: { callbacks: { label: ctx => `${ctx.parsed.y.toFixed(1)}%` } }
            },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => v + '%' }, grid: { color: '#F1F5F9' } },
                x: { title: { display: true, text: options.xLabel || '' }, grid: { display: false }, ticks: { maxTicksLimit: 10 } }
            }
        }
    });
}

/**
 * Create a pie/donut chart
 */
function createDonutChart(canvasId, labels, data, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: LancetColors.palette.slice(0, data.length),
                borderWidth: 2,
                borderColor: '#fff',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 15 } },
                title: { display: !!options.title, text: options.title, font: { size: 14, weight: 'bold' } },
                tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed.toFixed(1)}%` } }
            }
        }
    });
}

/**
 * Create a scatter plot with regression line
 */
function createScatterPlot(canvasId, xData, yData, options = {}) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return null;
    
    const points = xData.map((x, i) => ({ x, y: yData[i] }));
    
    // Simple linear regression for trend line
    const n = xData.length;
    const sumX = xData.reduce((a, b) => a + b, 0);
    const sumY = yData.reduce((a, b) => a + b, 0);
    const sumXY = xData.reduce((a, x, i) => a + x * yData[i], 0);
    const sumXX = xData.reduce((a, x) => a + x * x, 0);
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    const xMin = Math.min(...xData);
    const xMax = Math.max(...xData);
    
    return new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: options.label || 'Data',
                data: points,
                backgroundColor: LancetColors.primary + '40',
                borderColor: LancetColors.primary,
                pointRadius: 3,
                pointHoverRadius: 5,
            }, {
                label: 'Trend',
                data: [{ x: xMin, y: slope * xMin + intercept }, { x: xMax, y: slope * xMax + intercept }],
                type: 'line',
                borderColor: LancetColors.secondary,
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: !!options.title, text: options.title, font: { size: 14, weight: 'bold' } },
            },
            scales: {
                x: { title: { display: true, text: options.xLabel || 'X' }, grid: { color: '#F1F5F9' } },
                y: { title: { display: true, text: options.yLabel || 'Y' }, grid: { color: '#F1F5F9' } }
            }
        }
    });
}
