/**
 * Painel de Apostas & Transmissão
 * Monitoramento em tempo real de apostas, transmissão e desyncs
 */

// ============ STATE ============

let panelData = null;
let autoRefreshInterval = null;
let alertSoundEnabled = true;
let lastAlertState = 'ok';
let countdownIntervalId = null;
let currentConfig = null;

// ============ INIT ============

document.addEventListener('DOMContentLoaded', () => {
  console.log('🎰 Painel de Apostas inicializado');
  
  // Carrega dados iniciais
  refreshPanelData();
  
  // Auto-refresh a cada 3 segundos
  autoRefreshInterval = setInterval(refreshPanelData, 3000);
  
  // Para de fazer refresh se sair da página
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && autoRefreshInterval) {
      clearInterval(autoRefreshInterval);
    } else if (!document.hidden && !autoRefreshInterval) {
      autoRefreshInterval = setInterval(refreshPanelData, 3000);
    }
  });
  
  // Setup URL Configuration
  setupUrlConfiguration();

  // Setup alert sound toggle
  setupAlertSoundToggle();
});

// ============ API CALLS ============

async function refreshPanelData() {
  try {
    const [betData, desyncData, perfData, currentGameData] = await Promise.all([
      fetchBetPanelData(),
      fetchDesyncData(),
      fetchPerformanceAnalysis(),
      fetchCurrentGameData()
    ]);
    
    panelData = { ...betData, ...desyncData, ...perfData, ...currentGameData };
    renderPanelData();
    updateStatus('Conectado', 'ok');
  } catch (error) {
    console.error('❌ Erro ao carregar dados do painel:', error);
    updateStatus('Erro na conexão', 'error');
  }
}

async function fetchBetPanelData() {
  const response = await fetch('/api/bet-panel?minutes=60');
  if (!response.ok) throw new Error('API error');
  return response.json();
}

async function fetchDesyncData() {
  const response = await fetch('/api/transmission-bet-status?minutes=60&limit=50');
  if (!response.ok) throw new Error('API error');
  return response.json();
}

async function fetchPerformanceAnalysis() {
  const response = await fetch('/api/performance-analysis?minutes=1440');
  if (!response.ok) throw new Error('API error');
  return response.json();
}

async function fetchCurrentGameData() {
  try {
    const response = await fetch('/api/current-game?minutes=5');
    if (!response.ok) throw new Error('API error');
    return response.json();
  } catch (error) {
    console.warn('⚠️ Erro ao buscar dados do jogo atual:', error);
    return { current_game: null };
  }
}

function setupAlertSoundToggle() {
  const toggleBtn = document.getElementById('alertSoundToggle');
  if (!toggleBtn) return;

  const stored = localStorage.getItem('alertSoundEnabled');
  alertSoundEnabled = stored ? stored === 'true' : true;
  toggleBtn.textContent = alertSoundEnabled ? '🔔 Som: ON' : '🔕 Som: OFF';

  toggleBtn.addEventListener('click', () => {
    alertSoundEnabled = !alertSoundEnabled;
    localStorage.setItem('alertSoundEnabled', String(alertSoundEnabled));
    toggleBtn.textContent = alertSoundEnabled ? '🔔 Som: ON' : '🔕 Som: OFF';
  });
}

function playAlertSound() {
  if (!alertSoundEnabled) return;

  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const audioContext = new AudioContext();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.type = 'sine';
    oscillator.frequency.value = 880;
    gainNode.gain.value = 0.05;

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    oscillator.start();

    setTimeout(() => {
      oscillator.stop();
      audioContext.close();
    }, 200);
  } catch (error) {
    console.warn('⚠️ Falha ao tocar alerta sonoro:', error);
  }
}

function getHostLabel(urlValue) {
  if (!urlValue) return 'N/A';
  try {
    const parsed = new URL(urlValue);
    return parsed.host || urlValue;
  } catch (error) {
    return urlValue;
  }
}

