# J.A.R.V.I.S - Configuração de Falas

Este arquivo documenta o sistema de falas contextuais do J.A.R.V.I.S e como expandi-lo.

## Estrutura Atual

Localização: `backend/static/app.js` → objeto `jarvisPhrases`

### Falas Implementadas

#### **Saudação Inicial** (automática ao abrir)
- Baseada no horário:
  - `5h-12h`: "Bom dia. J.A.R.V.I.S online e pronto para monitorar."
  - `12h-18h`: "Boa tarde. J.A.R.V.I.S online e pronto para monitorar."
  - `18h-5h`: "Boa noite. J.A.R.V.I.S online e pronto para monitorar."

#### **Controle do Bot**
- **Iniciar** (aleatório entre):
  - "Iniciando monitoramento de arbitragem."
  - "Sistema de apostas ativado."
  - "Análise em tempo real iniciada."

- **Parar** (aleatório entre):
  - "Monitoramento pausado."
  - "Sistema de apostas desativado."
  - "Análise interrompida."

#### **Aposta Automática**
- **Ligar** (aleatório entre):
  - "Aposta automática ativada."
  - "Modo automático ligado."

- **Desligar** (aleatório entre):
  - "Aposta automática desativada."
  - "Modo automático desligado."

#### **Outros**
- **Jogo Selecionado**: "Jogo selecionado: [nome]."
- **Comando Desconhecido** (aleatório entre):
  - "Comando não reconhecido."
  - "Não compreendi a instrução."

---

## Como Adicionar Novas Falas

### 1. Eventos Planejados (já preparados no código, comentados)

```javascript
// No objeto jarvisPhrases, adicionar:

login: [
  "Bem-vindo de volta.",
  "Autenticação confirmada.",
  "Acesso concedido. Sistema pronto."
],

logout: [
  "Sessão encerrada.",
  "Até logo.",
  "Desconectando."
],

error: [
  "Erro detectado no sistema.",
  "Falha na operação.",
  "Anomalia identificada."
],

alert: [
  "Atenção necessária.",
  "Alerta do sistema.",
  "Situação requer análise."
],

betPlaced: [
  "Aposta realizada.",
  "Ordem executada.",
  "Transação concluída."
],

betBlocked: [
  "Aposta bloqueada pela análise de risco.",
  "Operação cancelada por segurança.",
  "Bloqueio aplicado."
],

authRequired: [
  "Autenticação necessária para continuar.",
  "Login requerido na fonte de dados.",
  "Credenciais solicitadas."
],

watchdogRestart: [
  "Reiniciando sistema após inatividade.",
  "Sistema travado detectado. Reiniciando.",
  "Restaurando operação normal."
]
```

### 2. Como Usar no Código

**Para eventos definidos (arrays):**
```javascript
speakRandom(jarvisPhrases.login);
```

**Para eventos com parâmetros (funções):**
```javascript
speakRandom(jarvisPhrases.gameSelected("Lakers vs Warriors"));
```

### 3. Onde Adicionar Chamadas

- **Login/Logout**: no futuro módulo de autenticação
- **Erros**: nos blocos `catch` ou callbacks de erro
- **Apostas**: em `core/orquestrador.py` → emitir evento via SSE → frontend escuta e fala
- **Watchdog**: em `backend/bot_controller.py` → após restart

---

## Personalização Avançada

### Tom e Velocidade
Atualmente configurado em `app.js`:
```javascript
utterance.lang = "en-US";  // Idioma
utterance.rate = 0.92;     // Velocidade (0.1-10, padrão 1)
utterance.pitch = 0.72;    // Tom (0-2, padrão 1)
```

### Voz do Navegador
O sistema busca automaticamente:
1. Voz com "Jarvis" no nome
2. Voz masculina em inglês (David, Mark, Guy, etc.)
3. Qualquer voz em inglês
4. Primeira voz disponível

---

## Próximos Passos para IA Feed

Quando quiser treinar/refinar com IA:
1. Colete exemplos de contextos reais (logs, eventos, situações)
2. Use prompt com persona do Jarvis (MCU) para gerar variações
3. Teste as frases geradas e selecione as melhores
4. Adicione ao objeto `jarvisPhrases`

**Exemplo de prompt para IA:**
```
Você é J.A.R.V.I.S do MCU. Crie 5 variações curtas e diretas (estilo britânico formal)
para quando o sistema de apostas automatizadas:
- Detectar uma oportunidade de arbitragem
- Bloquear uma aposta por risco alto
- Completar uma sessão com lucro
```

---

**Última atualização:** 2026-02-19  
**Responsável:** Sistema J.A.R.V.I.S v1.0
