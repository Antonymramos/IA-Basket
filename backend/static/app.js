const { useEffect, useRef, useState } = React;

const e = React.createElement;

function App() {
  const [status, setStatus] = useState(null);
  const [report, setReport] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [txnBetStatus, setTxnBetStatus] = useState(null);
  const [ensembleStats, setEnsembleStats] = useState(null);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [jarvisBriefing, setJarvisBriefing] = useState(null);
  const [jarvisIntel, setJarvisIntel] = useState(null);
  const [jarvisBreakdown, setJarvisBreakdown] = useState(null);
  const [jarvisPatterns, setJarvisPatterns] = useState(null);
  const [jarvisWeeklySummary, setJarvisWeeklySummary] = useState(null);
  const [jarvisQuestion, setJarvisQuestion] = useState("");
  const [jarvisAnswer, setJarvisAnswer] = useState("");
  const [voiceText, setVoiceText] = useState("");
  const [voiceResult, setVoiceResult] = useState("");
  const [knowledgePrompt, setKnowledgePrompt] = useState("");
  const [knowledgeResponse, setKnowledgeResponse] = useState("");
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [premiumVoice, setPremiumVoice] = useState(true);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceNeedsGesture, setVoiceNeedsGesture] = useState(false);
  const [audioUnlocked, setAudioUnlocked] = useState(false);
  const [audioError, setAudioError] = useState("");

  const recognitionRef = useRef(null);
  const keepListeningRef = useRef(false);

  const fetchStatus = async () => {
    const res = await fetch("/api/status");
    const data = await res.json();
    setStatus(data);
  };

  const fetchReport = async () => {
    const res = await fetch("/api/report");
    const data = await res.json();
    setReport(data);
  };

  const fetchDiagnostics = async () => {
    const res = await fetch("/api/diagnostics?minutes=120&limit=12");
    const data = await res.json();
    setDiagnostics(data);
  };

  const fetchTxnBetStatus = async () => {
    try {
      const res = await fetch("/api/transmission-bet-status?minutes=60&limit=20");
      const data = await res.json();
      setTxnBetStatus(data);
    } catch (err) {
      console.error("Erro ao carregar status transmissão/bet:", err);
    }
  };

  const fetchEnsembleStats = async () => {
    try {
      const res = await fetch("/api/ensemble-stats?minutes=60&limit=30");
      const data = await res.json();
      setEnsembleStats(data);
    } catch (err) {
      console.error("Erro ao carregar ensemble stats:", err);
    }
  };

  const fetchFeedbackStats = async () => {
    try {
      const res = await fetch("/api/feedback-stats?minutes=120&limit=50");
      const data = await res.json();
      setFeedbackStats(data);
    } catch (err) {
      console.error("Erro ao carregar feedback stats:", err);
    }
  };

  const fetchJarvisBriefing = async () => {
    try {
      const res = await fetch("/api/jarvis/briefing?minutes=120");
      const data = await res.json();
      setJarvisBriefing(data);
    } catch (err) {
      console.error("Erro ao carregar briefing Jarvis:", err);
    }
  };

  const fetchJarvisIntelligence = async () => {
    try {
      const res = await fetch("/api/jarvis/intelligence?minutes=120");
      const data = await res.json();
      setJarvisIntel(data);
    } catch (err) {
      console.error("Erro ao carregar inteligência Jarvis:", err);
    }
  };

  const fetchJarvisBreakdown = async () => {
    try {
      const res = await fetch("/api/jarvis/decision-breakdown?team_a=Lakers&team_b=Celtics");
      const data = await res.json();
      setJarvisBreakdown(data);
    } catch (err) {
      console.error("Erro ao carregar decision breakdown:", err);
    }
  };

  const fetchJarvisPatterns = async () => {
    try {
      const res = await fetch("/api/jarvis/pattern-insights");
      const data = await res.json();
      setJarvisPatterns(data);
    } catch (err) {
      console.error("Erro ao carregar pattern insights:", err);
    }
  };

  const fetchJarvisWeeklySummary = async () => {
    try {
      const res = await fetch("/api/jarvis/weekly-summary");
      const data = await res.json();
      setJarvisWeeklySummary(data);
    } catch (err) {
      console.error("Erro ao carregar resumo semanal:", err);
    }
  };

  const askJarvis = async (question) => {
    try {
      const res = await fetch("/api/jarvis/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      setJarvisAnswer(data.answer);
    } catch (err) {
      console.error("Erro ao perguntar ao Jarvis:", err);
      setJarvisAnswer("Erro ao processar pergunta.");
    }
  };

  const refreshAll = async () => {
    await Promise.all([fetchStatus(), fetchReport(), fetchDiagnostics(), fetchTxnBetStatus(), fetchEnsembleStats(), fetchFeedbackStats(), fetchJarvisBriefing(), fetchJarvisIntelligence(), fetchJarvisBreakdown(), fetchJarvisPatterns(), fetchJarvisWeeklySummary()]);
  };

  useEffect(() => {
    refreshAll();
    const timer = setInterval(refreshAll, 2000);
    return () => clearInterval(timer);
  }, []);

  const unlockAudio = async () => {
    if (audioUnlocked) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      await ctx.resume();
      setAudioUnlocked(true);
      setAudioError("");
      setVoiceResult("Audio liberado.");
    } catch {
      setAudioUnlocked(false);
      setAudioError("Nao foi possivel liberar o audio. Tente clicar novamente.");
    }
  };

  useEffect(() => {
    const onClick = () => unlockAudio();
    window.addEventListener("click", onClick, { once: true });
    return () => window.removeEventListener("click", onClick);
  }, []);

  const speakPremium = async (text) => {
    if (!ttsEnabled || !text) return false;
    if (!audioUnlocked) {
      setVoiceResult("Clique em qualquer lugar para liberar o audio.");
      setAudioError("Audio bloqueado pelo navegador. Clique para liberar.");
      return false;
    }
    try {
      const res = await fetch("/api/voice/premium", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (data.status === "ok" && data.audio) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
        audio.volume = 1;
        await audio.play();
        return true;
      }
    } catch {
      return false;
    }
    return false;
  };

  const speak = async (text) => {
    if (!ttsEnabled || !text) return;
    if (premiumVoice) {
      const ok = await speakPremium(text);
      if (ok) return;
    }

    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pt-BR";
    utterance.rate = 0.95;
    utterance.pitch = 0.75;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
  };

  const testVoice = async () => {
    await speak("Teste de audio do Jarvis.");
  };

  const openErrorsPanel = async () => {
    window.location.hash = "#erros";
    await speak("Abrindo painel dos erros da bet.");
  };

  const openBetPanel = async () => {
    const betUrl = status?.config?.bet_url;
    if (betUrl) {
      window.open(betUrl, "_blank");
      await speak("Abrindo painel da bet.");
    } else {
      await speak("URL da bet nao configurada.");
    }
  };

  const requestKnowledge = async (customPrompt) => {
    const prompt = (customPrompt || knowledgePrompt || "").trim();
    if (!prompt) return;

    setKnowledgeLoading(true);
    if (!customPrompt) {
      setKnowledgeResponse("");
    }

    const res = await fetch("/api/knowledge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();

    if (res.ok) {
      const answer = data.response || "Sem resposta";
      setKnowledgeResponse(answer);
      const shortAnswer = answer.split("\n")[0].slice(0, 240);
      await speak(shortAnswer || "Consulta concluida.");
    } else {
      setKnowledgeResponse(data.detail || "Falha na consulta Gemini.");
    }

    setKnowledgeLoading(false);
  };

  const sendVoiceCommand = async (text) => {
    if (!text || !text.trim()) return;

    const lowered = text.toLowerCase();
    if (/abrir|abre|mostrar|exibir/.test(lowered) && /(painel|dashboard)/.test(lowered) && /(erro|erros|diagn[oó]stico)/.test(lowered)) {
      await openErrorsPanel();
      setVoiceResult("Painel de erros aberto.");
      return;
    }

    if (/painel/.test(lowered) && /(bet|aposta)/.test(lowered)) {
      await openBetPanel();
      setVoiceResult("Painel da bet aberto.");
      return;
    }

    if (/busca|pesquisa|analisar|estrat[eé]gia|nba/.test(lowered)) {
      await requestKnowledge(text);
      setVoiceResult("Consulta IA executada.");
      return;
    }

    const res = await fetch("/api/voice/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    setVoiceResult(JSON.stringify(data.action || data, null, 2));

    if (data.action?.action === "start") {
      await speak("Sistema iniciado.");
    } else if (data.action?.action === "stop") {
      await speak("Sistema pausado.");
    } else if (data.action?.action === "set_auto_bet") {
      await speak(data.action.enabled ? "Auto bet ativada." : "Auto bet desativada.");
    } else if (data.action?.action === "open_errors_panel") {
      await openErrorsPanel();
    } else if (data.action?.action === "knowledge_query" && data.knowledge_response) {
      setKnowledgeResponse(data.knowledge_response);
      await speak(data.knowledge_response.split("\n")[0].slice(0, 220));
    }

    await refreshAll();
  };

  const startVoice = (fromGesture = false) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    if (!recognitionRef.current) {
      const rec = new SpeechRecognition();
      rec.lang = "pt-BR";
      rec.interimResults = true;
      rec.continuous = true;
      rec.maxAlternatives = 1;

      rec.onstart = () => {
        setVoiceListening(true);
        setVoiceResult("Escuta ativa.");
      };

      rec.onerror = (event) => {
        setVoiceListening(false);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          setVoiceNeedsGesture(true);
          setVoiceResult("Clique para liberar microfone e ativar autoescuta.");
          return;
        }
        setVoiceResult(`Erro reconhecimento: ${event.error}`);
      };

      rec.onend = () => {
        setVoiceListening(false);
        if (keepListeningRef.current) {
          setTimeout(() => {
            try {
              rec.start();
            } catch {
              // noop
            }
          }, 250);
        }
      };

      rec.onresult = async (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const result = event.results[i];
          if (result.isFinal && result[0]?.transcript) {
            transcript += ` ${result[0].transcript}`;
          }
        }
        transcript = transcript.trim();
        if (!transcript) return;
        setVoiceText(transcript);
        await sendVoiceCommand(transcript);
      };

      recognitionRef.current = rec;
    }

    keepListeningRef.current = true;
    if (fromGesture) {
      setVoiceNeedsGesture(false);
    }

    try {
      recognitionRef.current.start();
    } catch {
      // already running
    }
  };

  const stopVoice = () => {
    keepListeningRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // noop
      }
    }
    setVoiceListening(false);
  };

  useEffect(() => {
    const t = setTimeout(() => startVoice(false), 1200);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (!voiceNeedsGesture) return undefined;
    const unlock = () => startVoice(true);
    window.addEventListener("click", unlock, { once: true });
    return () => window.removeEventListener("click", unlock);
  }, [voiceNeedsGesture]);

  const running = status?.running;
  const autoBet = status?.auto_bet_enabled;

  return e(
    React.Fragment,
    null,
    e("div", { className: "scanline" }),
    e(
      "header",
      null,
      e("div", null,
        e("h1", null, "Jarvis Core"),
        e("div", { className: "muted" }, "IA operacional minimal"),
        e("div", { className: "hud-line" })
      ),
      e("div", { className: "status" },
        e("div", { className: `status-dot ${running ? "on" : ""}` }),
        e("div", { className: "badge" }, running ? "Rodando" : "Parado"),
        e("button", { className: "primary", style: { width: "auto", marginLeft: "8px" }, onClick: openErrorsPanel }, "Erros"),
        e("button", { className: "primary", style: { width: "auto", marginLeft: "8px" }, onClick: openBetPanel }, "Bet" )
      )
    ),
    e(
      "div",
      { className: "ai-shell" },
      e("div", { className: "ai-core" },
        e("div", { className: "ai-ring" }),
        e("div", { className: "ai-ring ai-ring--inner" }),
        e("div", { className: "ai-pulse" }),
        e("button", {
          className: voiceListening ? "secondary" : "primary",
          onClick: () => (voiceListening ? stopVoice() : startVoice(true)),
        }, voiceListening ? "Pausar escuta" : "Ativar escuta" )
      ),
      e("div", { className: "core-status" },
        e("div", { className: `core-pill ${audioUnlocked ? "on" : "off"}` }, audioUnlocked ? "Audio liberado" : "Audio bloqueado"),
        e("div", { className: `core-pill ${voiceListening ? "on" : "off"}` }, voiceListening ? "Escuta ativa" : "Escuta pausada"),
        voiceNeedsGesture ? e("div", { className: "core-hint" }, "Clique para liberar o microfone.") : null,
        audioError ? e("div", { className: "core-hint warn" }, audioError) : null
      )
    ),
    e(
      "div",
      { className: "container minimal-mode" },
      e(
        "div",
        { className: "card" },
        e("h2", null, "IA Estratégica"),
        e("div", { className: "field" },
          e("label", null, "Objetivo"),
          e("textarea", {
            value: knowledgePrompt,
            onChange: (ev) => setKnowledgePrompt(ev.target.value),
            rows: 3,
            placeholder: "Ex: últimos jogos da NBA, padrão de vitórias/derrotas e estratégia com margem baixa",
          })
        ),
        e("button", { className: "primary", onClick: () => requestKnowledge() }, knowledgeLoading ? "Consultando..." : "Analisar com Gemini"),
        e("div", { className: "field" },
          e("label", null, "Resposta IA"),
          e("textarea", { value: knowledgeResponse, readOnly: true, rows: 7 })
        )
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Operação"),
        e("div", { className: "report-grid" },
          e("div", { className: "report-item" }, `Auto bet: ${autoBet ? "ON" : "OFF"}`),
          e("div", { className: "report-item" }, `Escuta: ${voiceListening ? "ON" : "OFF"}`),
          e("div", { className: "report-item" }, `Detectados: ${report?.detected || 0}`),
          e("div", { className: "report-item" }, `Erros: ${report?.errors || 0}`)
        ),
        e("div", { className: "field" },
          e("label", null, "Texto reconhecido"),
          e("textarea", { value: voiceText, onChange: (ev) => setVoiceText(ev.target.value), rows: 2 })
        ),
        e("button", { className: "secondary", onClick: () => sendVoiceCommand(voiceText) }, "Executar comando"),
        e("div", { className: "field" },
          e("label", null, "Resultado"),
          e("textarea", { value: voiceResult, readOnly: true, rows: 4 })
        ),
        e("div", { className: "field" },
          e("label", null, "Voz"),
          e("div", { className: "voice-row" },
            e("button", { className: premiumVoice ? "secondary" : "primary", onClick: () => setPremiumVoice(!premiumVoice) }, premiumVoice ? "Premium ON" : "Premium OFF"),
            e("button", { className: ttsEnabled ? "secondary" : "primary", onClick: () => setTtsEnabled(!ttsEnabled) }, ttsEnabled ? "Desativar fala" : "Ativar fala")
          ),
          e("div", { className: "voice-row" },
            e("button", { className: "primary", onClick: unlockAudio }, audioUnlocked ? "Audio liberado" : "Liberar audio"),
            e("button", { className: "secondary", onClick: testVoice }, "Testar voz")
          )
        )
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Transmissão vs Aposta"),
        txnBetStatus
          ? e(
              React.Fragment,
              null,
              e(
                "div",
                { className: "report-grid" },
                e("div", { className: "report-item" }, `DESYNC: ${txnBetStatus.desync?.count || 0}`),
                e("div", { className: "report-item" }, `Delay Médio: ${(txnBetStatus.delay?.avg_lag_seconds || 0).toFixed(2)}s`),
                e("div", { className: "report-item" }, `Delay Máximo: ${(txnBetStatus.delay?.max_lag_seconds || 0).toFixed(2)}s`),
                e("div", { className: "report-item" }, `Pendente: ${txnBetStatus.delay?.count_pending || 0}`)
              ),
              txnBetStatus.immediate_feedback && txnBetStatus.immediate_feedback.length > 0
                ? e(
                    "div",
                    { className: "log-box", style: { marginTop: "10px", maxHeight: "150px", overflowY: "auto", background: "#1a2332" } },
                    e("div", { className: "muted", style: { fontWeight: "bold" } }, "🔔 Feedback Imediato:"),
                    txnBetStatus.immediate_feedback.map((fb, idx) =>
                      e("div", { key: idx, className: "log-item", style: { fontSize: "0.9em" } },
                        e("div", { style: { whiteSpace: "pre-wrap" } }, fb.message),
                        fb.narration ? e("div", { className: "muted", style: { fontSize: "0.8em" } }, `🔊 "${fb.narration}"`) : null
                      )
                    )
                  )
                : null,
              e("div", { className: "log-box", style: { marginTop: "10px", maxHeight: "150px", overflowY: "auto" } },
                !(txnBetStatus.desync?.recent_events?.length)
                  ? e("div", { className: "muted" }, "Sem dessincronizações recentes.")
                  : txnBetStatus.desync.recent_events.map((evt, idx) =>
                      e("div", { key: idx, className: "log-item" },
                        e("div", null, `Desync: T(${evt.t_a}-${evt.t_b}) vs B(${evt.b_a}-${evt.b_b}) - ${evt.type}pt`),
                        e("div", { className: "muted" }, `Δ: +${evt.diff_a}/+${evt.diff_b} (${evt.source || 'unknown'})`)
                      )
                    )
              ),
              txnBetStatus.delay?.pending_events?.length > 0
                ? e(
                    "div",
                    { className: "log-box", style: { marginTop: "10px", maxHeight: "120px", overflowY: "auto", borderColor: "#ff9500" } },
                    e("div", { className: "muted warn" }, "⚠ Atrasos Pendentes:"),
                    txnBetStatus.delay.pending_events.map((evt, idx) =>
                      e("div", { key: idx, className: "log-item" },
                        e("div", null, `Idade: ${(evt.age_seconds || 0).toFixed(1)}s (limite: ${(evt.threshold || 0).toFixed(1)}s)`),
                        e("div", { className: "muted" }, `Meta: T(${evt.target_a}-${evt.target_b}) | Bet: (${evt.bet_a}-${evt.bet_b})`)
                      )
                    )
                  )
                : null
            )
          : e("div", { className: "muted" }, "Carregando..."),
        e(
          "div",
          { className: "report-grid", style: { marginTop: "10px", fontSize: "0.9em" } },
          e("div", { className: "report-item" }, `Detectados: ${txnBetStatus?.summary?.detections || 0}`),
          e("div", { className: "report-item" }, `Bloqueados: ${txnBetStatus?.summary?.blocked || 0}`),
          e("div", { className: "report-item" }, `Expirados: ${txnBetStatus?.summary?.expired || 0}`),
          e("div", { className: "report-item" }, `Apostados: ${txnBetStatus?.summary?.executed || 0}`)
        )
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "IA Ensemble Voting"),
        ensembleStats
          ? e(
              React.Fragment,
              null,
              e(
                "div",
                { className: "report-grid" },
                e("div", { className: "report-item" }, `Consenso Forte: ${ensembleStats.summary?.consensus_decisions || 0} (≥70%)`),
                e("div", { className: "report-item" }, `Consenso Fraco: ${ensembleStats.summary?.weak_decisions || 0} (<70%)`),
                e("div", { className: "report-item" }, `Força Média: ${((ensembleStats.summary?.avg_consensus_strength || 0) * 100).toFixed(1)}%`),
                e("div", { className: "report-item" }, `Total Decisões: ${ensembleStats.summary?.total_ensemble_decisions || 0}`)
              ),
              e(
                "div",
                { className: "report-grid", style: { marginTop: "8px", fontSize: "0.85em" } },
                e("div", { className: "report-item" }, `✓ Executar (Consenso): ${ensembleStats.action_breakdown?.consensus_execute || 0}`),
                e("div", { className: "report-item" }, `📋 Registrar (Consenso): ${ensembleStats.action_breakdown?.consensus_register || 0}`),
                e("div", { className: "report-item warn" }, `✓ Executar (Fraco): ${ensembleStats.action_breakdown?.weak_execute || 0}`),
                e("div", { className: "report-item warn" }, `📋 Registrar (Fraco): ${ensembleStats.action_breakdown?.weak_register || 0}`)
              ),
              ensembleStats.recent_decisions && ensembleStats.recent_decisions.length > 0
                ? e(
                    "div",
                    { className: "log-box", style: { marginTop: "10px", maxHeight: "120px", overflowY: "auto" } },
                    e("div", { className: "muted" }, "Últimas decisões:"),
                    ensembleStats.recent_decisions.map((d, idx) =>
                      e("div", { key: idx, className: "log-item" },
                        e("div", null, `[${d.type.includes("CONSENSUS") ? "✓ Forte" : "⚠ Fraco"}] ${d.action} - ${(d.consensus_strength * 100).toFixed(0)}%`),
                        e("div", { className: "muted" }, `${d.votes_for_action}/${d.votes_count} modelos votaram`)
                      )
                    )
                  )
                : null
            )
          : e("div", { className: "muted" }, "Carregando..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "📊 Accuracy Tracking (Feedback Loop)"),
        feedbackStats
          ? e(
              React.Fragment,
              null,
              feedbackStats.summary && Object.keys(feedbackStats.summary).length > 0
                ? e(
                    React.Fragment,
                    null,
                    e(
                      "div",
                      { className: "report-grid" },
                      e("div", { className: "report-item" }, `Taxa de Acerto: ${((feedbackStats.summary.win_rate || 0) * 100).toFixed(1)}%`),
                      e("div", { className: "report-item" }, `Total Apostas: ${feedbackStats.summary.total_bets || 0}`),
                      e("div", { className: "report-item" }, `Ganhos: ${feedbackStats.summary.wins || 0}`),
                      e("div", { className: "report-item" }, `Lucro Esperado: ${(feedbackStats.summary.expected_profit || 0).toFixed(2)}`)
                    ),
                    feedbackStats.accuracy_by_points && Object.keys(feedbackStats.accuracy_by_points).length > 0
                      ? e(
                          "div",
                          { className: "report-grid", style: { marginTop: "8px", fontSize: "0.85em" } },
                          Object.entries(feedbackStats.accuracy_by_points).map(([key, stats]) =>
                            e("div", { key, className: "report-item" },
                              `${key}: ${((stats.accuracy || 0) * 100).toFixed(1)}% (${stats.wins}/${stats.total})`
                            )
                          )
                        )
                      : null,
                    feedbackStats.accuracy_by_consensus && Object.keys(feedbackStats.accuracy_by_consensus).length > 0
                      ? e(
                          "div",
                          { className: "report-grid", style: { marginTop: "8px", fontSize: "0.85em" } },
                          Object.entries(feedbackStats.accuracy_by_consensus).map(([key, stats]) =>
                            e("div", { key, className: "report-item" },
                              `${key}: ${((stats.accuracy || 0) * 100).toFixed(1)}% (${stats.wins}/${stats.total})`
                            )
                          )
                        )
                      : null,
                    feedbackStats.success_examples && feedbackStats.success_examples.length > 0
                      ? e(
                          "div",
                          { className: "log-box", style: { marginTop: "10px", maxHeight: "100px", overflowY: "auto" } },
                          e("div", { className: "muted" }, "Exemplos de sucesso (Few-Shot):"),
                          feedbackStats.success_examples.map((ex, idx) =>
                            e("div", { key: idx, className: "log-item", style: { fontSize: "0.8em" } },
                              e("div", null, `✓ ${ex.tipo_pontuacao}pt, EV=${(ex.ev_score || 0).toFixed(2)}, Consenso=${((ex.consensus_strength || 0) * 100).toFixed(0)}%`),
                              e("div", { className: "muted" }, `Delay: ${(ex.delay_seconds || 0).toFixed(1)}s`)
                            )
                          )
                        )
                      : null
                  )
                : e("div", { className: "muted" }, "Sem dados de apostas ainda...")
            )
          : e("div", { className: "muted" }, "Carregando..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "🧠 Jarvis Briefing"),
        jarvisBriefing && jarvisBriefing.briefing
          ? e(
              "div",
              { className: "log-box", style: { maxHeight: "200px", overflowY: "auto", fontSize: "0.9em", whiteSpace: "pre-wrap" } },
              jarvisBriefing.briefing
            )
          : e("div", { className: "muted" }, "Carregando inteligência Jarvis..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "🎯 Análise de Decisão"),
        jarvisBreakdown && jarvisBreakdown.breakdown && jarvisBreakdown.breakdown.components
          ? e(
              "div",
              { className: "report-grid" },
              e("div", { className: "report-item", style: { fontWeight: "bold" } }, 
                `${jarvisBreakdown.breakdown.matchup} - Confiança: ${jarvisBreakdown.breakdown.final_confidence.percentage}%`
              ),
              jarvisBreakdown.breakdown.components.map((comp, idx) =>
                e("div", { key: idx, className: "report-item", style: { fontSize: "0.85em" } },
                  `${comp.emoji} ${comp.name}: ${(comp.impact).toFixed(2)} (${comp.description})`
                )
              )
            )
          : e("div", { className: "muted" }, "Carregando análise..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "📊 Padrões Descobertos"),
        jarvisPatterns && jarvisPatterns.insights
          ? e(
              "div",
              null,
              e("div", { className: "report-item" }, [
                e("div", null, "🕐 Melhor Hora: " + (jarvisPatterns.insights.best_hour_description || "Analisando...")),
                e("div", null, "🎯 Melhor Tipo: " + (jarvisPatterns.insights.best_game_type || "N/A")),
                e("div", null, "📈 Taxa de Sucesso: " + (((jarvisPatterns.insights.success_rate || 0) * 100).toFixed(1) + "%")),
              ]),
              jarvisPatterns.insights.recommendation
                ? e("div", { className: "log-box", style: { marginTop: "10px", fontSize: "0.9em" } }, jarvisPatterns.insights.recommendation)
                : null
            )
          : e("div", { className: "muted" }, "Carregando padrões..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "📈 Resumo Semanal"),
        jarvisWeeklySummary && jarvisWeeklySummary.summary_text
          ? e(
              "div",
              { className: "log-box", style: { maxHeight: "150px", overflowY: "auto", fontSize: "0.9em", whiteSpace: "pre-wrap" } },
              jarvisWeeklySummary.summary_text
            )
          : e("div", { className: "muted" }, "Carregando resumo..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "💬 Chat com Jarvis"),
        e(
          "div",
          null,
          e("input", {
            type: "text",
            placeholder: "Pergunta para Jarvis (ex: Por que bloqueou? Qual meu melhor horário?)",
            value: jarvisQuestion,
            onChange: (ev) => setJarvisQuestion(ev.target.value),
            onKeyPress: (ev) => {
              if (ev.key === "Enter") {
                askJarvis(jarvisQuestion);
                setJarvisQuestion("");
              }
            },
            style: { width: "80%", padding: "8px", marginRight: "10px" }
          }),
          e("button", {
            onClick: () => {
              askJarvis(jarvisQuestion);
              setJarvisQuestion("");
            },
            style: { padding: "8px 16px", cursor: "pointer" }
          }, "Enviar")
        ),
        jarvisAnswer
          ? e("div", { className: "log-box", style: { marginTop: "10px", fontSize: "0.9em", whiteSpace: "pre-wrap" } }, jarvisAnswer)
          : e("div", { className: "muted", style: { marginTop: "10px" } }, "Faça uma pergunta para Jarvis responder..."),
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Painel de Erros"),
        diagnostics
          ? e(
              "div",
              { className: "report-grid" },
              e("div", { className: "report-item" }, `Bloqueio: ${((diagnostics.risk_metrics?.blocked_rate_vs_detected || 0) * 100).toFixed(1)}%`),
              e("div", { className: "report-item" }, `Expiração: ${((diagnostics.risk_metrics?.expired_rate_vs_detected || 0) * 100).toFixed(1)}%`),
              e("div", { className: "report-item" }, `Erro: ${((diagnostics.risk_metrics?.error_rate_vs_detected || 0) * 100).toFixed(1)}%`),
              e("div", { className: "report-item" }, `Eventos: ${diagnostics.window_events || 0}`)
            )
          : e("div", { className: "muted" }, "Carregando..."),
        e(
          "div",
          { className: "log-box", style: { marginTop: "10px" } },
          !(diagnostics?.recent_errors?.length)
            ? e("div", { className: "muted" }, "Sem erros recentes.")
            : diagnostics.recent_errors.map((item, idx) =>
                e("div", { key: idx, className: "log-item" },
                  e("div", null, `[${item.event}] ${item.game || ""}`),
                  e("div", { className: "muted" }, item.message || "sem detalhe")
                )
              )
        )
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(e(App));
