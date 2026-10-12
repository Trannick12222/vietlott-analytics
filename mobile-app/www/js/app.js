// Vietlott Analytics Dashboard JavaScript
const DEFAULT_SERVER_URL = 'http://10.18.30.172:8000';
let API_BASE_URL = localStorage.getItem('vietlott_api_url') || DEFAULT_SERVER_URL;

let currentLotteryType = 'MEGA_645';
let currentThreshold = 50;
let frequencyChart = null;
let currentComboMode = 'standard';
let currentBaoType = 7;
let cachedDashboardData = null;
let cachedBaoData = {};

function apiUrl(path) {
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    const base = API_BASE_URL.replace(/\/+$/, '');
    const cleanPath = path.startsWith('/') ? path : '/' + path;
    return base + cleanPath;
}

function promptChangeServer() {
    const current = API_BASE_URL;
    const entered = prompt('Nhập địa chỉ máy chủ Backend (Ví dụ: http://10.18.30.172:8000 hoặc địa chỉ domain Cloud):', current);
    if (entered && entered.trim() !== '') {
        API_BASE_URL = entered.trim().replace(/\/+$/, '');
        localStorage.setItem('vietlott_api_url', API_BASE_URL);
        showToast('Đã lưu địa chỉ máy chủ: ' + API_BASE_URL, 'success');
        loadDashboard();
    }
}


// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get initial lottery type from URL or default
    const pathParts = window.location.pathname.split('/');
    if (pathParts.includes('POWER_655')) {
        currentLotteryType = 'POWER_655';
    }

    // Apply saved language preferences
    applyLanguage(currentLang);
    
    // 1. Tải ngay dữ liệu từ Database lên giao diện tức thì
    loadDashboard();

    // 2. Kiểm tra ngầm kỳ quay mới nhất từ website (nếu có kỳ mới sẽ tự làm mới)
    setTimeout(() => {
        backgroundSync();
    }, 1500);
});

async function backgroundSync() {
    try {
        const res = await fetch(apiUrl('/api/fetch'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lottery_type: currentLotteryType, limit: 100 })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.records_added > 0) {
                showToast(`Đã cập nhật thêm ${data.records_added} kỳ quay mới!`, 'success');
                loadDashboard();
            }
        }
    } catch (e) {
        console.debug('Background sync completed or offline.');
    }
}

function switchLottery(type) {
    currentLotteryType = type;
    // Update tab styling
    document.querySelectorAll('.lottery-tab').forEach(tab => {
        tab.classList.remove('bg-blue-600', 'text-white');
        tab.classList.add('bg-slate-700', 'text-gray-300');
    });
    document.getElementById('tab-' + type).classList.remove('bg-slate-700', 'text-gray-300');
    document.getElementById('tab-' + type).classList.add('bg-blue-600', 'text-white');
    
    loadDashboard();
}

async function loadDashboard() {
    showLoading();
    try {
        const response = await fetch(apiUrl(`/api/dashboard/${currentLotteryType}`));
        if (!response.ok) {
            // If no data, try fetching first
            if (response.status === 500) {
                showToast('Đang tải dữ liệu lần đầu...', 'info');
                await fetchData();
                const retryResponse = await fetch(apiUrl(`/api/dashboard/${currentLotteryType}`));
                if (retryResponse.ok) {
                    const data = await retryResponse.json();
                    cachedDashboardData = data;
                    renderDashboard(data);
                    return;
                }
            }
            showToast('Chưa có dữ liệu. Nhấn "Làm mới dữ liệu" để bắt đầu.', 'info');
            return;
        }
        const data = await response.json();
        cachedDashboardData = data;
        renderDashboard(data);
    } catch (error) {
        console.error('Dashboard error:', error);
        showToast('Lỗi tải dữ liệu: ' + error.message, 'error');
    }
}

function renderDashboard(data) {
    renderDrawsTable(data.latest_draws);
    if (data.statistics) renderFrequencyChart(data.statistics);
    if (data.statistics) renderHotCold(data.statistics);
    if (data.predictions && data.predictions.regime_forecast) renderRegimeForecast(data.predictions.regime_forecast);
    if (data.predictions) renderPredictions(data.predictions);
    if (data.predictions) renderCombinations(data.predictions);
    if (data.wheeling_combinations) renderWheeling(data.wheeling_combinations);
    if (data.bao_combinations) renderBaoCombinations(data.bao_combinations);
    if (data.predictions) renderProbabilityComparison(data.predictions);
    if (data.backtest) renderBacktest(data.backtest);
    
    // Update info
    document.getElementById('total-draws').textContent = data.total_draws_in_db || 0;
    document.getElementById('last-fetch').textContent = data.last_fetch ? new Date(data.last_fetch).toLocaleString('vi-VN') : 'Chưa có';
    hideLoading();
}

function getBallClass(num) {
    if (num <= 9) return 'ball-range-1';
    if (num <= 18) return 'ball-range-2';
    if (num <= 27) return 'ball-range-3';
    if (num <= 36) return 'ball-range-4';
    if (num <= 45) return 'ball-range-5';
    return 'ball-range-6';
}

function renderBalls(numbers, size = '') {
    return numbers.map(n => `<span class="ball ${size} ${getBallClass(n)}">${n < 10 ? '0' + n : n}</span>`).join('');
}

