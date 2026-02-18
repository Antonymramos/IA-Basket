const { useEffect, useState } = React;

const e = React.createElement;

function App() {
  const [status, setStatus] = useState(null);
  const [connectors, setConnectors] = useState({ transmission: [], bet: [] });
  const [logs, setLogs] = useState([]);
  const [voiceText, setVoiceText] = useState("");
  const [voiceResult, setVoiceResult] = useState("");
  const [selectedGame, setSelectedGame] = useState("");
  const [transmissionProvider, setTransmissionProvider] = useState("");
  const [betProvider, setBetProvider] = useState("");
  const [liveWsUrl, setLiveWsUrl] = useState("");
  const [betUrl, setBetUrl] = useState("");
  const [warning, setWarning] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState("");
  const [assistantStatus, setAssistantStatus] = useState("Aguardando inicializacao");
  const [assistantReady, setAssistantReady] = useState(false);
  const [gameScore, setGameScore] = useState(0);
  const [minGameScore, setMinGameScore] = useState(0);
  const [whitelistEnabled, setWhitelistEnabled] = useState(false);
  const [whitelistGames, setWhitelistGames] = useState([]);
  const [report, setReport] = useState(null);
  const [knowledgePrompt, setKnowledgePrompt] = useState("");
  const [knowledgeResponse, setKnowledgeResponse] = useState("");
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);

  const fetchStatus = async () => {
    const res = await fetch("/api/status");
    const data = await res.json();
    setStatus(data);
    setSelectedGame(data.selected_game || "");
    setTransmissionProvider(data.transmission_provider || "simulated_feed");
    setBetProvider(data.bet_provider || "bet_mock");
    setLiveWsUrl(data.config?.live_feed_ws_url || "");
    setBetUrl(data.config?.bet_url || "");
    setWhitelistEnabled(Boolean(data.whitelist_enabled));
    setWhitelistGames(data.whitelist_games || []);
    const scoreMap = data.game_scores || {};
    const currentScore = data.selected_game ? scoreMap[data.selected_game] : undefined;
    setGameScore(currentScore || 0);
    setMinGameScore(data.min_game_score || 0);
  };

  const fetchConnectors = async () => {
    const res = await fetch("/api/connectors");
    const data = await res.json();
    setConnectors(data);
  };

  const fetchLogs = async () => {
    const res = await fetch("/api/logs?limit=200");
    const data = await res.json();
    setLogs(data.items || []);
  };

  const fetchReport = async () => {
    const res = await fetch("/api/report");
    const data = await res.json();
    setReport(data);
  };

  useEffect(() => {
    fetchStatus();
    fetchConnectors();
    fetchLogs();
    fetchReport();
    loadVoices();
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
      fetchReport();
    }, 1500);
    return () => clearInterval(interval);
  }, []);


  const applySelectionPayload = async (payload) => {
    const response = await fetch("/api/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const data = await response.json();
      setWarning(data.detail || "Falha ao aplicar conectores.");
      return false;
    }
    setWarning("");
    fetchStatus();
    return true;
  };

  const updateSelection = async () => {
    await applySelectionPayload({
      selected_game: selectedGame,
      transmission_provider: transmissionProvider,
      bet_provider: betProvider,
      live_feed_ws_url: liveWsUrl,
      bet_url: betUrl,
      game_score: Number(gameScore) || 0,
      min_game_score: Number(minGameScore) || 0,
      whitelist_enabled: Boolean(whitelistEnabled),
    });
  };

  const addWhitelist = async () => {
    if (!selectedGame) return;
    await fetch("/api/whitelist/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game: selectedGame }),
    });
    fetchStatus();
  };

  const removeWhitelist = async (gameName) => {
    await fetch("/api/whitelist/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game: gameName }),
    });
    fetchStatus();
  };

  const toggleAutoBet = async (enabled) => {
    await fetch("/api/control/auto-bet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    fetchStatus();
    speak(enabled ? "Aposta automatica ligada" : "Aposta automatica desligada");
  };

  const controlBot = async (action) => {
    await fetch(`/api/control/${action}`, { method: "POST" });
    fetchStatus();
    speak(action === "start" ? "Bot iniciado" : "Bot parado");
  };

  const sendVoiceCommand = async (text) => {
    const res = await fetch("/api/voice/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    setVoiceResult(JSON.stringify(data.action || data, null, 2));
    if (data.action?.action === "set_auto_bet") {
      speak(data.action.enabled ? "Aposta automatica ligada" : "Aposta automatica desligada");
    } else if (data.action?.action === "start") {
      speak("Bot iniciado");
    } else if (data.action?.action === "stop") {
      speak("Bot parado");
    } else if (data.action?.action === "select_game") {
      speak(`Jogo selecionado: ${data.action.game}`);
    } else if (data.status === "noop") {
      speak("Comando nao reconhecido");
    }
    fetchStatus();
  };

  const speak = (text) => {
    if (!ttsEnabled || !text) return;
    if (!window.speechSynthesis) return;
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pt-BR";
    const voice = voices.find((item) => item.name === selectedVoice);
    if (voice) {
      utterance.voice = voice;
    }
    utterance.rate = 1.05;
    utterance.pitch = 1.1;
    window.speechSynthesis.speak(utterance);
  };

  const loadVoices = () => {
    if (!window.speechSynthesis) return;
    const available = window.speechSynthesis.getVoices();
    setVoices(available);
    if (!selectedVoice && available.length > 0) {
      const ptVoice = available.find((item) => item.lang && item.lang.startsWith("pt"));
      setSelectedVoice((ptVoice || available[0]).name);
    }
  };

  const testVoice = () => {
    speak("Teste de voz do Jarvis. Se estiver ouvindo, a voz esta ativa.");
  };

  const startAssistantFlow = () => {
    setAssistantReady(true);
    setAssistantStatus("Assistente ativo");
    speak("Ola. Sou o Jarvis do Hoops. Preencha os campos e clique em aplicar configuracao.");
  };

  const applyAssistantSettings = async () => {
    await updateSelection();
    speak("Configuracao aplicada. Escolha se deseja iniciar o monitoramento.");
  };

  const startMonitoring = async () => {
    await controlBot("start");
    speak("Monitoramento iniciado.");
  };

  const requestKnowledge = async () => {
    if (!knowledgePrompt) return;
    setKnowledgeLoading(true);
    setKnowledgeResponse("");
    const res = await fetch("/api/knowledge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: knowledgePrompt }),
    });
    const data = await res.json();
    if (res.ok) {
      setKnowledgeResponse(data.response || "Sem resposta");
      speak("Resposta do conhecimento gerada.");
    } else {
      setKnowledgeResponse(data.detail || "Falha ao consultar Gemini.");
    }
    setKnowledgeLoading(false);
  };

  const startVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Seu navegador nao suporta reconhecimento de voz.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "pt-BR";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setVoiceText(transcript);
      sendVoiceCommand(transcript);
    };
    recognition.start();
  };

  const running = status?.running;
  const autoBet = status?.auto_bet_enabled;
  const liveFeedInvalid =
    transmissionProvider === "live_ws" &&
    liveWsUrl &&
    !liveWsUrl.startsWith("ws://") &&
    !liveWsUrl.startsWith("wss://");

  return e(
    React.Fragment,
    null,
    e("div", { className: "scanline" }),
    e(
      "header",
      null,
      e(
        "div",
        null,
        e("h1", null, "Hoops Jarvis"),
        e("div", { className: "muted" }, "Painel neural de arbitragem"),
        e("div", { className: "hud-line" })
      ),
      e("div", { className: "status" },
        e("div", { className: `status-dot ${running ? "on" : ""}` }),
        e("div", { className: "badge" }, running ? "Rodando" : "Parado")
      )
    ),
    e(
      "div",
      { className: "container" },
      e(
        "div",
        { className: "assistant-banner" },
        e("div", null, `Assistente: ${assistantStatus}`),
        !assistantReady && e(
          "button",
          { className: "assistant-button", onClick: startAssistantFlow },
          "Iniciar assistente"
        )
      )
    ),
    e(
      "div",
      { className: "container" },
      e(
        "div",
        { className: "card" },
        e("h2", null, "Selecao de jogo"),
        e("div", { className: "field" },
          e("label", null, "Jogo atual"),
          e("input", {
            value: selectedGame,
            onChange: (ev) => setSelectedGame(ev.target.value),
            placeholder: "Ex: Lakers x Warriors",
          })
        ),
        e("button", { className: "primary", onClick: updateSelection }, "Salvar selecao")
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Score / Whitelist"),
        e("div", { className: "field" },
          e("label", null, "Score do jogo"),
          e("input", {
            value: gameScore,
            onChange: (ev) => setGameScore(ev.target.value),
            placeholder: "0-100",
          })
        ),
        e("div", { className: "field" },
          e("label", null, "Score minimo para operar"),
          e("input", {
            value: minGameScore,
            onChange: (ev) => setMinGameScore(ev.target.value),
            placeholder: "0",
          })
        ),
        e("div", { className: "field" },
          e("label", null, "Whitelist ativa"),
          e("button", {
            className: whitelistEnabled ? "secondary" : "primary",
            onClick: () => setWhitelistEnabled(!whitelistEnabled),
          }, whitelistEnabled ? "Desativar" : "Ativar")
        ),
        e("div", { className: "field" },
          e("label", null, "Whitelist jogos"),
          e("div", { className: "pill-row" },
            whitelistGames.length === 0
              ? e("div", { className: "muted" }, "Sem jogos")
              : whitelistGames.map((game) =>
                  e("button", {
                    key: game,
                    className: "pill",
                    onClick: () => removeWhitelist(game),
                  }, game)
                )
          )
        ),
        e("button", { className: "primary", onClick: addWhitelist }, "Adicionar jogo atual"),
        e("button", { className: "secondary", onClick: updateSelection, style: { marginTop: "8px" } }, "Salvar regras")
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Fonte / Bet"),
        e("div", { className: "field" },
          e("label", null, "Transmissao"),
          e(
            "select",
            {
              value: transmissionProvider,
              onChange: (ev) => setTransmissionProvider(ev.target.value),
            },
            connectors.transmission.map((item) =>
              e("option", { key: item.id, value: item.id }, item.label)
            )
          )
        ),
        e("div", { className: "field" },
          e("label", null, "Live WS URL"),
          e("input", {
            value: liveWsUrl,
            onChange: (ev) => setLiveWsUrl(ev.target.value),
            placeholder: "wss://feed.rapido.com",
          })
        ),
        liveFeedInvalid && e("div", { className: "muted", style: { color: "#ffb703" } },
          "Fonte live precisa ser WebSocket rapido (ws:// ou wss://)."
        ),
        e("div", { className: "field" },
          e("label", null, "Casa / Bet"),
          e(
            "select",
            {
              value: betProvider,
              onChange: (ev) => setBetProvider(ev.target.value),
            },
            connectors.bet.map((item) =>
              e("option", { key: item.id, value: item.id }, item.label)
            )
          )
        ),
        e("div", { className: "field" },
          e("label", null, "Bet URL"),
          e("input", {
            value: betUrl,
            onChange: (ev) => setBetUrl(ev.target.value),
            placeholder: "https://www.bet365...",
          })
        ),
        e("button", { className: "primary", onClick: updateSelection }, "Aplicar conectores"),
        warning && e("div", { className: "muted", style: { marginTop: "8px", color: "#ffb703" } }, warning)
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Controles"),
        e("div", { className: "field" },
          e("label", null, "Auto-bet"),
          e("button", {
            className: autoBet ? "secondary" : "primary",
            onClick: () => toggleAutoBet(!autoBet),
          }, autoBet ? "Desligar" : "Ligar")
        ),
        e("div", { className: "field" },
          e("label", null, "Voz - respostas"),
          e("button", {
            className: ttsEnabled ? "secondary" : "primary",
            onClick: () => setTtsEnabled(!ttsEnabled),
          }, ttsEnabled ? "Desativar voz" : "Ativar voz")
        ),
        e("div", { className: "field" },
          e("label", null, "Voz do Jarvis"),
          e(
            "select",
            {
              value: selectedVoice,
              onChange: (ev) => setSelectedVoice(ev.target.value),
            },
            voices.length === 0
              ? e("option", { value: "" }, "Sem vozes detectadas")
              : voices.map((voice) =>
                  e("option", { key: voice.name, value: voice.name }, `${voice.name} (${voice.lang})`)
                )
          )
        ),
        e("div", { className: "field" },
          e("label", null, "Teste de voz"),
          e("button", { className: "primary", onClick: testVoice }, "Falar agora")
        ),
        e("div", { className: "field" },
          e("label", null, "Execucao"),
          e("button", { className: "primary", onClick: () => controlBot("start") }, "Iniciar"),
          e("button", { className: "secondary", onClick: () => controlBot("stop"), style: { marginTop: "8px" } }, "Parar")
        ),
        e("div", { className: "field" },
          e("label", null, "Comando por voz"),
          e("button", { className: "primary", onClick: startVoice }, "Falar comando")
        ),
        e("div", { className: "field" },
          e("label", null, "Texto reconhecido"),
          e("textarea", {
            value: voiceText,
            onChange: (ev) => setVoiceText(ev.target.value),
            rows: 2,
          })
        ),
        e("button", { className: "secondary", onClick: () => sendVoiceCommand(voiceText) }, "Enviar comando")
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Assistente"),
        e("div", { className: "assistant-note" },
          "1) Preencha Selecao de jogo e Fonte/Bet. 2) Ajuste Score/Whitelist. 3) Clique Aplicar."
        ),
        e("button", { className: "primary", onClick: applyAssistantSettings }, "Aplicar configuracao"),
        e("button", { className: "secondary", onClick: startMonitoring, style: { marginTop: "8px" } }, "Iniciar monitoramento"),
        e("button", { className: "primary", onClick: testVoice, style: { marginTop: "8px" } }, "Falar agora")
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Logs / Sinais"),
        e(
          "div",
          { className: "signal-meter" },
          Array.from({ length: 10 }).map((_, idx) =>
            e("div", { key: idx, className: "signal-bar" })
          )
        ),
        e(
          "div",
          { className: "log-box" },
          logs.length === 0
            ? e("div", { className: "muted" }, "Sem eventos ainda")
            : logs.map((item, idx) =>
                e(
                  "div",
                  { key: idx, className: "log-item" },
                  e("div", null, `[${item.event}] ${item.timestamp || ""}`),
                  e("div", { className: "muted" }, JSON.stringify(item))
                )
              )
        ),
        e("div", { className: "field" },
          e("label", null, "Resultado voz"),
          e("textarea", {
            value: voiceResult,
            readOnly: true,
            rows: 3,
          })
        )
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Performance da sessao"),
        report
          ? e(
              "div",
              { className: "report-grid" },
              e("div", { className: "report-item" }, `Detectados: ${report.detected}`),
              e("div", { className: "report-item" }, `Apostados: ${report.bet}`),
              e("div", { className: "report-item" }, `Bloqueados: ${report.blocked}`),
              e("div", { className: "report-item" }, `Expirados: ${report.expired}`),
              e("div", { className: "report-item" }, `Erros: ${report.errors}`)
            )
          : e("div", { className: "muted" }, "Carregando...")
      ),
      e(
        "div",
        { className: "card" },
        e("h2", null, "Conhecimento"),
        e("div", { className: "field" },
          e("label", null, "Pergunte ao Jarvis"),
          e("textarea", {
            value: knowledgePrompt,
            onChange: (ev) => setKnowledgePrompt(ev.target.value),
            rows: 3,
            placeholder: "Ex: Qual estrategia melhorar para delay de 5s?",
          })
        ),
        e("button", { className: "primary", onClick: requestKnowledge }, knowledgeLoading ? "Consultando..." : "Consultar Gemini"),
        e("div", { className: "field" },
          e("label", null, "Resposta"),
          e("textarea", {
            value: knowledgeResponse,
            readOnly: true,
            rows: 6,
          })
        )
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(e(App));
