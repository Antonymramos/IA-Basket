// =========================================
// JARVIS IA BASKET - Modern React App 2026
// =========================================

const { useState, useEffect, useRef, useCallback, useMemo } = React;
const e = React.createElement;

// ========== UTILITY HOOKS ==========
function useInterval(callback, delay) {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay !== null) {
      const id = setInterval(() => savedCallback.current(), delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue];
}

// ========== MODERN CARD COMPONENT ==========
function ModernCard({ title, icon, badge, children, className = '' }) {
  return e('div', { className: `modern-card ${className}` },
    e('div', { className: 'card-header' },
      e('div', { className: 'card-title' },
        icon && e('span', { className: 'card-icon' }, icon),
        title
      ),
      badge && e('span', { className: `card-badge badge-${badge.type}` }, badge.text)
    ),
    children
  );
}

// ========== STAT ITEM COMPONENT ==========
function StatItem({ value, label, color = 'cyan' }) {
  return e('div', { className: 'stat-item' },
    e('div', { className: 'stat-value', style: { color: `var(--neon-${color})` } }, value),
    e('div', { className: 'stat-label' }, label)
  );
}

// ========== PROGRESS BAR COMPONENT ==========
function ProgressBar({ value, max = 100, color = 'cyan' }) {
  const percentage = Math.min((value / max) * 100, 100);
  return e('div', { className: 'progress-bar' },
    e('div', { 
      className: 'progress-fill',
      style: { 
        width: `${percentage}%`,
        background: `linear-gradient(90deg, var(--neon-${color}), var(--neon-green))`
      }
    })
  );
}