function renderDrawsTable(draws) {
    const container = document.getElementById('draws-table');
    if (!draws || draws.length === 0) {
        const noDataMsg = (currentLang === 'en') ? 'No data available. Click "Refresh Data" to fetch.' : 'Chưa có dữ liệu. Nhấn "Làm mới dữ liệu" để fetch.';
        container.innerHTML = `<p class="text-gray-400 text-center py-4">${noDataMsg}</p>`;
        return;
    }
    const thDraw = (currentLang === 'en') ? 'Draw #' : 'Kỳ #';
    const thDate = (currentLang === 'en') ? 'Date' : 'Ngày';
    const thResult = (currentLang === 'en') ? 'Result' : 'Kết quả';
    const thSource = (currentLang === 'en') ? 'Source' : 'Nguồn';
    const footerCount = (currentLang === 'en') ? `Showing last <strong>${draws.length}</strong> draws` : `Hiển thị <strong>${draws.length}</strong> kỳ gần nhất`;

    let html = `<div class="overflow-y-auto max-h-[500px] border border-slate-700/60 rounded"><table class="w-full text-sm">
        <thead class="sticky top-0 bg-slate-900 border-b border-slate-700"><tr class="text-left text-gray-400">
            <th class="py-2.5 px-3">${thDraw}</th>
            <th class="py-2.5 px-3">${thDate}</th>
            <th class="py-2.5 px-3">${thResult}</th>
            ${draws.some(d => d.jackpot_2) ? '<th class="py-2.5 px-2 text-center">JP2</th>' : ''}
            <th class="py-2.5 px-3 text-right">${thSource}</th>
        </tr></thead><tbody>`;
    draws.forEach((d, idx) => {
        const rowBg = idx % 2 === 0 ? 'bg-slate-800/40' : 'bg-slate-800/80';
        html += `<tr class="${rowBg} border-b border-slate-800 hover:bg-slate-700/50 transition">
            <td class="py-2 px-3 text-white font-mono font-bold">#${d.draw_number}</td>
            <td class="py-2 px-3 text-gray-300 font-mono text-xs">${d.draw_date}</td>
            <td class="py-2 px-3">${renderBalls(d.numbers, 'ball-sm')}</td>
            ${d.jackpot_2 !== null && d.jackpot_2 !== undefined ? `<td class="py-2 px-2 text-center"><span class="ball ball-sm bg-red-600 font-bold border border-amber-300">${d.jackpot_2 < 10 ? '0' + d.jackpot_2 : d.jackpot_2}</span></td>` : (draws.some(x => x.jackpot_2) ? '<td></td>' : '')}
            <td class="py-2 px-3 text-gray-500 text-[11px] text-right">${d.source}</td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    html += `<div class="mt-2 text-right text-xs text-gray-400">${footerCount}</div>`;
    container.innerHTML = html;
}

function renderFrequencyChart(stats) {
    const ctx = document.getElementById('frequency-canvas');
    if (!ctx) return;
    
    const freq = stats.frequency;
    if (!freq || !freq.counts) return;
    
    const labels = Object.keys(freq.counts).map(Number).sort((a,b) => a-b);
    const counts = labels.map(l => freq.counts[l] || 0);
    const colors = labels.map(l => {
        const count = freq.counts[l] || 0;
        const maxCount = Math.max(...counts);
        const ratio = maxCount > 0 ? count / maxCount : 0;
        const r = Math.round(59 + ratio * 196);
        const b = Math.round(130 - ratio * 90);
        return `rgb(${r}, ${Math.round(80 - ratio * 40)}, ${b})`;
    });
    
    if (frequencyChart) frequencyChart.destroy();
    frequencyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Số lần xuất hiện',
                data: counts,
                backgroundColor: colors,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
            }
        }
    });
}

function renderHotCold(stats) {
    const container = document.getElementById('hot-cold-content');
    if (!container) return;
    
    const recency = stats.recency;
    if (!recency) return;
    
    const hot = recency.hot_numbers || [];
    const cold = recency.cold_numbers || [];
    const overdue = recency.overdue_numbers || [];
    
    let html = '<div class="grid grid-cols-1 md:grid-cols-3 gap-4">';
    
    // Hot numbers
    html += '<div class="bg-red-900/20 border border-red-800 rounded-lg p-4"><h4 class="text-red-400 font-bold mb-3">🔥 HOT Numbers</h4><div class="flex flex-wrap gap-1">';
    (Array.isArray(hot) ? hot.slice(0, 10) : []).forEach(n => {
        const num = typeof n === 'object' ? n.number || n : n;
        html += `<span class="ball ball-sm ${getBallClass(num)}">${num}</span>`;
    });
    html += '</div></div>';
    
    // Cold numbers
    html += '<div class="bg-blue-900/20 border border-blue-800 rounded-lg p-4"><h4 class="text-blue-400 font-bold mb-3">❄️ COLD Numbers</h4><div class="flex flex-wrap gap-1">';
    (Array.isArray(cold) ? cold.slice(0, 10) : []).forEach(n => {
        const num = typeof n === 'object' ? n.number || n : n;
        html += `<span class="ball ball-sm ${getBallClass(num)}">${num}</span>`;
    });
    html += '</div></div>';
    
    // Overdue numbers
    html += '<div class="bg-yellow-900/20 border border-yellow-800 rounded-lg p-4"><h4 class="text-yellow-400 font-bold mb-3">⏰ OVERDUE Numbers</h4><div class="flex flex-wrap gap-1">';
    (Array.isArray(overdue) ? overdue.slice(0, 10) : []).forEach(n => {
        const num = typeof n === 'object' ? n.number || n : n;
        html += `<span class="ball ball-sm ${getBallClass(num)}">${num}</span>`;
    });
    html += '</div><p class="text-yellow-600 text-xs mt-2">⚠️ "Overdue" không có nghĩa là sắp xuất hiện.</p></div>';
    
    html += '</div>';
    container.innerHTML = html;
}

function renderPredictions(predictions) {
    const container = document.getElementById('predictions-table');
    if (!container) return;
    
    const rankings = predictions.rankings || predictions.all_rankings || [];
    if (rankings.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-4">Chưa có dữ liệu dự đoán.</p>';
        return;
    }
    
    const threshold = currentThreshold;
    const filtered = rankings.filter(r => r.model_score >= threshold);
    
    const isEn = (currentLang === 'en');
    let html = `
    <div class="mb-3 text-xs text-amber-300/90 bg-amber-950/40 border border-amber-800/60 p-2 rounded">
        ${isEn 
            ? '⚠️ <strong>Notice:</strong> Filter threshold is based on <strong>MODEL SCORE</strong> (0-100), which is an analytical metric, <em>not the actual probability</em> of the number appearing.' 
            : '⚠️ <strong>Lưu ý:</strong> Ngưỡng lọc ở đây là <strong>MODEL SCORE</strong> (0-100), hoàn toàn <em>không phải xác suất thực tế</em> số đó sẽ xuất hiện.'}
    </div>`;
    
    if (filtered.length === 0) {
        html += `<div class="bg-yellow-900/30 border border-yellow-600 rounded-lg p-4 text-center my-4">
            <p class="text-yellow-200 font-medium">${isEn ? `No numbers met the model score threshold &ge; ${threshold}.` : `Không có con số nào đạt ngưỡng điểm mô hình &ge; ${threshold}.`}</p>
            <p class="text-gray-400 text-xs mt-1">${isEn ? 'Lower the slider threshold to display candidate numbers.' : 'Hãy hạ thanh trượt ngưỡng lọc để hiển thị danh sách các số tiềm năng.'}</p>
        </div>`;
        container.innerHTML = html;
        return;
    }
    
    const display = filtered;
    html += `<div class="overflow-x-auto max-h-[450px]"><table class="w-full text-sm">
        <thead class="sticky top-0 bg-slate-900 border-b border-slate-700"><tr class="text-left text-gray-400">
            <th class="py-2 px-2">#</th>
            <th class="py-2 px-2">${isEn ? 'Ball' : 'Số'}</th>
            <th class="py-2 px-2">Model Score</th>
            <th class="py-2 px-2">Math Prob</th>
            <th class="py-2 px-2">${isEn ? 'Frequency' : 'Tần suất'}</th>
            <th class="py-2 px-2">${isEn ? 'Last Seen' : 'Lần cuối'}</th>
            <th class="py-2 px-2 text-center" title="${isEn ? 'Extreme value & mean reversion alignment score' : 'Điểm phù hợp theo phân phối cực trị & hồi quy trung bình'}">${isEn ? 'Regime Fit' : 'Điểm Nhịp'}</th>
            <th class="py-2 px-2">${isEn ? 'Confidence' : 'Độ tin cậy'}</th>
        </tr></thead><tbody>`;
    
    display.forEach((r, i) => {
        const scoreClass = r.model_score >= 70 ? 'score-high' : r.model_score >= 40 ? 'score-medium' : 'score-low';
        const confClass = r.confidence === 'High' ? 'confidence-high' : r.confidence === 'Medium' ? 'confidence-medium' : 'confidence-low';
        const regimeScoreVal = r.regime_score !== undefined ? r.regime_score.toFixed(1) : '--';
        html += `<tr class="border-b border-slate-800 hover:bg-slate-800/50">
            <td class="py-2 px-2 text-gray-400">${i + 1}</td>
            <td class="py-2 px-2">${renderBalls([r.number], 'ball-sm')}</td>
            <td class="py-2 px-2"><div class="flex items-center gap-2"><span class="text-white font-bold">${r.model_score.toFixed(1)}</span><div class="score-bar w-20"><div class="score-bar-fill ${scoreClass}" style="width:${r.model_score}%"></div></div></div></td>
            <td class="py-2 px-2 text-gray-400">${r.mathematical_probability}%</td>
            <td class="py-2 px-2 text-gray-300 font-mono text-xs">${r.frequency}</td>
            <td class="py-2 px-2 text-gray-300 text-xs">${r.last_seen}</td>
            <td class="py-2 px-2 text-center font-mono text-xs text-indigo-300 font-bold">${regimeScoreVal}</td>
            <td class="py-2 px-2"><span class="px-2 py-0.5 rounded text-[11px] font-bold ${confClass}">${r.confidence}</span></td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    
    if (predictions.sample_size_warning) {
        html += `<div class="bg-orange-900/30 border border-orange-600 rounded-lg p-3 mt-4"><p class="text-orange-200 text-sm">⚠️ ${predictions.sample_size_warning}</p></div>`;
    }
    
    container.innerHTML = html;
}

function renderRegimeForecast(regimeData) {
    if (!regimeData) return;
    const regimeAnalysis = regimeData.regime_analysis;
    const orderStats = regimeData.order_statistics;
    const meanRev = regimeData.mean_reversion;

    if (!regimeAnalysis || !regimeAnalysis.next_draw_forecast) return;

    const forecast = regimeAnalysis.next_draw_forecast;
    const probs = forecast.probabilities || {};
    const pLow = probs.LOW || 0;
    const pStd = probs.STD || 0;
    const pHigh = probs.HIGH || 0;

    // Cập nhật % và width thanh bar
    const lowValEl = document.getElementById('regime-prob-low');
    const stdValEl = document.getElementById('regime-prob-std');
    const highValEl = document.getElementById('regime-prob-high');

    const lowBarEl = document.getElementById('regime-bar-low');
    const stdBarEl = document.getElementById('regime-bar-std');
    const highBarEl = document.getElementById('regime-bar-high');

    if (lowValEl) lowValEl.textContent = pLow.toFixed(1) + '%';
    if (stdValEl) stdValEl.textContent = pStd.toFixed(1) + '%';
    if (highValEl) highValEl.textContent = pHigh.toFixed(1) + '%';

    if (lowBarEl) lowBarEl.style.width = pLow + '%';
    if (stdBarEl) stdBarEl.style.width = pStd + '%';
    if (highBarEl) highBarEl.style.width = pHigh + '%';

    // Cập nhật range label tùy theo lottery_type
    const isMega = (currentLotteryType === 'MEGA_645');
    const isEn = (currentLang === 'en');
    const lowRangeEl = document.getElementById('regime-range-low');
    const stdRangeEl = document.getElementById('regime-range-std');
    const highRangeEl = document.getElementById('regime-range-high');

    const maxBallLabel = isEn ? 'Max ball' : 'Max bóng';
    if (lowRangeEl) lowRangeEl.textContent = isMega ? `${maxBallLabel} ≤ 33` : `${maxBallLabel} ≤ 40`;
    if (stdRangeEl) stdRangeEl.textContent = isMega ? `${maxBallLabel} 34 - 42` : `${maxBallLabel} 41 - 50`;
    if (highRangeEl) highRangeEl.textContent = isMega ? `${maxBallLabel} ≥ 43` : `${maxBallLabel} ≥ 51`;

    // Badge trạng thái dự báo
    const badgeNameEl = document.getElementById('regime-predicted-name');
    const badgeEl = document.getElementById('regime-predicted-badge');
    const predRegime = forecast.predicted_regime;
    let regimeLabel = isEn ? 'Gaussian Bell' : 'Cân Bằng Chuẩn';
    let badgeClass = 'bg-emerald-900/40 text-emerald-300 border-emerald-500/40';

    if (predRegime === 'LOW') {
        regimeLabel = isEn ? 'Low Compression' : 'Nén Dải Thấp (Rút Thấp)';
        badgeClass = 'bg-blue-900/40 text-blue-300 border-blue-500/40';
    } else if (predRegime === 'HIGH') {
        regimeLabel = isEn ? 'High Extreme Outbreak' : 'Bung Dải Cao (Cực Đại)';
        badgeClass = 'bg-purple-900/40 text-purple-300 border-purple-500/40';
    }

    if (badgeNameEl) badgeNameEl.textContent = regimeLabel;
    if (badgeEl) badgeEl.className = `px-3 py-1.5 rounded-lg text-xs font-bold border flex items-center gap-1.5 shadow ${badgeClass}`;

    // Cập nhật min, max, sum
    const minEl = document.getElementById('regime-exp-min');
    const maxEl = document.getElementById('regime-exp-max');
    const sumEl = document.getElementById('regime-exp-sum');

    if (minEl && forecast.expected_min_range) {
        minEl.textContent = `${forecast.expected_min_range[0].toString().padStart(2, '0')} - ${forecast.expected_min_range[1].toString().padStart(2, '0')}`;
    }
    if (maxEl && forecast.expected_max_range) {
        maxEl.textContent = `${forecast.expected_max_range[0].toString().padStart(2, '0')} - ${forecast.expected_max_range[1].toString().padStart(2, '0')}`;
    }
    if (sumEl && forecast.expected_sum_range) {
        sumEl.textContent = `${forecast.expected_sum_range[0]} - ${forecast.expected_sum_range[1]}`;
    }

    // Cập nhật Mean Reversion Oscillator
    if (meanRev) {
        const revBadge = document.getElementById('reversion-badge');
        const revDesc = document.getElementById('reversion-desc');
        const revIcon = document.getElementById('reversion-icon');

        if (revDesc) {
            if (isEn) {
                if (meanRev.reversion_status === 'OVERBOUGHT_HIGH') {
                    revDesc.textContent = 'Recent draw reached high extreme. High mathematical probability of downward pullback toward low/mid tiers.';
                } else if (meanRev.reversion_status === 'OVERSOLD_LOW') {
                    revDesc.textContent = 'Recent draw heavily compressed in low band. High probability of rebounding upward into higher tiers.';
                } else {
                    revDesc.textContent = 'Sum total and boundary balls oscillate stably around normal theoretical mean.';
                }
            } else {
                revDesc.textContent = meanRev.reversion_desc || '';
            }
        }
        if (revBadge) {
            let statusText = isEn ? 'Balanced Equilibrium' : 'Cân bằng (Balanced)';
            let statusClass = 'bg-slate-800 text-slate-300 border-slate-700';
            let icon = '⚖️';

            if (meanRev.reversion_status === 'OVERBOUGHT_HIGH') {
                statusText = isEn ? 'Negative Pullback (Down)' : 'Hồi quy âm (Kéo về Thấp/Trung)';
                statusClass = 'bg-amber-900/40 text-amber-300 border-amber-600/40';
                icon = '🧲';
            } else if (meanRev.reversion_status === 'OVERSOLD_LOW') {
                statusText = isEn ? 'Positive Rebound (Up)' : 'Hồi quy dương (Bung lên Cao)';
                statusClass = 'bg-cyan-900/40 text-cyan-300 border-cyan-600/40';
                icon = '🚀';
            }

            revBadge.textContent = statusText;
            revBadge.className = `px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusClass}`;
            if (revIcon) revIcon.textContent = icon;
        }
    }
}

function renderCombinations(predictions) {
    const container = document.getElementById('combinations-grid');
    if (!container) return;
    
    const combos = predictions.combinations || [];
    const isEn = (currentLang === 'en');
    if (combos.length === 0) {
        container.innerHTML = `<p class="text-gray-400 text-center py-4">${isEn ? 'No combinations generated yet.' : 'Chưa có bộ số nào được sinh.'}</p>`;
        return;
    }
    
    let html = '';
    combos.forEach((c, idx) => {
        const rank = c.rank || (idx + 1);
        const numbersStr = c.numbers.map(n => n < 10 ? '0' + n : '' + n).join(', ');
        const sumVal = c.sum_total || c.numbers.reduce((a, b) => a + b, 0);
        const fitnessVal = c.fitness_score ? c.fitness_score.toFixed(1) : (c.score ? c.score.toFixed(1) : '85.0');
        const oddEvenVal = c.odd_even_ratio || (c.numbers.filter(n => n % 2 === 0).length + (isEn ? 'E : ' : 'C : ') + c.numbers.filter(n => n % 2 !== 0).length + (isEn ? 'O' : 'L'));
        
        let stratName = c.strategy;
        if (isEn) {
            if (c.strategy.includes('Phong Độ') || c.strategy.includes('Elite')) stratName = 'Elite Hot Momentum';
            else if (c.strategy.includes('Cân Bằng') || c.strategy.includes('Balanced')) stratName = 'Balanced Cycle Rebound';
            else if (c.strategy.includes('Gan') || c.strategy.includes('Cold') || c.strategy.includes('Dị Biệt')) stratName = 'Cold Outbreak / Anomaly';
            else if (c.strategy.includes('Nén') || c.strategy.includes('Compression')) stratName = 'Low Band Compression';
            else if (c.strategy.includes('Delta') || c.strategy.includes('Spread')) stratName = 'Natural Delta Spread';
        }

        let badgeStyle = 'bg-amber-900/80 text-amber-300 border-amber-600';
        let borderStyle = 'border-amber-600/60';
        
        if (c.strategy.includes('Phong Độ') || c.strategy.includes('Hot') || c.strategy.includes('Elite')) {
            badgeStyle = 'bg-amber-900/80 text-amber-300 border-amber-600';
            borderStyle = 'border-amber-600/60';
        } else if (c.strategy.includes('Cân Bằng') || c.strategy.includes('Balanced')) {
            badgeStyle = 'bg-emerald-900/80 text-emerald-300 border-emerald-600';
            borderStyle = 'border-emerald-600/60';
        } else if (c.strategy.includes('Gan') || c.strategy.includes('Cold') || c.strategy.includes('Dị Biệt')) {
            badgeStyle = 'bg-cyan-900/80 text-cyan-300 border-cyan-500';
            borderStyle = 'border-cyan-500/60';
        } else if (c.strategy.includes('Nén') || c.strategy.includes('Compression')) {
            badgeStyle = 'bg-blue-900/80 text-blue-300 border-blue-500';
            borderStyle = 'border-blue-500/60';
        } else if (c.strategy.includes('Delta') || c.strategy.includes('Spread')) {
            badgeStyle = 'bg-purple-900/80 text-purple-300 border-purple-600';
            borderStyle = 'border-purple-600/60';
        }

        const deltaStr = c.delta_steps && c.delta_steps.length > 0 ? c.delta_steps.join(' · ') : '--';

        html += `<div class="bg-slate-800/90 rounded-xl p-4 border ${borderStyle} shadow-lg flex flex-col justify-between hover:border-indigo-400 hover:shadow-indigo-500/10 transition-all">
            <div>
                <div class="flex items-center justify-between mb-2.5">
                    <div class="flex items-center gap-1.5">
                        <span class="w-6 h-6 rounded-full bg-slate-700 text-white font-bold text-xs flex items-center justify-center font-mono border border-slate-600">
                            #${rank}
                        </span>
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold border ${badgeStyle}">
                            ${stratName}
                        </span>
                    </div>
                    <div class="text-right">
                        <span class="text-[11px] text-slate-400">${isEn ? 'Fitness:' : 'Độ Hài Hòa:'}</span>
                        <span class="text-emerald-400 font-bold font-mono text-sm ml-1">${fitnessVal}</span>
                    </div>
                </div>

                <!-- 6 quả bóng số -->
                <div class="flex gap-1.5 justify-center py-2.5 bg-slate-900/50 rounded-lg mb-3">
                    ${renderBalls(c.numbers, 'ball-md')}
                </div>
            </div>

            <!-- Các chỉ số toán học -->
            <div class="space-y-2 pt-1 border-t border-slate-700/60">
                <div class="grid grid-cols-2 gap-1.5 text-[11px] text-slate-300">
                    <div class="bg-slate-900/40 px-2 py-1 rounded flex justify-between">
                        <span class="text-slate-400">${isEn ? 'Sum:' : 'Tổng (Sum):'}</span>
                        <strong class="text-amber-300 font-mono">${sumVal} <span class="text-[9px] text-slate-400 font-normal">±1σ</span></strong>
                    </div>
                    <div class="bg-slate-900/40 px-2 py-1 rounded flex justify-between">
                        <span class="text-slate-400">${isEn ? 'Odd/Even:' : 'Chẵn/Lẻ:'}</span>
                        <strong class="text-slate-200">${oddEvenVal}</strong>
                    </div>
                </div>

                <div class="bg-slate-900/40 px-2 py-1 rounded flex items-center justify-between text-[11px]">
                    <span class="text-slate-400">${isEn ? 'Steps Δ:' : 'Bước nhảy Δ:'}</span>
                    <span class="text-indigo-300 font-mono text-xs">${deltaStr}</span>
                </div>

                <button onclick="copyCombo('${numbersStr}')" class="w-full mt-1 bg-slate-700/70 hover:bg-slate-600 text-slate-200 hover:text-white text-xs py-1.5 rounded transition flex items-center justify-center gap-1.5 border border-slate-600">
                    <span>📋</span> ${isEn ? `Copy Ticket (${numbersStr})` : `Sao chép 6 số (${numbersStr})`}
                </button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function copyCombo(numbersStr) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(numbersStr).then(() => {
            showToast(`Đã sao chép bộ số: ${numbersStr}`, 'success');
        }).catch(() => {
            prompt('Sao chép bộ số dưới đây:', numbersStr);
        });
    } else {
        prompt('Sao chép bộ số dưới đây:', numbersStr);
    }
}

let currentWheelSize = 12;
let currentWheelStrategy = 'balanced';
let cachedWheelData = null;

// ==================== TÍNH NĂNG CHUYỂN CHẾ ĐỘ BỘ SỐ ====================

function switchComboMode(mode) {
    currentComboMode = mode;
    const btnStd = document.getElementById('btn-combo-standard');
    const btnWheel = document.getElementById('btn-combo-wheeling');
    const btnBao = document.getElementById('btn-combo-bao');
    const btnCustom = document.getElementById('btn-combo-custom');
    
    const secStd = document.getElementById('section-combo-standard');
    const secWheel = document.getElementById('section-combo-wheeling');
    const secBao = document.getElementById('section-combo-bao');
    const secCustom = document.getElementById('section-combo-custom');

    // Reset styles
    [btnStd, btnWheel, btnBao, btnCustom].forEach(b => {
        if (b) b.className = 'combo-mode-btn bg-slate-700 hover:bg-slate-600 text-gray-300 text-xs md:text-sm px-3.5 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5';
    });
    [secStd, secWheel, secBao, secCustom].forEach(s => {
        if (s) s.classList.add('hidden');
    });

    if (mode === 'standard') {
        if (btnStd) btnStd.className = 'combo-mode-btn bg-blue-600 text-white text-xs md:text-sm px-3.5 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5';
        if (secStd) secStd.classList.remove('hidden');
    } else if (mode === 'wheeling') {
        if (btnWheel) btnWheel.className = 'combo-mode-btn bg-emerald-600 text-white text-xs md:text-sm px-3.5 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5';
        if (secWheel) secWheel.classList.remove('hidden');
        fetchWheelingData(currentWheelSize);
    } else if (mode === 'bao') {
        if (btnBao) btnBao.className = 'combo-mode-btn bg-blue-600 text-white text-xs md:text-sm px-3.5 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5';
        if (secBao) secBao.classList.remove('hidden');
        fetchBaoCombinations(currentBaoType);
    } else if (mode === 'custom') {
        if (btnCustom) btnCustom.className = 'combo-mode-btn bg-indigo-600 text-white text-xs md:text-sm px-3.5 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5';
        if (secCustom) secCustom.classList.remove('hidden');
        initCustomBallsGrid();
    }
}

async function selectBaoType(baoType) {
    currentBaoType = baoType;
    // Cập nhật giao diện nút bấm Bao
    document.querySelectorAll('.bao-btn').forEach(btn => {
        const val = parseInt(btn.getAttribute('data-bao'));
        if (val === baoType) {
            btn.className = 'bao-btn px-2.5 py-1 text-xs rounded font-bold bg-indigo-600 text-white shadow';
        } else {
            btn.className = 'bao-btn px-2.5 py-1 text-xs rounded font-bold bg-slate-700 text-slate-300 hover:bg-slate-600';
        }
    });

    await fetchBaoCombinations(baoType);
}

async function fetchBaoCombinations(baoType) {
    const cacheKey = `${currentLotteryType}_${baoType}`;
    if (cachedBaoData[cacheKey]) {
        renderBaoCombinations(cachedBaoData[cacheKey]);
        return;
    }
    try {
        const res = await fetch(apiUrl(`/api/combinations/bao/${currentLotteryType}?bao_type=${baoType}`));
        if (!res.ok) {
            showToast('Không thể tạo dàn vé bao. Vui lòng thử lại!', 'error');
            return;
        }
        const data = await res.json();
        cachedBaoData[cacheKey] = data;
        renderBaoCombinations(data);
    } catch (e) {
        showToast('Lỗi khi tải dàn vé bao: ' + e.message, 'error');
    }
}

function renderBaoCombinations(baoData) {
    if (!baoData) return;
    
    // Cập nhật thông số tóm tắt
    const countEl = document.getElementById('bao-ticket-count');
    const costEl = document.getElementById('bao-cost-value');
    if (countEl) countEl.textContent = baoData.ticket_count ? baoData.ticket_count.toLocaleString('vi-VN') : '--';
    if (costEl) costEl.textContent = baoData.cost ? baoData.cost.toLocaleString('vi-VN') : '--';

    const container = document.getElementById('bao-combinations-grid');
    if (!container) return;

    const combos = baoData.combinations || [];
    if (combos.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-4">Chưa có dàn vé bao nào.</p>';
        return;
    }

    const badgeColors = {
        'Tối ưu Model Score': 'bg-emerald-900/80 text-emerald-300 border-emerald-600',
        'Cân bằng Hot & Cold': 'bg-amber-900/80 text-amber-300 border-amber-600',
        'Phân bổ Đều Dải Số': 'bg-purple-900/80 text-purple-300 border-purple-600',
        'Săn Số Gan (Cold Outbreak)': 'bg-cyan-900/80 text-cyan-300 border-cyan-500',
        'Nén Dải Thấp (Rút Thấp)': 'bg-blue-900/80 text-blue-300 border-blue-500'
    };

    let html = '';
    combos.forEach(c => {
        const badgeClass = badgeColors[c.strategy] || 'bg-blue-900 text-blue-300 border-blue-600';
        html += `<div class="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-lg flex flex-col justify-between hover:border-indigo-500 transition-all">
            <div>
                <div class="flex items-center justify-between mb-3 border-b border-slate-700/80 pb-2">
                    <span class="px-2.5 py-0.5 rounded text-xs font-bold border ${badgeClass}">
                        ${c.strategy}
                    </span>
                    <span class="text-xs text-slate-400">
                        Score TB: <strong class="text-white font-mono text-sm">${c.score.toFixed(1)}</strong>
                    </span>
                </div>
                
                <div class="flex flex-wrap gap-1.5 justify-center py-3 bg-slate-900/40 rounded-lg p-2 mb-3">
                    ${renderBalls(c.numbers, 'ball-md')}
                </div>
            </div>

            <div class="grid grid-cols-3 gap-2 pt-2 border-t border-slate-700/60 text-[11px] text-slate-400 text-center">
                <div class="bg-slate-900/50 p-1.5 rounded">
                    Chẵn / Lẻ: <strong class="text-slate-200">${c.even_count}C : ${c.odd_count}L</strong>
                </div>
                <div class="bg-slate-900/50 p-1.5 rounded">
                    Thấp / Cao: <strong class="text-slate-200">${c.low_count}T : ${c.high_count}C</strong>
                </div>
                <div class="bg-slate-900/50 p-1.5 rounded">
                    Tổng vé: <strong class="text-amber-400 font-mono">${c.ticket_count}</strong>
                </div>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

// ==================== TÍNH NĂNG WHEELING SYSTEM ====================

async function selectWheelSize(size) {
    currentWheelSize = size;
    document.querySelectorAll('.wheel-btn').forEach(btn => {
        const val = parseInt(btn.getAttribute('data-wheel'));
        if (val === size) {
            btn.className = 'wheel-btn px-3 py-1.5 text-xs rounded-lg font-bold bg-emerald-600 text-white shadow transition flex items-center gap-1';
        } else {
            btn.className = 'wheel-btn px-3 py-1.5 text-xs rounded-lg font-bold bg-slate-700 text-slate-300 hover:bg-slate-600 transition';
        }
    });

    await fetchWheelingData(size, currentWheelStrategy);
}

async function selectWheelStrategy(strategy) {
    currentWheelStrategy = strategy;
    document.querySelectorAll('.wheel-strat-btn').forEach(btn => {
        const strat = btn.getAttribute('data-strat');
        if (strat === strategy) {
            btn.className = 'wheel-strat-btn px-2.5 py-1 text-xs rounded font-bold bg-emerald-600 text-white shadow transition flex items-center gap-1';
        } else {
            btn.className = 'wheel-strat-btn px-2.5 py-1 text-xs rounded font-bold bg-slate-700 text-slate-300 hover:bg-slate-600 transition flex items-center gap-1';
        }
    });

    const labels = {
        'balanced': 'Cân Bằng Chuẩn',
        'cold_outbreak': 'Săn Số Gan (Dị Biệt)',
        'low_comp': 'Nén Dải Thấp',
        'elite': 'Thuần Phong Độ'
    };
    showToast(`Đã đổi chiến lược Wheeling: ${labels[strategy] || strategy}`, 'info');
    await fetchWheelingData(currentWheelSize, strategy);
}

async function fetchWheelingData(size = currentWheelSize, strategy = currentWheelStrategy) {
    try {
        const res = await fetch(apiUrl(`/api/combinations/wheeling/${currentLotteryType}?wheel_size=${size}&strategy=${strategy}`));
        if (!res.ok) {
            showToast('Không thể tạo ma trận Wheeling. Vui lòng thử lại!', 'error');
            return;
        }
        const data = await res.json();
        cachedWheelData = data;
        renderWheeling(data);
    } catch (e) {
        showToast('Lỗi khi tải ma trận Wheeling: ' + e.message, 'error');
    }
}

function renderWheeling(wheelData) {
    if (!wheelData) return;
    cachedWheelData = wheelData;

    // Cập nhật thống kê
    const costEl = document.getElementById('wheel-cost');
    const fullCostEl = document.getElementById('wheel-full-cost');
    const savingsEl = document.getElementById('wheel-savings');
    const savingsPctEl = document.getElementById('wheel-savings-pct');
    const coverageEl = document.getElementById('wheel-coverage');
    const ticketCountEl = document.getElementById('wheel-ticket-count');
    const poolSizeEl = document.getElementById('wheel-pool-size');
    const descEl = document.getElementById('wheel-guarantee-desc');

    if (costEl) costEl.textContent = wheelData.formatted_cost || ((wheelData.cost || 0).toLocaleString('vi-VN') + ' VNĐ');
    if (fullCostEl) fullCostEl.textContent = wheelData.formatted_full_bao_cost || ((wheelData.full_bao_cost || 0).toLocaleString('vi-VN') + ' VNĐ');
    if (savingsEl) savingsEl.textContent = wheelData.formatted_savings || ((wheelData.savings || 0).toLocaleString('vi-VN') + ' VNĐ');
    if (savingsPctEl) savingsPctEl.textContent = `Tiết kiệm ${wheelData.savings_pct}% chi phí`;
    if (coverageEl) coverageEl.textContent = `${wheelData.triplet_coverage_pct}%`;
    if (ticketCountEl) ticketCountEl.textContent = `Gồm đúng ${wheelData.ticket_count} vé 6 số`;
    if (poolSizeEl) poolSizeEl.textContent = wheelData.wheel_size;
    if (descEl) descEl.textContent = wheelData.guarantee_desc;

    // Render tập bóng gốc
    const poolContainer = document.getElementById('wheel-pool-container');
    if (poolContainer && wheelData.selected_numbers) {
        poolContainer.innerHTML = renderBalls(wheelData.selected_numbers, 'ball-md');
    }

    // Render danh sách vé nén
    const ticketsGrid = document.getElementById('wheel-tickets-grid');
    if (ticketsGrid && wheelData.tickets) {
        let html = '';
        wheelData.tickets.forEach((t, idx) => {
            const ticketStr = t.map(n => n < 10 ? '0' + n : '' + n).join(', ');
            html += `<div class="bg-slate-800 rounded-xl p-3 border border-slate-700 hover:border-emerald-500 shadow transition flex flex-col justify-between">
                <div class="flex items-center justify-between mb-2">
                    <span class="w-5 h-5 rounded-full bg-emerald-900 text-emerald-300 font-bold text-xs flex items-center justify-center font-mono border border-emerald-600">
                        ${idx + 1}
                    </span>
                    <span class="text-[11px] text-slate-400 font-mono">Vé 6 số chuẩn</span>
                </div>
                <div class="flex gap-1 justify-center py-2 bg-slate-900/50 rounded-lg mb-2">
                    ${renderBalls(t, 'ball-sm')}
                </div>
                <button onclick="copyCombo('${ticketStr}')" class="w-full bg-slate-700/60 hover:bg-slate-600 text-slate-200 text-[11px] py-1 rounded transition flex items-center justify-center gap-1 border border-slate-600">
                    <span>📋</span> Sao chép vé ${idx + 1}
                </button>
            </div>`;
        });
        ticketsGrid.innerHTML = html;
    }
}

function copyAllWheelTickets() {
    if (!cachedWheelData || !cachedWheelData.tickets) {
        showToast('Chưa có danh sách vé để sao chép', 'info');
        return;
    }
    const lines = cachedWheelData.tickets.map((t, i) => `Vé ${i + 1}: ` + t.map(n => n < 10 ? '0' + n : '' + n).join(', '));
    const allText = `--- DÀN VÉ WHEELING SYSTEM (${cachedWheelData.wheel_size} SỐ / ${cachedWheelData.ticket_count} VÉ) ---\n` + lines.join('\n');
    copyCombo(allText);
}

function refreshCurrentCombo() {
    if (currentComboMode === 'wheeling') {
        fetchWheelingData(currentWheelSize);
        showToast(`Đã sinh lại Ma Trận Wheeling ${currentWheelSize} số`, 'info');
    } else if (currentComboMode === 'bao') {
        fetchBaoCombinations(currentBaoType);
        showToast(`Đã sinh lại dàn Bao ${currentBaoType}`, 'info');
    } else if (currentComboMode === 'custom') {
        runCustomOptimizer();
        showToast('Đã tính toán lại dàn số tự chọn', 'info');
    } else {
        loadDashboard();
        showToast('Đã sinh lại các bộ số tiêu chuẩn', 'info');
    }
}

// ==================== TÍNH NĂNG TỰ CHỌN DÀN SỐ (CUSTOM POOL) ====================
let customSelectedNumbers = new Set([3, 6, 11, 19, 20, 23, 24, 26, 30, 43, 48, 52]);
let cachedCustomData = null;

function initCustomBallsGrid() {
    // Luôn hiển thị đầy đủ 55 bóng để người dùng tự do chọn bất kỳ con số nào
    const maxNum = 55;
    const container = document.getElementById('custom-balls-grid');
    if (!container) return;

    let html = '';
    for (let i = 1; i <= maxNum; i++) {
        const isSelected = customSelectedNumbers.has(i);
        const ballClass = getBallClass(i);
        const activeClass = isSelected 
            ? `${ballClass} ring-2 ring-white scale-105 shadow-md opacity-100 font-bold` 
            : 'bg-slate-800 text-slate-400 opacity-40 hover:opacity-80 border border-slate-700';
        const titleTip = i > 45 ? ' title="Bóng số Power 6/55"' : '';
        html += `<button type="button" onclick="toggleCustomBall(${i})" id="btn-custom-ball-${i}" ${titleTip} class="ball ball-sm cursor-pointer transition-all ${activeClass}">${i < 10 ? '0' + i : i}</button>`;
    }
    container.innerHTML = html;
    updateCustomInputFromSet();
}

function toggleCustomBall(num) {
    if (customSelectedNumbers.has(num)) {
        customSelectedNumbers.delete(num);
    } else {
        if (customSelectedNumbers.size >= 20) {
            showToast('Chỉ nên chọn tối đa 20 con số để đảm bảo tốc độ tính toán.', 'warning');
            return;
        }
        customSelectedNumbers.add(num);
    }
    updateCustomBallUI(num);
    updateCustomInputFromSet();
}

function updateCustomBallUI(num) {
    const btn = document.getElementById(`btn-custom-ball-${num}`);
    if (!btn) return;
    const isSelected = customSelectedNumbers.has(num);
    const ballClass = getBallClass(num);
    if (isSelected) {
        btn.className = `ball ball-sm cursor-pointer transition-all ${ballClass} ring-2 ring-white scale-105 shadow-md opacity-100 font-bold`;
    } else {
        btn.className = 'ball ball-sm cursor-pointer transition-all bg-slate-800 text-slate-400 opacity-40 hover:opacity-80 border border-slate-700';
    }
}

function updateCustomInputFromSet() {
    const sorted = Array.from(customSelectedNumbers).sort((a, b) => a - b);
    const inputEl = document.getElementById('custom-pool-input');
    const countEl = document.getElementById('custom-selected-count');
    if (inputEl) inputEl.value = sorted.map(n => n < 10 ? '0' + n : '' + n).join(' ');
    if (countEl) countEl.textContent = sorted.length;
    checkPoolSuitabilityDebounced();
}

function applyCustomInputToGrid() {
    const inputEl = document.getElementById('custom-pool-input');
    if (!inputEl) return;
    const val = inputEl.value.trim();
    const parts = val.split(/[\s,;]+/).map(Number).filter(n => !isNaN(n) && n > 0);
    
    customSelectedNumbers.clear();
    parts.forEach(n => {
        if (n >= 1 && n <= 55) {
            customSelectedNumbers.add(n);
        }
    });

    initCustomBallsGrid();
    showToast(`Đã nhận ${customSelectedNumbers.size} con số hợp lệ`, 'info');
}

function clearCustomSelection() {
    customSelectedNumbers.clear();
    initCustomBallsGrid();
    showToast('Đã xóa tất cả lựa chọn', 'info');
}

function setCustomPreset(type) {
    customSelectedNumbers.clear();
    const rankings = (cachedDashboardData && cachedDashboardData.predictions && cachedDashboardData.predictions.all_rankings) 
        ? cachedDashboardData.predictions.all_rankings 
        : [];

    // Hàm trợ giúp lọc tối đa maxRepeats số vừa ra (gap === 0)
    function pickWithRepeatLimit(candidates, count, maxRepeats = 2) {
        let picked = [];
        let repeatCount = 0;
        for (const c of candidates) {
            const isRepeat = (c.gap === 0 || c.last_seen === 'Current');
            if (isRepeat) {
                if (repeatCount < maxRepeats) {
                    picked.push(c.number);
                    repeatCount++;
                }
            } else {
                picked.push(c.number);
            }
            if (picked.length >= count) break;
        }
        return picked;
    }

    if (type === 'hot') {
        // Lấy Top 12 số có điểm phong độ Model Score cao nhất (khống chế tối đa 2 số vừa ra kỳ trước)
        const top = pickWithRepeatLimit(rankings, 12, 2);
        top.forEach(num => customSelectedNumbers.add(num));
        showToast('🔥 Đã chọn dàn 12 số Top Nóng (đã khống chế tối đa 2 bóng lặp kỳ trước)', 'info');
    } else if (type === 'balanced') {
        // Phối hợp 6 Hot nhất (tối đa 1 lặp) + 6 Cold/Gan nhất (gap cao)
        const topHot = pickWithRepeatLimit(rankings, 6, 1);
        const sortedByGap = [...rankings].filter(r => !topHot.includes(r.number)).sort((a, b) => (b.gap || 0) - (a.gap || 0));
        const topCold = sortedByGap.slice(0, 6).map(r => r.number);
        topHot.forEach(num => customSelectedNumbers.add(num));
        topCold.forEach(num => customSelectedNumbers.add(num));
        showToast('⚖️ Đã chọn dàn 12 số Cân Bằng (6 Hot + 6 Cold)', 'info');
    } else if (type === 'cold_outbreak') {
        // Săn số gan / dị biệt: 4 Hot + 8 Cold nhất
        const topHot = pickWithRepeatLimit(rankings, 4, 1);
        const sortedByGap = [...rankings].filter(r => !topHot.includes(r.number)).sort((a, b) => (b.gap || 0) - (a.gap || 0));
        const topCold = sortedByGap.slice(0, 8).map(r => r.number);
        topHot.forEach(num => customSelectedNumbers.add(num));
        topCold.forEach(num => customSelectedNumbers.add(num));
        showToast('❄️ Đã chọn dàn Săn Số Gan & Dị Biệt (4 Hot + 8 Cold Gan Lớn)', 'info');
    } else if (type === 'low_comp') {
        // Nén dải thấp: Chọn các số điểm cao nhất có giá trị <= 33 (Mega) hoặc <= 40 (Power)
        const lowLimit = currentLotteryType === 'POWER_655' ? 40 : 33;
        const lowCandidates = rankings.filter(r => r.number <= lowLimit);
        const selected = pickWithRepeatLimit(lowCandidates, 12, 2);
        selected.forEach(num => customSelectedNumbers.add(num));
        showToast(`🔵 Đã chọn dàn 12 số Nén Dải Thấp (tất cả bóng ≤ ${lowLimit}, tối đa 2 bóng lặp)`, 'info');
    }

    // Nếu không có dữ liệu rankings trong cache, nạp danh sách dự phòng
    if (customSelectedNumbers.size === 0) {
        const defaultNums = currentLotteryType === 'POWER_655' 
            ? [3, 6, 11, 19, 20, 23, 24, 26, 30, 43, 48, 52] 
            : [3, 6, 11, 19, 20, 23, 24, 26, 30, 43];
        defaultNums.forEach(n => customSelectedNumbers.add(n));
        showToast('Đã nạp dàn số đề xuất mặc định', 'info');
    }

    initCustomBallsGrid();
}

async function runCustomOptimizer() {
    const nums = Array.from(customSelectedNumbers).sort((a, b) => a - b);
    if (nums.length < 6) {
        showToast('Vui lòng chọn ít nhất 6 con số để lọc tổ hợp vé.', 'error');
        return;
    }
    const countSelect = document.getElementById('custom-ticket-count');
    const ticketCount = countSelect ? parseInt(countSelect.value) : 8;

    // Tự động nhận diện nếu có số > 45 thì bắt buộc phải chuyển sang Power 6/55
    let targetLottery = currentLotteryType;
    if (nums.some(n => n > 45)) {
        if (currentLotteryType !== 'POWER_655') {
            targetLottery = 'POWER_655';
            showToast('Dàn số có chứa bóng > 45 -> Tự động tối ưu hóa theo POWER 6/55!', 'info');
            // Cập nhật tab trên màn hình cho đồng bộ
            document.querySelectorAll('.lottery-tab').forEach(tab => {
                tab.classList.remove('bg-blue-600', 'text-white');
                tab.classList.add('bg-slate-700', 'text-gray-300');
            });
            const tabP = document.getElementById('tab-POWER_655');
            if (tabP) {
                tabP.classList.remove('bg-slate-700', 'text-gray-300');
                tabP.classList.add('bg-blue-600', 'text-white');
            }
            currentLotteryType = 'POWER_655';
        }
    }

    showToast('Đang quét và chấm điểm qua 17 công thức xác suất...', 'info');

    try {
        const res = await fetch(apiUrl('/api/combinations/custom'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lottery_type: targetLottery,
                numbers: nums,
                ticket_count: ticketCount
            })
        });

        if (!res.ok) {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể tối ưu hóa'), 'error');
            return;
        }

        const data = await res.json();
        cachedCustomData = data;
        renderCustomResults(data);
        showToast(`Đã lọc ra ${data.tickets.length} vé xuất sắc nhất!`, 'success');
    } catch (e) {
        showToast('Lỗi kết nối: ' + e.message, 'error');
    }
}

function renderCustomResults(data) {
    const statsContainer = document.getElementById('custom-stats-container');
    if (statsContainer) statsContainer.classList.remove('hidden');

    const costEl = document.getElementById('custom-cost');
    const ticketLabelEl = document.getElementById('custom-ticket-label');
    const fullCostEl = document.getElementById('custom-full-cost');
    const totalCombosEl = document.getElementById('custom-total-combos');
    const savingsEl = document.getElementById('custom-savings');
    const savingsPctEl = document.getElementById('custom-savings-pct');
    const coverageEl = document.getElementById('custom-coverage');
    const copyAllBtn = document.getElementById('btn-copy-custom-all');

    if (costEl) costEl.textContent = data.formatted_cost;
    if (ticketLabelEl) ticketLabelEl.textContent = `Gồm đúng ${data.ticket_count} vé`;
    if (fullCostEl) fullCostEl.textContent = data.formatted_full_bao_cost;
    if (totalCombosEl) totalCombosEl.textContent = `Từ ${data.total_possible_combinations.toLocaleString('vi-VN')} tổ hợp gốc`;
    if (savingsEl) savingsEl.textContent = data.formatted_savings;
    if (savingsPctEl) savingsPctEl.textContent = `Tiết kiệm ${data.savings_pct}% chi phí`;
    if (coverageEl) coverageEl.textContent = `${data.triplet_coverage_pct}%`;
    if (copyAllBtn) copyAllBtn.classList.remove('hidden');

    const container = document.getElementById('custom-tickets-grid');
    if (!container) return;

    let html = '';
    data.tickets.forEach((t, idx) => {
        const numbersStr = t.numbers.map(n => n < 10 ? '0' + n : '' + n).join(', ');
        const scoreClass = t.fitness >= 75 ? 'text-emerald-400' : 'text-amber-400';
        
        let matchBadge = '';
        if (t.is_forecast_match) {
            matchBadge = `<div class="mb-2 flex items-center justify-between text-[11px] bg-indigo-950/60 border border-indigo-500/50 px-2 py-1 rounded text-indigo-300 font-medium shadow-sm">
                <span class="flex items-center gap-1">🎯 <strong>Khớp nhịp dự báo:</strong> ${t.regime_label}</span>
                <span class="font-bold text-indigo-200 font-mono">+${t.regime_bonus}đ</span>
            </div>`;
        } else if (t.regime_label) {
            matchBadge = `<div class="mb-2 flex items-center justify-between text-[10px] bg-slate-900/60 border border-slate-700/60 px-2 py-0.5 rounded text-slate-400">
                <span>Dải vé: ${t.regime_label}</span>
            </div>`;
        }

        html += `<div class="bg-slate-800 rounded-xl p-3.5 border border-slate-700 hover:border-indigo-500 shadow transition flex flex-col justify-between">
            <div class="flex items-center justify-between mb-2">
                <span class="w-6 h-6 rounded-full bg-indigo-900/80 text-indigo-200 font-bold text-xs flex items-center justify-center font-mono border border-indigo-600">
                    #${idx + 1}
                </span>
                <span class="text-xs text-slate-300">
                    Điểm 21 công thức: <strong class="${scoreClass} font-mono text-sm">${t.fitness}</strong>
                </span>
            </div>

            <div class="flex gap-1 justify-center py-2 bg-slate-900/50 rounded-lg mb-2">
                ${renderBalls(t.numbers, 'ball-sm')}
            </div>

            ${matchBadge}

            <div class="grid grid-cols-2 gap-1.5 text-[11px] text-slate-300 mb-2">
                <div class="bg-slate-900/40 px-2 py-1 rounded flex justify-between">
                    <span class="text-slate-400">Tổng (Sum):</span>
                    <strong class="text-amber-300 font-mono">${t.sum}</strong>
                </div>
                <div class="bg-slate-900/40 px-2 py-1 rounded flex justify-between">
                    <span class="text-slate-400">Chẵn/Lẻ:</span>
                    <strong class="text-slate-200">${t.odd_even}</strong>
                </div>
            </div>

            <button onclick="copyCombo('${numbersStr}')" class="w-full bg-slate-700/80 hover:bg-slate-600 text-slate-200 text-xs py-1.5 rounded transition flex items-center justify-center gap-1.5 border border-slate-600">
                <span>📋</span> Sao chép vé (${numbersStr})
            </button>
        </div>`;
    });
    container.innerHTML = html;

    if (data.suitability) {
        renderSuitabilityCard(data.suitability);
    }
}

function copyAllCustomTickets() {
    if (!cachedCustomData || !cachedCustomData.tickets) return;
    const lines = cachedCustomData.tickets.map((t, i) => `Vé ${i + 1}: ` + t.numbers.map(n => n < 10 ? '0' + n : '' + n).join(', '));
    const allText = `--- DÀN VÉ TỰ CHỌN TỐI ƯU HÓA (${cachedCustomData.pool_size} SỐ / ${cachedCustomData.ticket_count} VÉ) ---\n` + lines.join('\n');
    copyCombo(allText);
}

let suitabilityDebounceTimer = null;
function checkPoolSuitabilityDebounced() {
    clearTimeout(suitabilityDebounceTimer);
    suitabilityDebounceTimer = setTimeout(() => {
        const nums = Array.from(customSelectedNumbers);
        if (nums.length >= 6) {
            fetch(apiUrl('/api/combinations/evaluate-suitability'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ numbers: nums })
            }).then(r => r.json()).then(data => {
                renderSuitabilityCard(data);
            }).catch(() => {});
        }
    }, 300);
}

function renderSuitabilityCard(suit) {
    if (!suit) return;
    const verdictEl = document.getElementById('suitability-verdict');
    const iconEl = document.getElementById('suitability-icon');
    const megaPctEl = document.getElementById('suitability-mega-pct');
    const powerPctEl = document.getElementById('suitability-power-pct');
    const megaBar = document.getElementById('suitability-mega-bar');
    const powerBar = document.getElementById('suitability-power-bar');
    const reasonsList = document.getElementById('suitability-reasons-list');
    const switchContainer = document.getElementById('suitability-switch-container');

    if (megaPctEl) megaPctEl.textContent = `${suit.mega_pct}%`;
    if (powerPctEl) powerPctEl.textContent = `${suit.power_pct}%`;
    if (megaBar) megaBar.style.width = `${suit.mega_pct}%`;
    if (powerBar) powerBar.style.width = `${suit.power_pct}%`;

    const isRecMega = suit.recommended === 'MEGA_645';

    if (verdictEl) {
        if (suit.is_mandatory) {
            verdictEl.innerHTML = `<span class="text-rose-400">⚠️ BẮT BUỘC: POWER 6/55 (${suit.power_pct}%)</span> — Không thể chơi Mega 6/45`;
            if (iconEl) iconEl.textContent = '🚨';
        } else if (isRecMega) {
            verdictEl.innerHTML = `<span class="text-blue-400">⭐ KHUYÊN DÙNG: MEGA 6/45 (${suit.mega_pct}%)</span> — Tối ưu xác suất & kinh tế`;
            if (iconEl) iconEl.textContent = '🎯';
        } else {
            verdictEl.innerHTML = `<span class="text-purple-400">⭐ KHUYÊN DÙNG: POWER 6/55 (${suit.power_pct}%)</span> — Khớp dải số trung bình cao`;
            if (iconEl) iconEl.textContent = '⚡';
        }
    }

    if (reasonsList && suit.reasons) {
        reasonsList.innerHTML = suit.reasons.map(r => `<li>${r}</li>`).join('');
    }

    if (switchContainer) {
        if (suit.recommended !== currentLotteryType) {
            const targetType = suit.recommended;
            const targetLabel = isRecMega ? 'Mega 6/45' : 'Power 6/55';
            switchContainer.innerHTML = `<button type="button" onclick="switchLotteryAndKeepPool('${targetType}')" class="text-xs bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-3 py-1.5 rounded-lg transition shadow flex items-center gap-1.5">
                <span>👉</span> Chuyển sang ${targetLabel} ngay
            </button>`;
        } else {
            switchContainer.innerHTML = `<span class="text-xs text-emerald-400 font-bold bg-emerald-950/60 border border-emerald-600/60 px-2.5 py-1 rounded-full flex items-center gap-1">
                <span>✓</span> Đang ở đúng loại hình tối ưu
            </span>`;
        }
    }
}

function switchLotteryAndKeepPool(targetType) {
    switchLottery(targetType);
    setTimeout(() => {
        switchComboMode('custom');
        runCustomOptimizer();
    }, 200);
}



// ==================== HẾT PHẦN VÉ BAO VÀ WHEELING ====================

function renderProbabilityComparison(predictions) {
    const el = document.getElementById('math-prob');
    if (el) el.textContent = predictions.mathematical_probability + '%';
}

function renderBacktest(backtest) {
    if (!backtest || backtest.status === 'insufficient_data') {
        const container = document.getElementById('backtest-content');
        if (container) container.innerHTML = `<div class="bg-yellow-900/30 border border-yellow-600 rounded-lg p-4"><p class="text-yellow-200">${backtest ? backtest.message : 'Không đủ dữ liệu để chạy backtesting.'}</p></div>`;
        return;
    }
    
    document.getElementById('model-avg').textContent = backtest.model ? backtest.model.avg_matched.toFixed(3) : '--';
    document.getElementById('random-avg').textContent = backtest.random_baseline ? backtest.random_baseline.avg_matched.toFixed(3) : '--';
    
    const verdictEl = document.getElementById('verdict-text');
    if (verdictEl) {
        verdictEl.textContent = backtest.better_than_random ? 'Nhỉnh hơn ngẫu nhiên nhẹ' : 'Không có lợi thế vượt trội';
        verdictEl.className = backtest.better_than_random ? 'text-lg font-bold text-green-400' : 'text-lg font-bold text-red-400';
    }
    
    document.getElementById('backtest-disclaimer').textContent = backtest.verdict || backtest.disclaimer || '';
}

async function fetchData() {
    showToast('Đang tải dữ liệu từ Vietlott...', 'info');
    try {
        const response = await fetch(apiUrl('/api/fetch'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lottery_type: currentLotteryType, limit: 100 })
        });
        const data = await response.json();
        cachedBaoData = {};
        cachedWheelData = null;
        showToast(`${data.message}`, 'success');
        loadDashboard();
    } catch (error) {
        showToast('Lỗi: ' + error.message, 'error');
    }
}