function updateCurrentSources() {
  const txEl = document.getElementById('currentTxSource');
  const betEl = document.getElementById('currentBetSource');
  if (!txEl || !betEl) return;

  const provider = currentConfig?.transmission_provider || 'live_http';
  const providerLabel = provider === 'live_ws' ? 'WS' : 'HTTP';
  const txHost = getHostLabel(currentConfig?.live_feed_ws_url);
  const betHost = getHostLabel(currentConfig?.bet_url);

  txEl.textContent = txHost === 'N/A' ? providerLabel : `${providerLabel} | ${txHost}`;
  betEl.textContent = betHost;
}


// ============ RENDERING ============

function renderPanelData() {
  if (!panelData) return;
  
  // Renderiza dados do jogo atual
  renderCurrentGameData(panelData);
  
  // Estatísticas de Apostas
  const bets = panelData.bets || {};
  document.getElementById('stat-detectadas').textContent = bets.detectadas || 0;
  document.getElementById('stat-executadas').textContent = bets.apostou || 0;
  document.getElementById('stat-bloqueadas').textContent = bets.bloqueadas || 0;
  document.getElementById('stat-expiradas').textContent = bets.expiradas || 0;
  
  // Taxa de sucesso
  const total = (bets.detectadas || 0) + (bets.bloqueadas || 0) + (bets.expiradas || 0);
  const taxa = total > 0 ? ((bets.apostou || 0) / total * 100).toFixed(1) : 0;
  document.getElementById('taxa-sucesso').textContent = `${taxa}%`;
  
  // Histórico de apostas
  renderBetHistory();
  
  // Transmissão
  const transmission = panelData.transmission || {};
  document.getElementById('stat-desyncs').textContent = transmission.desync_count || 0;
  document.getElementById('stat-delays').textContent = transmission.delay_count || 0;
  document.getElementById('lag-medio').textContent = `${transmission.avg_lag || 0}ms`;
  
  // OTT Analysis
  const ottAnalysis = panelData.ott_analysis || {};
  document.getElementById('ott-health-score').textContent = ottAnalysis.health_score || 0;
  document.getElementById('ott-sync-quality').textContent = `${ottAnalysis.sync_quality || 0}%`;
  document.getElementById('ott-status').textContent = ottAnalysis.status === 'active' ? '✅ Ativo' : '⚠️ Aviso';
  document.getElementById('ott-sources').textContent = ottAnalysis.sources && ottAnalysis.sources.length > 0 ? ottAnalysis.sources.join(', ') : 'N/A';
  document.getElementById('ott-placars').textContent = `${ottAnalysis.placars_monitored || 0} placar(es)`;
  
  // Decision Analysis
  const decisionAnalysis = panelData.decision_analysis || {};
  if (decisionAnalysis.total_signals) {
    document.getElementById('decision-accuracy').textContent = `${Math.round(decisionAnalysis.accuracy_rate)}%`;
    document.getElementById('decision-signals').textContent = decisionAnalysis.total_signals;
    
    const breakdown = decisionAnalysis.decision_breakdown;
    document.getElementById('decision-executed-pct').textContent = `${Math.round(breakdown.executed_pct || 0)}%`;
    document.getElementById('decision-executed-count').textContent = `${decisionAnalysis.executed} apostas`;
    document.getElementById('decision-blocked-pct').textContent = `${Math.round(breakdown.blocked_pct || 0)}%`;
    document.getElementById('decision-blocked-count').textContent = `${decisionAnalysis.blocked} bloqueadas`;
    document.getElementById('decision-expired-pct').textContent = `${Math.round(breakdown.expired_pct || 0)}%`;
    document.getElementById('decision-expired-count').textContent = `${decisionAnalysis.expired} expiradas`;
    
    renderDecisionConflicts(decisionAnalysis.conflicts || []);
  }
  
  // Desyncs
  if (transmission.desync_events && transmission.desync_events.length > 0) {
    document.getElementById('desyncCard').style.display = 'block';
    renderDesyncList(transmission.desync_events);
  } else {
    document.getElementById('desyncCard').style.display = 'none';
  }
  
  // Delays
  if (transmission.delay_events && transmission.delay_events.length > 0) {
    document.getElementById('delayCard').style.display = 'block';
    renderDelayList(transmission.delay_events);
  } else {
    document.getElementById('delayCard').style.display = 'none';
  }
  
  // Performance Analysis
  renderPerformanceAnalysis(panelData);
}