// ========== CHART COMPONENT ==========
function ChartComponent({ data, type = 'line' }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !window.Chart) return;

    const ctx = canvasRef.current.getContext('2d');
    
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    chartRef.current = new Chart(ctx, {
      type: type,
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#cbd5e0',
              font: { family: 'Inter', size: 12 }
            }
          }
        },
        scales: type !== 'doughnut' && type !== 'pie' ? {
          y: {
            ticks: { color: '#718096' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          x: {
            ticks: { color: '#718096' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        } : {}
      }
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [data, type]);

  return e('canvas', { ref: canvasRef, style: { maxHeight: '300px' } });
}

// ========== MAIN APP COMPONENT ==========
function App() {
  // State Management
  const [status, setStatus] = useState(null);
  const [jarvisBriefing, setJarvisBriefing] = useState(null);
  const [jarvisIntel, setJarvisIntel] = useState(null);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [ensembleStats, setEnsembleStats] = useState(null);
  const [patternInsights, setPatternInsights] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  
  // Gemini Insights State
  const [geminiInsight, setGeminiInsight] = useState('');
  const [geminiLoading, setGensLoading] = useState(false);
  
  // Settings
  const [autoRefresh, setAutoRefresh] = useLocalStorage('autoRefresh', true);
  const [refreshInterval, setRefreshInterval] = useLocalStorage('refreshInterval', 3000);
  
  // ========== API CALLS - OTIMIZADO ==========
  
  // Endpoint agregado que carrega todos os dados em uma única chamada
  const fetchDashboardData = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard/modern');
      const data = await res.json();
      
      // Atualizar todos os estados com uma única requisição
      if (data.intelligence) setJarvisIntel(data.intelligence);
      if (data.briefing) setJarvisBriefing(data.briefing);
      if (data.patterns) setPatternInsights(data.patterns);
      if (data.weekly_summary) setWeeklySummary(data.weekly_summary);
      if (data.feedback_stats) setFeedbackStats(data.feedback_stats);
      if (data.system_health) {
        setStatus(prev => ({
          ...prev,
          auto_bet: data.system_health.auto_bet,
          last_update: data.system_health.last_update
        }));
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error('Error loading status:', err);
    }
  }, []);

  const fetchEnsembleStats = useCallback(async () => {
    try {
      const res = await fetch('/api/ensemble-stats?minutes=60&limit=30');
      const data = await res.json();
      setEnsembleStats(data);
    } catch (err) {
      console.error('Error loading ensemble stats:', err);
    }
  }, []);

  const fetchSystemHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/system-health?minutes=60');
      const data = await res.json();
      setSystemHealth(data);
    } catch (err) {
      console.error('Error loading system health:', err);
    }
  }, []);

  const fetchGeminiInsight = useCallback(async (prompt) => {
    setGensLoading(true);
    try {
      const res = await fetch('/api/knowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      setGeminiInsight(data.response || 'Sem resposta');
    } catch (err) {
      setGeminiInsight('Erro ao consultar Gemini: ' + err.message);
    } finally {
      setGensLoading(false);
    }
  }, []);
  
  // Novo: Fetch rápido de insights usando o endpoint otimizado
  const fetchQuickInsight = useCallback(async (topic) => {
    setGensLoading(true);
    try {
      const res = await fetch(`/api/gemini/auto-insight?topic=${topic}`);
      const data = await res.json();
      setGeminiInsight(data.insight || 'Sem resposta');
    } catch (err) {
      setGeminiInsight('Erro ao gerar insight: ' + err.message);
    } finally {
      setGensLoading(false);
    }
  }, []);

  // Refresh All Data - OTIMIZADO com endpoint agregado
  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchStatus(),
      fetchDashboardData(), // 1 chamada ao invés de 6!
      fetchEnsembleStats(),
      fetchSystemHealth()  // Saúde do sistema
    ]);
  }, [fetchStatus, fetchDashboardData, fetchEnsembleStats, fetchSystemHealth]);
  // Initial Load
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // Auto Refresh
  useInterval(() => {
    if (autoRefresh) {
      refreshAll();
    }
  }, autoRefresh ? refreshInterval : null);

  // ========== CHART DATA ==========
  const performanceChartData = useMemo(() => {
    if (!feedbackStats || !feedbackStats.summary) return null;

    return {
      labels: ['Ganhas', 'Perdidas'],
      datasets: [{
        label: 'Apostas',
        data: [feedbackStats.summary.wins || 0, feedbackStats.summary.losses || 0],
        backgroundColor: [
          'rgba(0, 255, 136, 0.6)',
          'rgba(255, 51, 102, 0.6)'
        ],
        borderColor: [
          'rgba(0, 255, 136, 1)',
          'rgba(255, 51, 102, 1)'
        ],
        borderWidth: 2
      }]
    };
  }, [feedbackStats]);

  const accuracyChartData = useMemo(() => {
    if (!feedbackStats || !feedbackStats.accuracy_by_points) return null;

    const labels = Object.keys(feedbackStats.accuracy_by_points);
    const accuracies = labels.map(key => (feedbackStats.accuracy_by_points[key].accuracy || 0) * 100);

    return {
      labels: labels.map(l => `${l} pontos`),
      datasets: [{
        label: 'Acurácia (%)',
        data: accuracies,
        backgroundColor: 'rgba(0, 217, 255, 0.6)',
        borderColor: 'rgba(0, 217, 255, 1)',
        borderWidth: 2,
        fill: true
      }]
    };
  }, [feedbackStats]);

  // ========== RENDER ==========
  return e('div', null,
    // Header
    e('div', { className: 'app-header' },
      e('h1', null, '🏀 JARVIS IA BASKET'),
      e('p', { className: 'app-subtitle' }, 
        'Sistema de Inteligência Artificial para Análise de Apostas Esportivas'
      ),
      e('div', { className: 'flex items-center justify-between mt-4', style: { maxWidth: '600px', margin: '1rem auto 0' } },
        e('div', { className: 'flex items-center gap-4' },
          e('span', { className: `pill ${status?.auto_bet ? 'pill-active' : 'pill-inactive'}` },
            status?.auto_bet ? '✓ Auto Bet ON' : '✗ Auto Bet OFF'
          ),
          e('span', { className: `pill ${autoRefresh ? 'pill-active' : 'pill-inactive'}` },
            autoRefresh ? '🔄 Auto Refresh' : '⏸ Paused'
          )
        ),
        e('button', { 
          className: 'btn btn-secondary',
          onClick: () => setAutoRefresh(!autoRefresh),
          style: { padding: '0.5rem 1rem', fontSize: '0.875rem' }
        }, autoRefresh ? 'Pausar' : 'Ativar')
      )
    ),

    // Main Dashboard Grid
    e('div', { className: 'dashboard-grid' },
      
      // Jarvis Briefing Card
      e(ModernCard, {
        title: 'Jarvis Briefing',
        icon: '🧠',
        badge: { type: 'info', text: 'IA' }
      },
        jarvisBriefing && jarvisBriefing.briefing
          ? e('div', { style: { whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: '1.6' } },
              jarvisBriefing.briefing
            )
          : e('div', { className: 'loading-spinner' })
      ),

      // Performance Stats Card
      e(ModernCard, {
        title: 'Performance',
        icon: '📊',
        badge: feedbackStats ? { 
          type: (feedbackStats.summary?.win_rate || 0) >= 0.6 ? 'success' : 'warning',
          text: `${((feedbackStats.summary?.win_rate || 0) * 100).toFixed(0)}%`
        } : null
      },
        feedbackStats && feedbackStats.summary
          ? e('div', null,
              e('div', { className: 'stats-grid' },
                e(StatItem, { value: feedbackStats.summary.total_bets || 0, label: 'Total Apostas', color: 'cyan' }),
                e(StatItem, { value: feedbackStats.summary.wins || 0, label: 'Ganhas', color: 'green' }),
                e(StatItem, { value: feedbackStats.summary.losses || 0, label: 'Perdidas', color: 'pink' }),
                e(StatItem, { value: `R$ ${(feedbackStats.summary.expected_profit || 0).toFixed(0)}`, label: 'Lucro EV', color: 'yellow' })
              ),
              performanceChartData && e('div', { style: { marginTop: '1.5rem', height: '200px' } },
                e(ChartComponent, { data: performanceChartData, type: 'doughnut' })
              )
            )
          : e('div', { className: 'loading-spinner' })
      ),

      // Acurácia por Tipo Card
      feedbackStats && feedbackStats.accuracy_by_points && e(ModernCard, {
        title: 'Acurácia por Tipo',
        icon: '🎯',
        badge: { type: 'info', text: 'Análise' }
      },
        accuracyChartData && e('div', { style: { height: '250px' } },
          e(ChartComponent, { data: accuracyChartData, type: 'bar' })
        )
      ),

      // Pattern Insights Card
      patternInsights && patternInsights.insights && e(ModernCard, {
        title: 'Padrões Descobertos',
        icon: '🔍',
        badge: { type: 'success', text: 'Insights' }
      },
        e('div', { className: 'stats-grid' },
          e(StatItem, {
            value: patternInsights.insights.best_hour_description || 'N/A',
            label: 'Melhor Hora',
            color: 'purple'
          }),
          e(StatItem, {
            value: `${patternInsights.insights.best_game_type || 'N/A'}pt`,
            label: 'Melhor Tipo',
            color: 'orange'
          }),
          e(StatItem, {
            value: `${((patternInsights.insights.success_rate || 0) * 100).toFixed(0)}%`,
            label: 'Taxa Sucesso',
            color: 'green'
          })
        ),
        patternInsights.insights.recommendation && e('div', {
          style: {
            marginTop: '1rem',
            padding: '1rem',
            background: 'rgba(0, 217, 255, 0.1)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(0, 217, 255, 0.3)',
            fontSize: '0.9rem'
          }
        }, patternInsights.insights.recommendation)
      ),

      // Weekly Summary Card
      weeklySummary && e(ModernCard, {
        title: 'Resumo Semanal',
        icon: '📈',
        badge: { type: 'warning', text: 'Semana' }
      },
        e('div', { style: { whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: '1.6' } },
          weeklySummary.summary_text || 'Carregando...'
        )
      ),

      // Ensemble Voting Card
      ensembleStats && e(ModernCard, {
        title: 'Ensemble Voting',
        icon: '🗳️',
        badge: { type: 'info', text: '3 Modelos' }
      },
        e('div', null,
          e('div', { className: 'stats-grid' },
            e(StatItem, {
              value: ensembleStats.summary?.strong_consensus || 0,
              label: 'Consenso Forte',
              color: 'green'
            }),
            e(StatItem, {
              value: ensembleStats.summary?.weak_consensus || 0,
              label: 'Consenso Fraco',
              color: 'yellow'
            }),
            e(StatItem, {
              value: `${((ensembleStats.summary?.avg_confidence || 0) * 100).toFixed(0)}%`,
              label: 'Confiança Média',
              color: 'cyan'
            })
          ),
          ensembleStats.summary?.avg_confidence && e('div', { style: { marginTop: '1rem' } },
            e(ProgressBar, { value: (ensembleStats.summary.avg_confidence * 100), max: 100, color: 'cyan' })
          )
        )
      ),

      // ========== NOVOS CARDS: SYSTEM HEALTH ==========

      // System Health Score Card
      systemHealth && e(ModernCard, {
        title: 'Saúde do Sistema',
        icon: systemHealth.overall_status === 'healthy' ? '💚' : systemHealth.overall_status === 'degraded' ? '💛' : '❤️',
        badge: {
          type: systemHealth.overall_status === 'healthy' ? 'success' : systemHealth.overall_status === 'degraded' ? 'warning' : 'danger',
          text: systemHealth.overall_status.toUpperCase()
        }
      },
        e('div', null,
          e('div', { style: { textAlign: 'center', marginBottom: '1.5rem' } },
            e('div', { 
              style: { 
                fontSize: '3rem', 
                fontWeight: 'bold',
                color: systemHealth.health_score >= 80 ? 'var(--neon-green)' : systemHealth.health_score >= 50 ? 'var(--neon-yellow)' : 'var(--neon-pink)'
              } 
            }, systemHealth.health_score),
            e('div', { style: { fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' } }, 'Health Score')
          ),
          e(ProgressBar, { 
            value: systemHealth.health_score, 
            max: 100, 
            color: systemHealth.health_score >= 80 ? 'green' : systemHealth.health_score >= 50 ? 'yellow' : 'pink' 
          }),
          e('div', { className: 'stats-grid', style: { marginTop: '1.5rem' } },
            e(StatItem, { value: systemHealth.errors?.total_errors || 0, label: 'Erros', color: 'pink' }),
            e(StatItem, { value: systemHealth.errors?.total_warnings || 0, label: 'Avisos', color: 'yellow' }),
            e(StatItem, { value: systemHealth.transmission?.total_desyncs || 0, label: 'Desyncs', color: 'orange' }),
            e(StatItem, { value: systemHealth.transmission?.total_delays || 0, label: 'Delays', color: 'purple' })
          )
        )
      ),

      // Live Bets & Transmission Card
      systemHealth && e(ModernCard, {
        title: 'Apostas & Transmissão',
        icon: '🎰',
        badge: { type: 'info', text: 'Live' }
      },
        e('div', null,
          // Apostas Stats
          e('div', { className: 'stats-grid', style: { marginBottom: '1.5rem' } },
            e(StatItem, { value: systemHealth.bets?.detected || 0, label: 'Detectadas', color: 'cyan' }),
            e(StatItem, { value: systemHealth.bets?.executed || 0, label: 'Executadas', color: 'green' }),
            e(StatItem, { value: systemHealth.bets?.blocked || 0, label: 'Bloqueadas', color: 'pink' }),
            e(StatItem, { value: systemHealth.bets?.expired || 0, label: 'Expiradas', color: 'orange' })
          ),
          
          // Apostas Recentes
          systemHealth.bets?.recent && systemHealth.bets.recent.length > 0 && e('div', null,
            e('div', { style: { fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'var(--neon-cyan)' } }, '🔴 Apostas Recentes'),
            e('div', { 
              style: { 
                maxHeight: '150px', 
                overflowY: 'auto',
                background: 'rgba(0, 0, 0, 0.2)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem'
              } 
            },
              systemHealth.bets.recent.slice(0, 5).map((bet, idx) => {
                const statusColors = {
                  'APOSTOU': 'var(--neon-green)',
                  'DETECTADO': 'var(--neon-cyan)',
                  'BLOQUEADO': 'var(--neon-pink)',
                  'EXPIROU': 'var(--neon-orange)'
                };
                const statusIcons = {
                  'APOSTOU': '✅',
                  'DETECTADO': '🔍',
                  'BLOQUEADO': '🚫',
                  'EXPIROU': '⏱️'
                };
                
                return e('div', { 
                  key: idx, 
                  style: { 
                    marginBottom: idx < 4 ? '0.5rem' : 0,
                    padding: '0.5rem',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: `3px solid ${statusColors[bet.status] || 'var(--text-muted)'}`
                  }
                },
                  e('div', { style: { display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' } },
                    e('span', { style: { color: statusColors[bet.status], fontWeight: 'bold' } }, 
                      `${statusIcons[bet.status]} ${bet.status}`
                    ),
                    e('span', { style: { color: 'var(--text-muted)' } }, 
                      new Date(bet.timestamp * 1000).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
                    )
                  ),
                  e('div', { style: { color: 'var(--text-secondary)', fontSize: '0.75rem' } },
                    `${bet.game || 'N/A'} • ${bet.type}pt ${bet.confidence ? `• ${(bet.confidence * 100).toFixed(0)}%` : ''}`
                  )
                );
              })
            )
          ),
          
          // Desyncs (se houver)
          systemHealth.transmission?.desyncs && systemHealth.transmission.desyncs.length > 0 && e('div', { style: { marginTop: '1rem' } },
            e('div', { 
              style: { 
                fontSize: '0.85rem', 
                fontWeight: 'bold', 
                marginBottom: '0.5rem', 
                color: 'var(--neon-orange)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              } 
            }, 
              e('span', null, '⚠️ Dessincronizações'),
              e('span', { 
                style: { 
                  fontSize: '0.7rem',
                  padding: '0.25rem 0.5rem',
                  background: 'rgba(255, 107, 53, 0.2)',
                  borderRadius: 'var(--radius-sm)'
                } 
              }, systemHealth.transmission.desyncs.length)
            ),
            e('div', {
              style: {
                maxHeight: '120px',
                overflowY: 'auto',
                background: 'rgba(255, 107, 53, 0.1)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                border: '1px solid rgba(255, 107, 53, 0.3)'
              }
            },
              systemHealth.transmission.desyncs.slice(0, 3).map((desync, idx) =>
                e('div', { 
                  key: idx,
                  style: { marginBottom: idx < 2 ? '0.5rem' : 0 }
                },
                  `T(${desync.transmission}) vs B(${desync.bet}) ${desync.diff} • ${desync.point_type}pt`
                )
              )
            )
          )
        )
      ),

      // System Errors Card
      systemHealth && systemHealth.errors?.recent && systemHealth.errors.recent.length > 0 && e(ModernCard, {
        title: 'Erros do Sistema',
        icon: '🚨',
        badge: { 
          type: 'danger', 
          text: `${systemHealth.errors.recent.length} Erros` 
        }
      },
        e('div', {
          style: {
            maxHeight: '300px',
            overflowY: 'auto'
          }
        },
          systemHealth.errors.recent.map((error, idx) => {
            const severityColors = {
              'critical': 'var(--neon-pink)',
              'warning': 'var(--neon-yellow)'
            };
            const severityIcons = {
              'critical': '🔴',
              'warning': '🟡'
            };
            
            return e('div', {
              key: idx,
              style: {
                marginBottom: '1rem',
                padding: '1rem',
                background: error.severity === 'critical' ? 'rgba(255, 51, 102, 0.1)' : 'rgba(255, 215, 0, 0.1)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${error.severity === 'critical' ? 'rgba(255, 51, 102, 0.3)' : 'rgba(255, 215, 0, 0.3)'}`,
                fontSize: '0.85rem'
              }
            },
              e('div', { style: { display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' } },
                e('span', { style: { color: severityColors[error.severity], fontWeight: 'bold' } },
                  `${severityIcons[error.severity]} ${error.type}`
                ),
                e('span', { style: { color: 'var(--text-muted)', fontSize: '0.75rem' } },
                  new Date(error.timestamp * 1000).toLocaleTimeString('pt-BR')
                )
              ),
              e('div', { style: { color: 'var(--text-secondary)', marginBottom: '0.25rem' } },
                error.message
              ),
              error.game && e('div', { style: { color: 'var(--text-muted)', fontSize: '0.75rem' } },
                `Jogo: ${error.game}`
              )
            );
          })
        )
      )
    ),

    // Gemini Insights Section
    e('div', { style: { marginTop: '2rem' } },
      e(ModernCard, {
        title: 'Gemini AI Insights',
        icon: '✨',
        badge: { type: 'danger', text: 'Gemini 2.0' }
      },
        e('div', { className: 'input-group' },
          e('label', { className: 'input-label' }, 'Pergunte ao Gemini sobre estratégias de aposta:'),
          e('textarea', {
            className: 'textarea',
            rows: 3,
            placeholder: 'Ex: Analise os padrões de vitória dos Lakers nas últimas 10 partidas e sugira uma estratégia de aposta',
            value: geminiInsight,
            readOnly: true
          })
        ),
        e('div', { className: 'flex gap-4', style: { marginTop: '1rem' } },
          e('button', {
            className: 'btn btn-primary',
            onClick: () => fetchQuickInsight('strategy'),
            disabled: geminiLoading
          }, geminiLoading ? 'Consultando...' : '🎯 Estratégia do Dia'),
          e('button', {
            className: 'btn btn-secondary',
            onClick: () => fetchQuickInsight('teams'),
            disabled: geminiLoading
          }, '🏀 Melhores Times'),
          e('button', {
            className: 'btn btn-secondary',
            onClick: () => fetchQuickInsight('patterns'),
            disabled: geminiLoading
          }, '📊 Padrões Temporais'),
          e('button', {
            className: 'btn btn-secondary',
            onClick: () => fetchQuickInsight('risk'),
            disabled: geminiLoading
          }, '⚠️ Análise de Risco')
        )
      )
    ),

    // Floating Action Button - Painel de Apostas
    e('button', {
      className: 'fab-bet-panel',
      onClick: () => window.location.href = '/bet-panel',
      title: 'Ir para Painel de Apostas'
    },
      '🎰',
      e('div', { className: 'fab-tooltip' }, 'Painel de Apostas')
    )
  );
}

// ========== RENDER APP ==========
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(App));