function updateThreshold(value) {
    currentThreshold = parseFloat(value);
    document.getElementById('threshold-value').textContent = value;
    if (cachedDashboardData && cachedDashboardData.predictions) {
        renderPredictions(cachedDashboardData.predictions);
    }
}

function showLoading() {
    // Có thể bổ sung loading indicator nếu cần
}

function hideLoading() {}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ==========================================
// ĐA NGÔN NGỮ (I18N: VIỆT NAM & ENGLISH)
// ==========================================
let currentLang = localStorage.getItem('vietlott_lang') || 'vi';

const i18nDict = {
    vi: {
        nav_formulas: "21 Công Thức Toán Học (EN)",
        nav_refresh: "Làm mới dữ liệu",
        total_draws_label: "Tổng số kỳ quay:",
        last_updated_label: "Cập nhật lần cuối:",
        sec_draw_history: "Lịch Sử Quay Thưởng",
        sec_hot_cold: "Hot & Cold Numbers",
        sec_frequency: "Tần Suất Xuất Hiện",
        sec_predictions: "Bảng Điểm Mô Hình (Predictions)",
        filter_model_score: "Lọc Model Score ≥",
        sec_combinations: "Gợi Ý Bộ Số (Combinations)",
        sec_prob_comparison: "Xác Suất vs Mô Hình",
        sec_backtest: "Kiểm Thử Lịch Sử (Backtesting)",
        tab_standard_combos: "15 Dãy Tuyển Chọn",
        tab_wheeling_matrix: "Ma Trận Wheeling (Tiết Kiệm 99%)",
        tab_bao_combos: "Dàn Số Bao (Bao 5 - 18)",
        tab_custom_pool: "Dàn Số Tự Chọn (Custom)",
        btn_recalc_combos: "Sinh lại bộ số",
        combos_banner_title: "15 Dãy số siêu tuyển chọn (Bao quát toàn diện 5 chiến lược & 21 công thức toán học):",
        combos_banner_desc: "Bao gồm: 🏆 <strong>Tối Ưu Phong Độ</strong> (Hot Elite), ⚖️ <strong>Cân Bằng Chu Kỳ</strong> (Rebound), ❄️ <strong>Săn Số Gan & Dị Biệt</strong> (Cold Outbreak - ngừa các kỳ lệch dải cao như 04/10), 🔵 <strong>Nén Dải Thấp</strong> (Low Compression - ngừa các kỳ rút thấp như #1400), và 🌊 <strong>Bước Nhảy Delta</strong> (Spread).",
        prob_math_title: "Xác Suất Toán Học (Mathematical Probability)",
        prob_math_desc: "Đây là xác suất cố định theo cơ chế quay số. Mỗi số có xác suất bằng nhau trong mỗi kỳ quay.",
        prob_model_title: "Model Score",
        prob_model_desc: "Đây là điểm phân tích từ nhiều phương pháp thống kê. KHÔNG PHẢI xác suất trúng thưởng thực tế.",
        prob_diff_title: "Giải thích sự khác biệt:",
        prob_diff_math_label: "Mathematical Probability:",
        prob_diff_math_val: "Xác suất lý thuyết = số lượng số chọn / tổng số. Cố định cho mọi kỳ.",
        prob_diff_model_label: "Model Score:",
        prob_diff_model_val: "Điểm tổng hợp từ frequency, recency, Bayesian, Monte Carlo. Thay đổi theo dữ liệu.",
        prob_diff_conf_label: "Confidence:",
        prob_diff_conf_val: "Mức độ nhất quán giữa các phương pháp phân tích, không phải độ chắc chắn trúng thưởng.",
        regime_algo_tag: "Thuật Toán 21: Phân Phối Cực Trị & Markov Regime",
        regime_header_title: "Dự Báo Nhịp Dải & Trạng Thái Kỳ Tiếp Theo",
        regime_expected_label: "Trạng thái dự kiến:",
        regime_summary_desc: "Dựa trên Thống kê Thứ tự Cực trị $X_{(1)}$ & $X_{(6)}$, Phân phối Siêu bội và Ma trận Chuyển dịch Markov 100 kỳ quay.",
        regime_col_low: "🔵 Nén Dải Thấp (Rút thấp)",
        regime_col_std: "🟢 Cân Bằng Chuẩn (Gauss)",
        regime_col_high: "🟣 Bung Dải Cao (Cực đại)",
        regime_box_min: "Bóng nhỏ nhất (Min)",
        regime_box_max: "Bóng lớn nhất (Max)",
        regime_box_sum: "Vùng Tổng Điểm (Sum)",
        regime_rev_title: "Chỉ Số Hồi Quy Trung Bình (Mean Reversion):",
        regime_rev_desc: "Đang phân tích dao động tổng điểm và dải cực đại qua 3 kỳ gần nhất...",
        footer_warning_title: "⚠️ CẢNH BÁO:",
        footer_warning_desc: "Ứng dụng này chỉ dùng cho mục đích phân tích thống kê và giải trí.",
        footer_disclaimer: "Xổ số là trò chơi may rủi. Không có mô hình toán học hay thuật toán nào có thể dự đoán chính xác kết quả. Hãy chơi có trách nhiệm."
    },
    en: {
        nav_formulas: "21 Mathematical Formulas (EN)",
        nav_refresh: "Refresh Data",
        total_draws_label: "Total Draws:",
        last_updated_label: "Last Updated:",
        sec_draw_history: "Draw History & Results",
        sec_hot_cold: "Hot & Cold Numbers",
        sec_frequency: "Number Frequency Chart",
        sec_predictions: "Model Score Leaderboard (Predictions)",
        filter_model_score: "Filter Model Score ≥",
        sec_combinations: "Recommended Tickets (Combinations)",
        sec_prob_comparison: "Theoretical Probability vs Model",
        sec_backtest: "Historical Backtesting",
        tab_standard_combos: "15 Elite Combinations",
        tab_wheeling_matrix: "Wheeling Matrix (Save 99%)",
        tab_bao_combos: "Permutation Packages (Bao 5 - 18)",
        tab_custom_pool: "Custom Pool Optimizer",
        btn_recalc_combos: "Regenerate Tickets",
        combos_banner_title: "15 Elite Combinations (Synthesized across 5 strategies & 21 mathematical formulas):",
        combos_banner_desc: "Including: 🏆 <strong>Elite Hot Momentum</strong>, ⚖️ <strong>Balanced Cycle Rebound</strong>, ❄️ <strong>Cold Outbreak & Anomalies</strong>, 🔵 <strong>Low Band Compression</strong>, and 🌊 <strong>Natural Delta Steps Spread</strong>.",
        prob_math_title: "Theoretical Combinatorial Probability",
        prob_math_desc: "Fixed mathematical odds determined by physical lottery mechanics. Every ball holds identical baseline probability in every single draw.",
        prob_model_title: "Multi-Factor Model Score",
        prob_model_desc: "Composite ranking score computed across 8 statistical & stochastic algorithms. NOT an empirical guarantee.",
        prob_diff_title: "Key Methodological Distinctions:",
        prob_diff_math_label: "Theoretical Probability:",
        prob_diff_math_val: "Combinatorial odds = balls drawn / total pool. Constant and stationary across all draws.",
        prob_diff_model_label: "Model Score:",
        prob_diff_model_val: "Composite analytical metric synthesized from frequency, recency, Bayes, and Monte Carlo.",
        prob_diff_conf_label: "Confidence Metric:",
        prob_diff_conf_val: "Cross-model agreement level indicating algorithmic consensus, not outcome certainty.",
        regime_algo_tag: "Algorithm 21: Extreme Value & Markov Regime",
        regime_header_title: "Stochastic Regime & Next Draw Structural Forecast",
        regime_expected_label: "Forecasted Regime:",
        regime_summary_desc: "Synthesized from Extreme Order Statistics $X_{(1)}$ & $X_{(6)}$, Hypergeometric Density, and 100-Draw Markov Transition Matrix.",
        regime_col_low: "🔵 Low Band Compression",
        regime_col_std: "🟢 Gaussian Bell (Standard)",
        regime_col_high: "🟣 High Extreme Outbreak",
        regime_box_min: "Minimum Ball ($X_1$)",
        regime_box_max: "Maximum Ball ($X_6$)",
        regime_box_sum: "Expected Sum ($\Sigma$)",
        regime_rev_title: "Mean Reversion Oscillator Metric:",
        regime_rev_desc: "Analyzing 3-draw sum volatility and boundary pullbacks against theoretical mean...",
        footer_warning_title: "⚠️ DISCLAIMER:",
        footer_warning_desc: "This application is built strictly for educational, statistical, and entertainment purposes.",
        footer_disclaimer: "Lottery draws are purely stochastic random events. No algorithmic model can guarantee future outcomes. Please play responsibly."
    }
};

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('vietlott_lang', lang);
    applyLanguage(lang);
}