function renderBetHistory() {
  const bets = panelData.recent_bets || [];
  const container = document.getElementById('betList');
  
  if (bets.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <div class="empty-state-text">Nenhuma aposta registrada no período</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = bets.map((bet, idx) => {
    const statusClass = bet.status.toLowerCase();
    const timeAgo = formatTimeAgo(bet.timestamp);
    const confidencePercent = bet.confidence ? (bet.confidence * 100).toFixed(0) : '?';
    
    return `
      <div class="bet-item ${statusClass}">
        <div class="bet-item-left">
          <div class="bet-game">${bet.game || 'N/A'}</div>
          <div class="bet-info">
            <div class="bet-info-item">
              <span class="bet-info-label">Tipo:</span>
              <strong>${bet.type || '?'}</strong>
            </div>
            <div class="bet-info-item">
              <span class="bet-info-label">Confiança:</span>
              <strong>${confidencePercent}%</strong>
            </div>
            ${bet.signal_id ? `
              <div class="bet-info-item">
                <span class="bet-info-label">ID:</span>
                <strong>${bet.signal_id.substring(0, 8)}...</strong>
              </div>
            ` : ''}
          </div>
        </div>
        <div class="bet-item-right">
          <div class="bet-status ${statusClass}">
            ${getStatusLabel(bet.status)}
          </div>
          <div class="bet-time">${timeAgo}</div>
        </div>
      </div>
    `;
  }).join('');
}

function renderCurrentGameData(panelData) {
  const gameData = panelData?.current_game || null;
  
  if (!gameData) {
    // Se não hay dados, mostra placeholder
    document.getElementById('currentGameCompactName').textContent = 'Nenhum jogo ativo';
    document.getElementById('currentGameCompactPlacar').textContent = '-- : --';
    document.getElementById('currentGameCompactQuarter').textContent = 'Q0';
    document.getElementById('currentGameCompactQuality').textContent = '--%';
    document.getElementById('currentGameCompactStatus').textContent = 'N/A';
    document.getElementById('currentGameCompactDelay').textContent = '0s';
    document.getElementById('currentGameCompactDesyncs').textContent = '0';
    document.getElementById('currentGameCompactHealth').textContent = '100%';
    document.getElementById('currentCompactRecommendation').textContent = '⏸️ AGUARDANDO';
    document.getElementById('currentCompactRisk').textContent = 'N/A';
    document.getElementById('currentCompactConfidence').textContent = '0%';
    updateCurrentSources();

    const alertBanner = document.getElementById('currentAlertBanner');
    const gameSection = document.getElementById('currentGameSection');
    if (alertBanner) alertBanner.style.display = 'none';
    if (gameSection) gameSection.style.borderColor = 'var(--neon-cyan)';
    lastAlertState = 'ok';
    return;
  }
  
  const game = gameData.game || {};
  const transmission = gameData.transmission || {};
  const recommendation = gameData.recommendation || {};
  
  // Game info
  document.getElementById('currentGameCompactName').textContent = game.name || 'Jogo desconhecido';
  
  // Placar
  const placar = `${game.placar?.t_a || '--'} : ${game.placar?.t_b || '--'}`;
  document.getElementById('currentGameCompactPlacar').textContent = placar;
  document.getElementById('currentGameCompactQuarter').textContent = game.quarter || 'Q0';
  
  // Quality
  document.getElementById('currentGameCompactQuality').textContent = `${transmission.quality || 0}%`;
  
  // Status
  const statusText = transmission.status === 'critical' ? '❌ Critico' : transmission.status === 'warning' ? '⚠️ Alerta' : '✅ OK';
  const statusEl = document.getElementById('currentGameCompactStatus');
  if (statusEl) {
    statusEl.textContent = statusText;
    statusEl.style.color = transmission.status === 'critical'
      ? 'var(--neon-pink)'
      : transmission.status === 'warning'
        ? 'var(--neon-yellow)'
        : 'var(--neon-green)';
  }
  
  // Delay
  const delay = transmission.delay || 0;
  const delayEl = document.getElementById('currentGameCompactDelay');
  if (delayEl) {
    delayEl.textContent = `${delay}s`;
    delayEl.style.color = delay > 5
      ? 'var(--neon-pink)'
      : delay > 3
        ? 'var(--neon-yellow)'
        : 'var(--neon-green)';
  }
  
  // Desyncs
  document.getElementById('currentGameCompactDesyncs').textContent = transmission.desyncs || 0;
  
  // Health score
  const health = transmission.health_score || 0;
  const healthEl = document.getElementById('currentGameCompactHealth');
  if (healthEl) {
    healthEl.textContent = `${health}%`;
    healthEl.style.color = health < 50
      ? 'var(--neon-pink)'
      : health < 70
        ? 'var(--neon-yellow)'
        : 'var(--neon-green)';
  }

  // Alert handling (delay > 3s or health < 70%)
  const alertBanner = document.getElementById('currentAlertBanner');
  const alertText = document.getElementById('currentAlertText');
  const gameSection = document.getElementById('currentGameSection');
  const isWarning = delay > 3 || health < 70;
  const isCritical = delay > 5 || health < 50;
  const alertState = isCritical ? 'critical' : isWarning ? 'warning' : 'ok';

  if (alertBanner && alertText && gameSection) {
    if (alertState === 'ok') {
      alertBanner.style.display = 'none';
      gameSection.style.borderColor = 'var(--neon-cyan)';
    } else {
      alertBanner.style.display = 'flex';
      if (isCritical) {
        alertBanner.style.background = 'rgba(255, 0, 128, 0.12)';
        alertBanner.style.borderColor = 'var(--neon-pink)';
        alertText.style.color = 'var(--neon-pink)';
        alertText.textContent = delay > 5 && health < 50
          ? '🚨 Delay critico e saude baixa'
          : delay > 5
            ? '🚨 Delay critico acima de 5s'
            : '🚨 Saude abaixo de 50%';
        gameSection.style.borderColor = 'var(--neon-pink)';
      } else {
        alertBanner.style.background = 'rgba(255, 255, 0, 0.12)';
        alertBanner.style.borderColor = 'var(--neon-yellow)';
        alertText.style.color = 'var(--neon-yellow)';
        alertText.textContent = delay > 3 && health < 70
          ? '⚠️ Delay alto e saude abaixo de 70%'
          : delay > 3
            ? '⚠️ Delay acima de 3s'
            : '⚠️ Saude abaixo de 70%';
        gameSection.style.borderColor = 'var(--neon-yellow)';
      }
    }
  }

  if (alertState !== 'ok' && alertState !== lastAlertState) {
    playAlertSound();
  }
  lastAlertState = alertState;
  
  // Recommendation
  const canBet = recommendation.can_bet || false;
  const recText = canBet ? '✅ PODE' : '❌ NAO';
  const recEl = document.getElementById('currentCompactRecommendation');
  if (recEl) {
    recEl.textContent = recText;
    recEl.style.color = canBet ? 'var(--neon-green)' : 'var(--neon-pink)';
  }
  
  // Recommendation details
  document.getElementById('currentCompactRisk').textContent = recommendation.risk || 'Desconhecido';
  document.getElementById('currentCompactConfidence').textContent = `${recommendation.confidence || 0}%`;

  // Sources
  updateCurrentSources();
  
  // Countdown timer
  let countdown = 3;
  const counterEl = document.getElementById('countdownTimer');
  if (countdownIntervalId) {
    clearInterval(countdownIntervalId);
  }
  countdownIntervalId = setInterval(() => {
    countdown--;
    if (counterEl) {
      counterEl.textContent = `${Math.max(0, countdown)}s`;
    }
    if (countdown <= 0) {
      clearInterval(countdownIntervalId);
      countdownIntervalId = null;
      countdown = 3;
    }
  }, 1000);
}

function renderDesyncList(desyncs) {
  const container = document.getElementById('desyncList');
  
  if (desyncs.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">✓</div>
        <div class="empty-state-text">Nenhum desync detectado no período</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = desyncs.slice(0, 20).map(desync => {
    const timeAgo = formatTimeAgo(desync.ts);
    
    return `
      <div class="transmission-item">
        <div class="transmission-header">
          <div class="transmission-meta">
            <div class="transmission-scores">
              Transmissão: ${desync.transmission} → 
              Bet: ${desync.bet}
            </div>
          </div>
          <div class="transmission-diff">
            ${desync.diff}
          </div>
        </div>
        <div class="transmission-time">${timeAgo}</div>
        ${desync.point_type ? `
          <div style="font-size: 0.85rem; color: var(--text-secondary);">
            Tipo: <strong>${desync.point_type}</strong>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function renderDelayList(delays) {
  const container = document.getElementById('delayList');
  
  if (delays.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">✓</div>
        <div class="empty-state-text">Nenhum delay detectado no período</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = delays.slice(0, 25).map(delay => {
    const timeAgo = formatTimeAgo(delay.ts);
    
    return `
      <div class="delay-item">
        <div class="delay-info">
          <div class="delay-target">
            Alvo: ${delay.target_a || '?'} - ${delay.target_b || '?'} | 
            Aposta: ${delay.bet_a || '?'} - ${delay.bet_b || '?'}
          </div>
          <div class="delay-details">
            <span>Age: <strong>${delay.age_seconds || 0}s</strong></span>
            <span>Threshold: <strong>${delay.threshold || 5}s</strong></span>
            <span>Source: <strong>${delay.source || 'N/A'}</strong></span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.3rem;">
            ${timeAgo}
          </div>
        </div>
        <div class="delay-badge">
          ⏱️ DELAY
        </div>
      </div>
    `;
  }).join('');
}

function renderDecisionConflicts(conflicts) {
  const container = document.getElementById('conflictsList');
  
  if (!conflicts || conflicts.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">✓</div>
        <div class="empty-state-text">Nenhum conflito detectado</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = conflicts.map(conflict => {
    const timeAgo = formatTimeAgo(conflict.ts);
    const type = conflict.type === 'desync_conflict' ? 'DESYNC' : 'DELAY';
    const badgeClass = conflict.impact === 'high' ? 'high' : 
                      conflict.impact === 'medium' ? 'medium' : 'low';
    
    // Build the main info text
    let infoText = '';
    if (conflict.type === 'desync_conflict') {
      infoText = `Transmissão: <strong>${conflict.transmission_score}</strong> | Aposta: <strong>${conflict.bet_score}</strong> | Diff: <strong>${conflict.difference}</strong>`;
    } else {
      infoText = `Lag: <strong>${conflict.age_seconds || 0}s</strong> / Threshold: <strong>${conflict.threshold || 5}s</strong>`;
    }
    
    return `
      <div class="conflict-item ${badgeClass}">
        <div style="flex: 1;">
          <div class="conflict-type">⚠️ ${type}</div>
          <div class="conflict-details">
            ${infoText}
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.3rem;">${timeAgo}</div>
          </div>
        </div>
        <div class="conflict-badge ${badgeClass}">
          ${conflict.impact.toUpperCase()}
        </div>
      </div>
    `;
  }).join('');
}

// ============ UTILITIES ============

function getStatusLabel(status) {
  const map = {
    'DETECTADO': 'Detectada',
    'APOSTOU': 'Executada',
    'BLOQUEADO': 'Bloqueada',
    'EXPIROU': 'Expirada'
  };
  return map[status] || status;
}

function formatTimeAgo(timestamp) {
  const now = Date.now() / 1000;
  const diff = now - timestamp;
  
  if (diff < 60) return `${Math.round(diff)}s atrás`;
  if (diff < 3600) return `${Math.round(diff / 60)}m atrás`;
  return `${Math.round(diff / 3600)}h atrás`;
}

function updateStatus(text, state) {
  const statusEl = document.getElementById('statusText');
  const dotEl = document.querySelector('.status-dot');
  
  if (statusEl) statusEl.textContent = text;
  
  if (dotEl) {
    dotEl.style.background = state === 'ok' ? 'var(--neon-green)' : 'var(--neon-orange)';
  }
}

function goToDashboard() {
  window.location.href = '/modern';
}

// ============ URL CONFIGURATION ============

function setupUrlConfiguration() {
  const saveBtn = document.getElementById('saveUrlsBtn');
  const betUrlInput = document.getElementById('betUrl');
  const transmissionUrlInput = document.getElementById('transmissionUrl');
  const providerSelect = document.getElementById('transmissionProvider');
  const messageEl = document.getElementById('urlMessage');
  
  if (!saveBtn) return;
  
  // Load current URLs from API status
  loadCurrentUrls();
  
  // Save URLs when button clicked
  saveBtn.addEventListener('click', saveUrls);
  
  // Update placeholder when provider changes
  providerSelect?.addEventListener('change', () => {
    const placeholder = providerSelect.value === 'live_ws'
      ? 'ws://exemplo.com/live'
      : providerSelect.value === 'bllsport_net'
        ? 'https://bllsport.com/view/...?...'
        : 'https://bllsport.com/view/...';
    transmissionUrlInput.placeholder = placeholder;
  });
}

async function loadCurrentUrls() {
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error('Erro ao carregar status');
    
    const data = await response.json();
    const config = data.config || {};
    currentConfig = config;
    
    document.getElementById('betUrl').value = config.bet_url || '';
    document.getElementById('transmissionUrl').value = config.live_feed_ws_url || '';
    document.getElementById('transmissionProvider').value = config.transmission_provider || 'live_http';
    updateCurrentSources();
  } catch (error) {
    console.error('❌ Erro ao carregar URLs:', error);
  }
}

async function saveUrls() {
  const betUrl = document.getElementById('betUrl').value.trim();
  const transmissionUrl = document.getElementById('transmissionUrl').value.trim();
  const transmissionProvider = document.getElementById('transmissionProvider').value;
  const saveBtn = document.getElementById('saveUrlsBtn');
  const messageEl = document.getElementById('urlMessage');
  
  if (!betUrl || !transmissionUrl) {
    showMessage('❌ Preencha todas as URLs', 'error');
    return;
  }
  
  saveBtn.disabled = true;
  saveBtn.textContent = '⏳ Salvando...';
  
  try {
    const response = await fetch('/api/config/update-urls', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bet_url: betUrl,
        live_feed_ws_url: transmissionUrl,
        transmission_provider: transmissionProvider
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao salvar URLs');
    }
    
    await response.json();
    showMessage('✅ URLs salvas com sucesso!', 'success');
    
    setTimeout(() => {
      saveBtn.disabled = false;
      saveBtn.textContent = '💾 Salvar URLs';
      showMessage('', '');
    }, 3000);
  } catch (error) {
    showMessage(`❌ Erro: ${error.message}`, 'error');
    saveBtn.disabled = false;
    saveBtn.textContent = '💾 Salvar URLs';
  }
}

function showMessage(text, type) {
  const messageEl = document.getElementById('urlMessage');
  if (!messageEl) return;
  
  messageEl.textContent = text;
  messageEl.style.display = text ? 'inline-block' : 'none';
  
  if (type === 'success') {
    messageEl.style.color = 'var(--neon-green)';
  } else if (type === 'error') {
    messageEl.style.color = 'var(--neon-pink)';
  }
}

// ============ PERFORMANCE ANALYSIS ============

function renderPerformanceAnalysis(data) {
  if (!data || !data.quarter_analysis) return;
  
  const quarters = data.quarter_analysis || {};
  const confidence = data.confidence_quartiles || {};
  const stages = data.stage_analysis || {};
  const metrics = data.key_metrics || {};
  const bankroll = data.bankroll_management || {};
  
  // Render Quarters
  ['Q1', 'Q2', 'Q3', 'Q4'].forEach(q => {
    const qData = quarters[q] || {};
    document.getElementById(`quarter-${q.toLowerCase()}-wins`).textContent = 
      `${qData.success || 0}/${qData.total || 0}`;
    document.getElementById(`quarter-${q.toLowerCase()}-rate`).textContent = 
      `${qData.win_rate || 0}%`;
  });
  
  // Render Confidence Quartiles
  const confKeys = ['Q1_low', 'Q2_medium', 'Q3_high', 'Q4_very_high'];
  const confIds = ['conf-q1', 'conf-q2', 'conf-q3', 'conf-q4'];
  
  confKeys.forEach((key, idx) => {
    const cData = confidence[key] || {};
    const id = confIds[idx];
    document.getElementById(`${id}-rate`).textContent = `${cData.rate || 0}%`;
    document.getElementById(`${id}-wins`).textContent = `${cData.success || 0}`;
    document.getElementById(`${id}-total`).textContent = `${cData.total || 0}`;
  });
  
  // Render Stages
  const stageKeys = ['pre_game', 'inicio', 'meio', 'final'];
  const stageIds = ['stage-pre', 'stage-inicio', 'stage-meio', 'stage-final'];
  
  stageKeys.forEach((key, idx) => {
    const sData = stages[key] || {};
    const id = stageIds[idx];
    document.getElementById(`${id}-wins`).textContent = `${sData.success || 0}`;
    document.getElementById(`${id}-total`).textContent = `${sData.total || 0}`;
    document.getElementById(`${id}-rate`).textContent = `${sData.rate || 0}%`;
  });
  
  // Render Key Metrics
  document.getElementById('metric-win-rate').textContent = `${metrics.win_rate || 0}%`;
  document.getElementById('metric-roi').textContent = `${metrics.roi || 0}%`;
  document.getElementById('metric-odds').textContent = `${(metrics.avg_odds || 0).toFixed(2)}`;
  document.getElementById('metric-ev').textContent = `${(metrics.expected_value || 0).toFixed(3)}`;
  
  // Render Bankroll Management
  const lotes = bankroll.lotes || {};
  
  if (lotes.conservative) {
    document.getElementById('bankroll-cons-alloc').textContent = 
      `R$ ${lotes.conservative.allocation || 0}`;
    document.getElementById('bankroll-cons-roi').textContent = 
      `${lotes.conservative.expected_roi || 0}%`;
  }
  
  if (lotes.moderate) {
    document.getElementById('bankroll-mod-alloc').textContent = 
      `R$ ${lotes.moderate.allocation || 0}`;
    document.getElementById('bankroll-mod-roi').textContent = 
      `${lotes.moderate.expected_roi || 0}%`;
  }
  
  if (lotes.aggressive) {
    document.getElementById('bankroll-agg-alloc').textContent = 
      `R$ ${lotes.aggressive.allocation || 0}`;
    document.getElementById('bankroll-agg-roi').textContent = 
      `${lotes.aggressive.expected_roi || 0}%`;
  }
  
  if (lotes.recovery) {
    document.getElementById('bankroll-rec-alloc').textContent = 
      `R$ ${lotes.recovery.allocation || 0}`;
    document.getElementById('bankroll-rec-roi').textContent = 
      `${lotes.recovery.expected_roi || 0}%`;
  }
  
  // Render Recommendations
  renderRecommendations(bankroll.recommendations || []);
}

function renderRecommendations(recommendations) {
  const container = document.getElementById('recommendations-list');
  
  if (!recommendations || recommendations.length === 0) {
    container.innerHTML = `
      <div style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1rem;">
        Sem recomendações no momento
      </div>
    `;
    return;
  }
  
  container.innerHTML = recommendations.map(rec => {
    const bgColor = rec.type === 'success' ? 'rgba(76, 175, 80, 0.1)' :
                   rec.type === 'warning' ? 'rgba(255, 193, 7, 0.1)' :
                   'rgba(0, 217, 255, 0.1)';
    
    const borderColor = rec.type === 'success' ? 'var(--neon-green)' :
                       rec.type === 'warning' ? 'var(--neon-yellow)' :
                       'var(--neon-cyan)';
    
    return `
      <div style="background: ${bgColor}; padding: 0.75rem; border-radius: 6px; border-left: 3px solid ${borderColor}; font-size: 0.9rem;">
        <div style="color: var(--text-primary); margin-bottom: 0.3rem;">${rec.text}</div>
        <div style="color: var(--text-muted); font-size: 0.8rem;">▶ ${rec.action}</div>
      </div>
    `;
  }).join('');
}

// ============ EXPORT ============

console.log('✅ app-bet-panel.js carregado');