function applyLanguage(lang) {
    const dict = i18nDict[lang] || i18nDict['vi'];

    // Update buttons in navbar
    const btnVi = document.getElementById('lang-btn-vi');
    const btnEn = document.getElementById('lang-btn-en');
    if (btnVi && btnEn) {
        if (lang === 'vi') {
            btnVi.className = "px-2.5 py-1 text-xs font-bold rounded transition bg-blue-600 text-white shadow";
            btnEn.className = "px-2.5 py-1 text-xs font-bold rounded transition text-slate-400 hover:text-white";
        } else {
            btnVi.className = "px-2.5 py-1 text-xs font-bold rounded transition text-slate-400 hover:text-white";
            btnEn.className = "px-2.5 py-1 text-xs font-bold rounded transition bg-blue-600 text-white shadow";
        }
    }

    // Apply all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.innerHTML = dict[key];
        }
    });

    // Re-render components with cached data if available
    if (cachedDashboardData) {
        renderDashboard(cachedDashboardData);
    }
}

// Modal control for 21 formulas
function openFormulasModal() {
    const modal = document.getElementById('formulas-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeFormulasModal() {
    const modal = document.getElementById('formulas-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('formulas-modal');
    if (modal && e.target === modal) {
        closeFormulasModal();
    }
});

// Close modal on Escape key
window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeFormulasModal();
    }
});

