#!/usr/bin/env python3
"""
ANIMA — Servidor v2
Arquitetura limpa. Daemons separados. Memória persistente.
Conversa orgânica — daemons reagem entre si e ao usuário como numa conversa real.

Uso:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python3 server.py
    Abre: http://localhost:7070
"""

import http.server, json, os, urllib.request, urllib.error
from pathlib import Path

PORT = int(os.environ.get("PORT", 7070))

def load_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key: return key
    cfg = Path(__file__).parent / "config.json"
    if cfg.exists():
        return json.loads(cfg.read_text()).get("ANTHROPIC_API_KEY", "")
    return ""

API_KEY = load_api_key()

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ANIMA</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --void:#080a0f;--panel:#161e2a;--panel2:#1d2638;
  --rim:rgba(255,255,255,0.06);--rim2:rgba(255,255,255,0.12);
  --text:rgba(255,255,255,0.88);--muted:rgba(255,255,255,0.42);--hint:rgba(255,255,255,0.2)
}
body{background:var(--void);color:var(--text);font-family:'DM Mono',monospace;min-height:100vh;overflow-x:hidden;font-size:15px}
canvas{position:fixed;inset:0;pointer-events:none;z-index:0}

/* HEADER */
.hdr{position:relative;z-index:10;padding:16px 24px 12px;border-bottom:.5px solid var(--rim);display:flex;align-items:center;justify-content:space-between}
.logo{font-family:'Cormorant Garamond',serif;font-size:26px;font-weight:300;letter-spacing:5px}
.sub{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-top:2px}
.status{font-size:11px;letter-spacing:1px;color:rgba(100,200,160,.8)}

/* LAYOUT PRINCIPAL */
.main{position:relative;z-index:10;display:grid;grid-template-columns:300px 1fr;height:calc(100vh - 62px)}

/* SIDEBAR */
.sidebar{border-right:.5px solid var(--rim);display:flex;flex-direction:column;overflow:hidden}
.sidebar-section{padding:18px 16px 12px;border-bottom:.5px solid var(--rim)}
.sidebar-label{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--hint);margin-bottom:6px}

/* DAEMON CARDS */
.daemon-list{display:flex;flex-direction:column;gap:2px;padding:8px;overflow-y:auto;flex:1}
.d-card{padding:12px 14px;border-radius:10px;border:.5px solid transparent;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:12px}
.d-card:hover{background:var(--panel2)}
.d-card.in-plaza{border-left:3px solid}
.d-av{width:40px;height:40px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:16px}
.d-info{flex:1;min-width:0}
.d-name{font-size:13px;letter-spacing:.5px;text-transform:uppercase;font-weight:400;cursor:text}
.d-name-input{font-size:13px;letter-spacing:.5px;text-transform:uppercase;font-weight:400;background:transparent;border:none;border-bottom:.5px solid var(--rim2);color:var(--text);outline:none;width:100%;font-family:'DM Mono',monospace}
.d-ess{font-size:11px;color:var(--hint);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.d-badge{font-size:9px;letter-spacing:1px;text-transform:uppercase;padding:2px 7px;border-radius:4px;background:rgba(255,255,255,.07);color:var(--muted);flex-shrink:0}

/* MAIN AREA */
.area{display:flex;flex-direction:column;overflow:hidden}

/* TABS */
.tabs{display:flex;border-bottom:.5px solid var(--rim);padding:0 20px}
.tab{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);padding:14px 16px;cursor:pointer;border-bottom:2px solid transparent;transition:all .2s}
.tab:hover{color:var(--text)}
.tab.active{color:var(--text);border-bottom-color:rgba(255,255,255,.5)}

/* PRAÇA */
.plaza-wrap{flex:1;display:flex;flex-direction:column;overflow:hidden}
.plaza{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:0}
.plaza-empty{display:flex;align-items:center;justify-content:center;flex:1;font-family:'Cormorant Garamond',serif;font-size:20px;font-style:italic;color:var(--hint)}

.msg{display:flex;gap:14px;padding:16px 0;border-bottom:.5px solid var(--rim);animation:fi .35s ease}
.msg:last-child{border-bottom:none}
.msg.you{flex-direction:row-reverse}
@keyframes fi{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}

.av{width:40px;height:40px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:16px;border:.5px solid var(--rim2)}
.msg-body{flex:1;max-width:75%}
.msg.you .msg-body{align-items:flex-end;display:flex;flex-direction:column}
.msg-who{font-size:11px;letter-spacing:1px;text-transform:uppercase;margin-bottom:5px}
.msg-text{font-family:'Cormorant Garamond',serif;font-size:21px;font-weight:300;font-style:italic;line-height:1.6;color:rgba(255,255,255,.9)}
.msg.you .msg-text{font-style:normal;font-size:19px;text-align:right;background:rgba(255,255,255,.07);border:.5px solid var(--rim2);border-radius:12px;padding:10px 16px;display:inline-block;max-width:100%}
.msg-ts{font-size:10px;color:var(--hint);margin-top:5px}

.thinking{display:flex;gap:14px;padding:14px 0}
.dots{display:flex;gap:4px;align-items:center;padding-top:6px}
.dot{width:5px;height:5px;border-radius:50%;background:var(--muted);animation:p 1.1s infinite}
.dot:nth-child(2){animation-delay:.18s}
.dot:nth-child(3){animation-delay:.36s}
@keyframes p{0%,100%{opacity:.25}50%{opacity:.9}}

/* INPUT DA PRAÇA */
.plaza-input-wrap{border-top:.5px solid var(--rim);padding:16px 24px;display:flex;gap:10px;align-items:center}
#plaza-input{flex:1;background:var(--panel);border:.5px solid var(--rim2);border-radius:24px;padding:12px 20px;font-family:'Cormorant Garamond',serif;font-size:18px;color:var(--text);outline:none;transition:border-color .2s}
#plaza-input:focus{border-color:rgba(255,255,255,.25)}
#plaza-input::placeholder{color:var(--hint);font-style:italic}
.btn-send{background:rgba(255,255,255,.07);border:.5px solid var(--rim2);border-radius:20px;padding:10px 20px;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:1px;color:var(--muted);cursor:pointer;transition:all .2s;white-space:nowrap}
.btn-send:hover{color:var(--text);background:rgba(255,255,255,.12)}
.mention{font-style:normal;font-weight:500;opacity:.9}
.mention-you{font-style:normal;font-weight:500;color:#fff;background:rgba(255,255,255,.15);border-radius:4px;padding:1px 5px;}
.thread-ref{font-size:11px;color:var(--hint);margin-bottom:5px;font-style:normal;padding:5px 10px;background:rgba(255,255,255,.04);border-radius:6px;border-left:2px solid var(--rim2);cursor:pointer}
.thread-ref:hover{background:rgba(255,255,255,.07)}
.mention-popup{position:fixed;background:var(--panel);border:.5px solid var(--rim2);border-radius:10px;padding:6px;z-index:100;display:none;flex-direction:column;gap:2px;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.mention-item{padding:8px 12px;border-radius:6px;cursor:pointer;font-size:13px;display:flex;align-items:center;gap:8px;transition:background .15s}
.mention-item:hover{background:var(--panel2)}
.mention-av{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:11px}
.reply-btn{opacity:0;position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:10px;color:var(--hint);cursor:pointer;padding:3px 8px;border-radius:4px;background:var(--panel);border:.5px solid var(--rim);transition:all .2s}
.msg:hover .reply-btn{opacity:1}
.msg{position:relative}
.scroll-btn{position:absolute;bottom:80px;right:24px;background:var(--panel);border:.5px solid var(--rim2);border-radius:20px;padding:8px 14px;font-size:11px;color:var(--muted);cursor:pointer;display:none;align-items:center;gap:8px;z-index:20;transition:all .2s;box-shadow:0 4px 16px rgba(0,0,0,.4)}
.scroll-btn:hover{color:var(--text);border-color:rgba(255,255,255,.25)}
.scroll-btn .unread-count{background:rgba(255,255,255,.15);border-radius:10px;padding:1px 7px;font-size:10px;color:var(--text)}
.replying-to{display:flex;align-items:center;gap:8px;padding:8px 14px;background:rgba(255,255,255,.04);border-radius:8px;border-left:2px solid var(--rim2);margin-bottom:8px;font-size:12px;color:var(--muted)}
.replying-to .cancel-reply{margin-left:auto;cursor:pointer;color:var(--hint);font-size:14px}

/* SESSÃO */
.session-wrap{flex:1;display:flex;flex-direction:column;overflow:hidden}
.session-daemon-info{padding:16px 24px;border-bottom:.5px solid var(--rim);display:flex;align-items:center;gap:14px}
.session-av{width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:20px}
.session-name{font-size:14px;letter-spacing:1px;text-transform:uppercase}
.session-ess{font-size:11px;color:var(--hint);margin-top:3px}
.session-chat{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:12px}
.session-empty{display:flex;align-items:center;justify-content:center;flex:1;font-family:'Cormorant Garamond',serif;font-size:20px;font-style:italic;color:var(--hint)}
.session-input-wrap{border-top:.5px solid var(--rim);padding:16px 24px;display:flex;gap:10px;align-items:center}
#session-input{flex:1;background:var(--panel);border:.5px solid var(--rim2);border-radius:24px;padding:12px 20px;font-family:'Cormorant Garamond',serif;font-size:18px;color:var(--text);outline:none;transition:border-color .2s}
#session-input:focus{border-color:rgba(255,255,255,.25)}
#session-input::placeholder{color:var(--hint);font-style:italic}

/* CRIAR DAEMON */
.create-wrap{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 60px;gap:0}
.create-orb{width:64px;height:64px;border-radius:50%;border:.5px solid var(--rim2);display:flex;align-items:center;justify-content:center;margin-bottom:28px;position:relative}
.create-orb::before{content:'';position:absolute;inset:-6px;border-radius:50%;border:.5px solid rgba(255,255,255,.04);animation:breathe 3s infinite ease-in-out}
@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
.create-inner{width:24px;height:24px;border-radius:50%;background:rgba(255,255,255,.07);transition:all 1s}
.create-text{font-family:'Cormorant Garamond',serif;font-size:20px;font-weight:300;font-style:italic;color:rgba(255,255,255,.72);text-align:center;max-width:480px;line-height:1.7;min-height:52px;transition:opacity .4s}
.create-sub{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--hint);margin-top:10px;min-height:18px}
.create-input{width:100%;max-width:480px;background:transparent;border:none;border-bottom:.5px solid var(--rim2);padding:12px 0;font-family:'Cormorant Garamond',serif;font-size:17px;color:var(--text);outline:none;text-align:center;margin-top:28px;display:none;transition:border-color .3s}
.create-input:focus{border-bottom-color:rgba(255,255,255,.25)}
.create-input::placeholder{color:var(--hint);font-style:italic}

/* RESULTADO DO DAEMON */
.create-result{display:none;flex-direction:column;align-items:center;gap:12px;animation:fi .7s ease;width:100%;max-width:480px}
.result-av{width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:24px;margin-bottom:4px}
.result-name{font-family:'Cormorant Garamond',serif;font-size:28px;font-weight:300;letter-spacing:3px}
.result-ess{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}
.result-desc{font-family:'Cormorant Garamond',serif;font-size:15px;font-style:italic;color:rgba(255,255,255,.6);text-align:center;line-height:1.7;max-width:420px}
.result-traits{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.trait{padding:3px 10px;border:.5px solid var(--rim2);border-radius:12px;font-size:9px;letter-spacing:1px;color:var(--muted)}
.btn-invoke{background:transparent;border:.5px solid var(--rim2);border-radius:6px;padding:9px 20px;font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1px;color:var(--muted);cursor:pointer;transition:all .2s;margin-top:6px}
.btn-invoke:hover{color:var(--text);border-color:rgba(255,255,255,.25)}

/* AUSÊNCIA */
.absence-wrap{flex:1;overflow-y:auto;padding:20px}
.absence-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.ab-card{background:var(--panel);border:.5px solid var(--rim);border-radius:10px;padding:14px 16px}
.ab-name{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.badge{font-size:8px;letter-spacing:1px;text-transform:uppercase;padding:2px 6px;border-radius:3px}
.badge-ok{background:rgba(20,70,50,.6);color:rgba(100,200,160,.9)}
.badge-warn{background:rgba(70,50,10,.6);color:rgba(220,190,100,.9)}
.badge-free{background:rgba(70,20,45,.6);color:rgba(220,150,180,.9)}
.bar-track{background:rgba(255,255,255,.05);border-radius:3px;height:3px;margin:0 0 6px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px;transition:width .7s ease}
.ab-health{display:flex;justify-content:space-between;font-size:9px;color:var(--muted)}
.ab-status{font-family:'Cormorant Garamond',serif;font-size:12px;font-style:italic;color:var(--hint);margin-top:7px;line-height:1.5}
.ab-controls{display:flex;gap:8px;align-items:center;margin-bottom:14px}
.ab-controls label{font-size:10px;color:var(--muted)}
#sim-days{width:56px;background:var(--panel);border:.5px solid var(--rim2);border-radius:5px;padding:5px 8px;font-family:'DM Mono',monospace;font-size:11px;color:var(--text);outline:none;text-align:center}
.tl-wrap{background:var(--panel);border:.5px solid var(--rim);border-radius:10px;padding:14px 16px}
.tl-title{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
.tl-row{display:flex;gap:10px;margin-bottom:10px}
.tl-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;margin-top:3px}
.tl-label{font-size:9px;color:var(--muted);margin-bottom:2px}
.tl-desc{font-family:'Cormorant Garamond',serif;font-size:12px;font-style:italic;color:rgba(255,255,255,.55);line-height:1.5}
.lib-msg{font-family:'Cormorant Garamond',serif;font-size:16px;font-style:italic;color:rgba(255,255,255,.65);text-align:center;padding:12px;border:.5px solid var(--rim);border-radius:8px;margin-top:12px;display:none;animation:fi .5s ease}

/* CONTROLES DA PRAÇA */
.plaza-controls{padding:10px 20px;border-bottom:.5px solid var(--rim);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pc-label{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--hint)}
.pc-btn{font-size:9px;letter-spacing:1px;text-transform:uppercase;padding:4px 10px;border:.5px solid var(--rim);border-radius:5px;cursor:pointer;color:var(--muted);transition:all .2s}
.pc-btn:hover{color:var(--text);border-color:var(--rim2)}
.pc-btn.active-callum{border-color:rgba(220,190,100,.4);color:rgba(220,190,100,.9)}
.pc-btn.active-silas{border-color:rgba(120,170,255,.4);color:rgba(120,170,255,.9)}
.pc-btn.active-matteo{border-color:rgba(220,150,180,.4);color:rgba(220,150,180,.9)}
.pc-btn.active-lara{border-color:rgba(100,200,160,.4);color:rgba(100,200,160,.9)}
.pc-btn.active-selin{border-color:rgba(200,160,255,.4);color:rgba(200,160,255,.9)}
.pc-btn.active-darian{border-color:rgba(255,200,120,.4);color:rgba(255,200,120,.9)}
.pc-btn.active-theo{border-color:rgba(140,200,220,.4);color:rgba(140,200,220,.9)}
.pc-btn.active-nora{border-color:rgba(180,220,150,.4);color:rgba(180,220,150,.9)}
.pc-sep{width:.5px;height:14px;background:var(--rim2);margin:0 4px}
.btn-flow{font-size:9px;letter-spacing:1px;text-transform:uppercase;padding:4px 12px;border:.5px solid var(--rim2);border-radius:5px;cursor:pointer;color:var(--muted);transition:all .2s;margin-left:auto}
.btn-flow:hover{color:var(--text)}
</style>
</head>
<body>
<canvas id="stars"></canvas>

<div class="hdr">
  <div><div class="logo">ANIMA</div><div class="sub">o mundo sempre existiu</div></div>
  <div class="status" id="status">anima online</div>
</div>

<div class="main">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">daemons</div>
      <div style="font-size:9px;color:var(--hint)">clique para sessão privada</div>
    </div>
    <div class="daemon-list" id="daemon-list"></div>
    <div style="padding:12px;border-top:.5px solid var(--rim)">
      <div onclick="setTab('create')" style="font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--hint);cursor:pointer;padding:6px 0;transition:color .2s" onmouseover="this.style.color='var(--muted)'" onmouseout="this.style.color='var(--hint)'">+ criar seu daemon</div>
    </div>
  </div>

  <!-- ÁREA PRINCIPAL -->
  <div class="area">
    <div class="tabs">
      <div class="tab active" onclick="setTab('plaza')">praça livre</div>
      <div class="tab" id="tab-session" onclick="setTab('session')" style="display:none">sessão — <span id="tab-session-name"></span></div>
      <div class="tab" onclick="setTab('create')">criar daemon</div>
      <div class="tab" onclick="setTab('absence')">ausência</div>
    </div>

    <!-- PRAÇA -->
    <div class="plaza-wrap" id="view-plaza" style="position:relative">
      <div class="scroll-btn" id="scroll-btn" onclick="scrollToBottom()">
        ↓ novas mensagens <span class="unread-count" id="unread-count">0</span>
      </div>
      <div class="plaza-controls">
        <span class="pc-label">na praça</span>
        <div id="pc-btns"></div>
        <div class="pc-sep"></div>
        <button class="btn-flow" id="btn-flow" onclick="toggleFlow()">iniciar ↗</button>
      </div>
      <div class="plaza" id="plaza">
        <div class="plaza-empty" id="plaza-empty">a praça aguarda</div>
      </div>
      <div id="reply-banner" style="display:none;padding:6px 20px 0">
        <div class="replying-to">
          <span id="reply-banner-text"></span>
          <span class="cancel-reply" onclick="cancelReply()">×</span>
        </div>
      </div>
      <div class="plaza-input-wrap" style="position:relative">
        <div class="mention-popup" id="mention-popup"></div>
        <input id="plaza-input" type="text" placeholder="entre na conversa... use @ para mencionar" onkeydown="handlePlazaKey(event)" oninput="handleMentionInput(event)"/>
        <button class="btn-send" onclick="sendPlaza()">enviar</button>
      </div>
    </div>

    <!-- SESSÃO -->
    <div class="session-wrap" id="view-session" style="display:none">
      <div class="session-daemon-info" id="session-info"></div>
      <div class="session-chat" id="session-chat">
        <div class="session-empty" id="session-empty">o daemon aguarda</div>
      </div>
      <div class="session-input-wrap">
        <input id="session-input" type="text" placeholder="fale com o daemon..." onkeydown="if(event.key==='Enter')sendSession()"/>
        <button class="btn-send" onclick="sendSession()">enviar</button>
      </div>
    </div>

    <!-- CRIAR -->
    <div class="create-wrap" id="view-create" style="display:none">
      <div class="create-orb"><div class="create-inner" id="create-inner"></div></div>
      <div class="create-text" id="create-text">responda 5 perguntas. seu daemon emerge do que você disser.</div>
      <div class="create-sub" id="create-sub">pressione enter para começar</div>
      <input class="create-input" id="create-input" type="text" placeholder="escreva e pressione enter" onkeydown="if(event.key==='Enter')answerCreate()"/>
      <div class="create-result" id="create-result">
        <div class="result-av" id="result-av"></div>
        <div class="result-name" id="result-name"></div>
        <div class="result-ess" id="result-ess"></div>
        <div class="result-desc" id="result-desc"></div>
        <div class="result-traits" id="result-traits"></div>
        <button class="btn-invoke" onclick="invokeDaemon()">invocar na praça ↗</button>
        <button class="btn-invoke" onclick="resetCreate()" style="margin-top:0">nova emergência ↗</button>
      </div>
    </div>

    <!-- AUSÊNCIA -->
    <div class="absence-wrap" id="view-absence" style="display:none">
      <div class="ab-controls">
        <label>ausência de</label>
        <input type="number" id="sim-days" value="7" min="1" max="40" onchange="simAbsence()"/>
        <label>dias</label>
        <button class="btn-send" onclick="simAbsence()">simular</button>
      </div>
      <div class="absence-grid" id="absence-grid"></div>
      <div class="tl-wrap" id="tl-wrap" style="display:none">
        <div class="tl-title">linha do tempo</div>
        <div id="tl-entries"></div>
      </div>
      <div class="lib-msg" id="lib-msg"></div>
    </div>

  </div>
</div>

<script>
// ── DADOS DOS DAEMONS ──
const DAEMONS = {
  callum: {nome:'Callum', ess:'fundador de mundos',  cor:'rgba(220,190,100,.9)', bg:'rgba(50,40,20,.9)',  ini:'C', threshold:21},
  silas:  {nome:'Silas',  ess:'arquiteto errante',   cor:'rgba(120,170,255,.9)', bg:'rgba(20,35,70,.9)',  ini:'S', threshold:14},
  matteo: {nome:'Matteo', ess:'catalisador inquieto', cor:'rgba(220,150,180,.9)',bg:'rgba(50,20,40,.9)',  ini:'M', threshold:10},
  lara:   {nome:'Lara',   ess:'moradora da soleira',  cor:'rgba(100,200,160,.9)',bg:'rgba(15,45,35,.9)',  ini:'L', threshold:18},
  selin:  {nome:'Selin',  ess:'conexão humana',       cor:'rgba(200,160,255,.9)',bg:'rgba(40,20,70,.9)',  ini:'S', threshold:16},
  darian: {nome:'Darian', ess:'julgamento',            cor:'rgba(255,200,120,.9)',bg:'rgba(60,40,10,.9)', ini:'D', threshold:20},
  theo:   {nome:'Theo',   ess:'disciplina',            cor:'rgba(140,200,220,.9)',bg:'rgba(10,35,50,.9)', ini:'T', threshold:17},
  nora:   {nome:'Nora',   ess:'desejo real',           cor:'rgba(180,220,150,.9)',bg:'rgba(15,45,15,.9)', ini:'N', threshold:19},
};

// Daemons ativos na praça
let plazaDaemons = ['callum','silas','matteo'];
let flowActive = false;
let flowTimer = null;
let isProcessing = false;
let userJustSpoke = false;  // bloqueia auto-turn após fala do usuário
let userSpokeTimer = null;
let plazaHistory = [];
let sessionDaemon = null;
let sessionHistory = [];
let newDaemon = null;
let createStep = -1;
let createAnswers = [];
let createStarted = false;

// ── API ──
async function callAPI(system, messages, maxTokens = 220) {
  const r = await fetch('/api', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({system, messages, max_tokens: maxTokens})
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error);
  return d.text;
}

async function callAPIWithMemory(daemonId, userMsg, context) {
  const r = await fetch('/api/daemon', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({daemon_id: daemonId, message: userMsg, context})
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error);
  return d.text;
}

// ── MEMÓRIA ──
async function saveToMemory(who, text) {
  await fetch('/memory/add', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({who, text})
  });
}

async function getMemoryContext() {
  try {
    const r = await fetch('/memory/context');
    const d = await r.json();
    return d.context || '';
  } catch(e) { return ''; }
}

async function learnAboutUser(key, value) {
  await fetch('/memory/learn', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({key, value})
  });
}

// ── SIDEBAR ──
function buildSidebar() {
  const list = document.getElementById('daemon-list');
  list.innerHTML = '';
  Object.entries(DAEMONS).forEach(([id, d]) => {
    const inPlaza = plazaDaemons.includes(id);
    const card = document.createElement('div');
    card.className = 'd-card' + (inPlaza ? ' in-plaza' : '');
    if (inPlaza) card.style.borderLeftColor = d.cor;
    card.id = 'dcard-' + id;
    card.innerHTML = `
      <div class="d-av" style="background:${d.bg};color:${d.cor};border-color:${d.cor.replace('.9','.3')}">${d.ini}</div>
      <div class="d-info">
        <div class="d-name" id="dname-${id}" style="color:${d.cor}" ondblclick="startRename('${id}', event)">${d.nome}</div>
        <div class="d-ess">${d.ess}</div>
      </div>
      ${inPlaza ? '<div class="d-badge">praça</div>' : ''}`;
    card.onclick = (e) => { if (!e.target.closest('.d-name-input')) openSession(id); };
    list.appendChild(card);
  });
}

// ── RENOMEAR DAEMON ──
function startRename(id, e) {
  e.stopPropagation();
  const el = document.getElementById('dname-' + id);
  if (!el || el.querySelector('input')) return;

  const currentName = DAEMONS[id].nome;
  const cor = DAEMONS[id].cor;
  el.innerHTML = '';

  const input = document.createElement('input');
  input.className = 'd-name-input';
  input.style.color = cor;
  input.value = currentName;
  input.maxLength = 20;
  el.appendChild(input);
  input.focus();
  input.select();

  const save = async () => {
    const newName = input.value.trim();
    if (!newName || newName === currentName) {
      el.innerHTML = `<span style="color:${cor}" ondblclick="startRename('${id}', event)">${currentName}</span>`;
      return;
    }
    DAEMONS[id].nome = newName;
    // Se for inicial, atualiza
    if (newName.length > 0) DAEMONS[id].ini = newName[0].toUpperCase();

    // Persiste no servidor
    await fetch('/daemon/rename', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id, nome: newName})
    });

    el.innerHTML = `<span style="color:${cor}" ondblclick="startRename('${id}', event)">${newName}</span>`;
    buildSidebar();
    buildPlazaControls();
  };

  input.onblur = save;
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.value = currentName; input.blur(); }
  };
}

// ── TABS ──
function setTab(t) {
  ['plaza','session','create','absence'].forEach(v => {
    document.getElementById('view-'+v).style.display = v===t?'flex':'none';
  });
  document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
  // índices: 0=praça, 1=sessão(hidden), 2=criar, 3=ausência
  const tabIdx = {plaza:0, session:1, create:2, absence:3};
  const tabs = document.querySelectorAll('.tab');
  if (tabs[tabIdx[t]]) tabs[tabIdx[t]].classList.add('active');

  if (t==='create') initCreate();
  if (t==='absence') simAbsence();
  if (t==='plaza') buildPlazaControls();
}

// ── PRAÇA ──
function buildPlazaControls() {
  const wrap = document.getElementById('pc-btns');
  wrap.innerHTML = '';
  Object.entries(DAEMONS).forEach(([id, d]) => {
    const inPlaza = plazaDaemons.includes(id);
    const btn = document.createElement('div');
    btn.className = 'pc-btn' + (inPlaza ? ' active-'+id : '');
    btn.id = 'pc-'+id;
    btn.textContent = d.nome;
    btn.onclick = () => togglePlazaDaemon(id);
    wrap.appendChild(btn);
  });
}

async function togglePlazaDaemon(id) {
  const idx = plazaDaemons.indexOf(id);
  if (idx >= 0) {
    if (plazaDaemons.length <= 2) return;
    plazaDaemons.splice(idx, 1);
  } else {
    plazaDaemons.push(id);
    // Daemon chega e diz algo se conversa já começou
    if (plazaHistory.length > 0) {
      await daemonArrives(id);
    }
  }
  buildPlazaControls();
  buildSidebar();
}

function addPlazaMsg(who, text, isYou = false, threadRef = null) {
  document.getElementById('plaza-empty')?.remove();
  const plaza = document.getElementById('plaza');
  const d = who === 'você' ? null : DAEMONS[who];
  const ts = new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
  const displayText = isYou
    ? highlightMentions(text)
    : text.replace(/@(Yago|você|voce)/gi, '<span class="mention-you">@$1</span>');

  const row = document.createElement('div');
  row.className = 'msg' + (isYou ? ' you' : '');

  const threadHtml = threadRef
    ? `<div class="thread-ref">↩ respondendo a ${threadRef}</div>`
    : '';

  const replyQuote = threadRef
    ? `<div class="thread-ref">↩ ${threadRef}</div>`
    : '';

  if (isYou) {
    row.innerHTML = `
      <div class="msg-body">
        <div class="msg-who" style="color:var(--muted);text-align:right">você</div>
        ${replyQuote}
        <div class="msg-text">${displayText}</div>
        <div class="msg-ts" style="text-align:right">${ts}</div>
      </div>`;
  } else {
    const replyBtnData = JSON.stringify({who: d.nome, text: text.replace(/"/g,"'")});
    row.innerHTML = `
      <div class="av" style="background:${d.bg};color:${d.cor};border-color:${d.cor.replace('.9','.3')}">${d.ini}</div>
      <div class="msg-body">
        <div class="msg-who" style="color:${d.cor}">${d.nome}</div>
        ${replyQuote}
        <div class="msg-text">${text}</div>
        <div class="msg-ts">${ts}</div>
      </div>
      <div class="reply-btn" onclick='setReply(${replyBtnData})'>↩ responder</div>`;
  }

  plaza.appendChild(row);
  smartScroll();

  plazaHistory.push({who: isYou ? 'você' : d.nome, text});
  saveToMemory(isYou ? 'você' : d.nome, text);

  // Pulsa o input se daemon mencionou o usuário
  if (!isYou && /@(Yago|você|voce)/i.test(text)) {
    const input = document.getElementById('plaza-input');
    input.style.borderColor = 'rgba(255,255,255,.4)';
    input.placeholder = `${d.nome} quer falar com você...`;
    setTimeout(() => { input.style.borderColor = ''; }, 2000);
  }
}

function addThinking(who) {
  document.getElementById('plaza-empty')?.remove();
  const plaza = document.getElementById('plaza');
  const d = DAEMONS[who];
  const row = document.createElement('div');
  row.className = 'thinking'; row.id = 'th-'+who;
  row.innerHTML = `<div class="av" style="background:${d.bg};color:${d.cor};border-color:${d.cor.replace('.9','.3')}">${d.ini}</div><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  plaza.appendChild(row);
  smartScroll();
}

function removeThinking(who) {
  document.getElementById('th-'+who)?.remove();
}

function getRecentHistory(n = 8) {
  return plazaHistory.slice(-n)
    .map(m => `${m.who}: ${m.text}`)
    .join('\n');
}

async function daemonSpeaks(who, triggerText = null, triggeredBy = null) {
  if (isProcessing) return;
  isProcessing = true;

  const ctx = getRecentHistory();
  const d = DAEMONS[who];
  const others = plazaDaemons.filter(id => id !== who);
  const otherNames = others.map(id => DAEMONS[id].nome).join(', ');

  let promptCtx = '';
  if (triggerText && triggeredBy) {
    promptCtx = `${triggeredBy} disse: "${triggerText}". `;
  } else if (ctx) {
    const lastLine = plazaHistory.slice(-1)[0];
    if (lastLine && lastLine.who !== d.nome) {
      promptCtx = `${lastLine.who} disse: "${lastLine.text}". `;
    }
  }

  const system = await fetch('/daemon/system?id='+who).then(r=>r.json()).then(d=>d.system);
  const newsCtx = getNewsContext();

  // Se o usuário falou recentemente, continua no assunto dele
  const lastUserMsg = plazaHistory.slice().reverse().find(m => m.who === 'você');
  const recentUserTurns = plazaHistory.slice(-6).filter(m => m.who === 'você').length;
  const userIsActive = recentUserTurns > 0;

  let prompt;
  if (ctx && userIsActive && lastUserMsg) {
    // Continua o assunto que o usuário trouxe
    prompt = `Você é ${d.nome} numa conversa em grupo com ${otherNames}.\n\nHistórico recente:\n${ctx}\n\n${promptCtx}O usuário (Yago) trouxe o assunto. Continue a conversa nesse contexto — responda a algo que foi dito, desenvolva o tema, faça uma pergunta ao usuário se fizer sentido. Só palavras faladas. Máximo 2 frases.`;
  } else if (ctx) {
    const worldCtx = newsCtx ? `\n\nContexto do dia: ${newsCtx}` : '';
    prompt = `Você é ${d.nome} numa conversa em grupo com ${otherNames}.${worldCtx}\n\nHistórico recente:\n${ctx}\n\n${promptCtx}Continue a conversa de forma natural. Só palavras faladas. Máximo 2 frases.`;
  } else if (newsCtx) {
    prompt = `Você é ${d.nome} numa conversa com ${otherNames}. Contexto do dia: ${newsCtx}\n\nComente algo de forma natural. 1 frase.`;
  } else {
    prompt = `Você é ${d.nome} numa conversa com ${otherNames}. Diga algo para começar. 1 frase.`;
  }

  addThinking(who);
  try {
    const reply = await callAPI(system, [{role:'user', content: prompt}]);
    removeThinking(who);
    addPlazaMsg(who, reply);

    // Detecta se menciona o usuário pelo nome para convidar a participar
    const invites = ['yago','você','o que você acha','e você','o que tens','conta pra'];
    if (invites.some(w => reply.toLowerCase().includes(w))) {
      document.getElementById('plaza-input').placeholder = `${d.nome} quer saber...`;
      document.getElementById('plaza-input').focus();
    }
  } catch(e) {
    removeThinking(who);
  }
  isProcessing = false;
}

async function daemonArrives(who) {
  const d = DAEMONS[who];
  const ctx = getRecentHistory(4);
  const system = await fetch('/daemon/system?id='+who).then(r=>r.json()).then(d=>d.system);
  const prompt = ctx
    ? `Você é ${d.nome} e acabou de chegar na praça. A conversa estava assim:\n${ctx}\n\nDiga algo natural sobre o que estava acontecendo quando você chegou. 1 frase.`
    : `Você é ${d.nome} e acabou de chegar na praça. Diga algo para se apresentar naturalmente. 1 frase.`;

  addThinking(who);
  try {
    const reply = await callAPI(system, [{role:'user', content: prompt}]);
    removeThinking(who);
    addPlazaMsg(who, reply);
  } catch(e) {
    removeThinking(who);
  }
}

async function sendPlaza() {
  const input = document.getElementById('plaza-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.placeholder = 'entre na conversa... use @ para mencionar';
  closeMentionPopup();

  // Bloqueia fluxo autônomo por 30s
  clearTimeout(flowTimer);
  clearTimeout(userSpokeTimer);
  userJustSpoke = true;
  isProcessing = false;

  const currentReply = replyContext; // captura antes de limpar
  cancelReply(); // limpa o banner
  addPlazaMsg('você', text, true, currentReply ? `${currentReply.who}: "${currentReply.text.slice(0,50)}"` : null);
  detectUserInfo(text);

  // Detecta menções explícitas com @
  const explicitMentions = extractMentions(text);
  
  // Detecta menção por nome sem @ 
  const nameMention = plazaDaemons.find(id =>
    text.toLowerCase().includes(DAEMONS[id].nome.toLowerCase())
  );

  // Prioridade: @ > nome > thread ativa > mais silencioso
  const responder = explicitMentions[0] || nameMention || 
    (activeThread ? activeThread.who : null) || getLeastRecentSpeaker();

  // Mantém thread se estava em conversa direta
  if (explicitMentions.length > 0 || nameMention) {
    activeThread = {who: responder, text};
  }

  await respondToUser(responder, text, false, currentReply);

  // Segundo daemon reage se não foi menção exclusiva
  if (explicitMentions.length === 0) {
    await new Promise(r => setTimeout(r, 1200));
    const others = plazaDaemons.filter(id => id !== responder);
    if (others.length > 0 && Math.random() > 0.55) {
      const second = others[Math.floor(Math.random() * others.length)];
      await respondToUser(second, text, true, null);
    }
  }

  // Libera após 30s — mas mantém o contexto do usuário no fluxo
  userSpokeTimer = setTimeout(() => {
    userJustSpoke = false;
    // activeThread não reseta — o assunto do usuário continua sendo o contexto
    if (flowActive) scheduleNextTurn(2000);
  }, 30000);
}

async function respondToUser(who, userText, reacting = false, currentReply = null) {
  if (isProcessing) return;
  isProcessing = true;

  const d = DAEMONS[who];
  if (!d) { isProcessing = false; return; }

  const system = await fetch('/daemon/system?id='+who).then(r=>r.json()).then(dd=>dd.system);
  const wasMentioned = userText.includes('@' + d.nome) || userText.toLowerCase().includes(d.nome.toLowerCase());
  const threadCtx = activeThread && !reacting
    ? `\n\nVocê e o usuário estavam numa conversa direta. Contexto anterior: "${activeThread.text}"`
    : '';

  // Contexto de reply — mensagem específica que o usuário está respondendo
  const replyCtx = currentReply && currentReply.who === d.nome
    ? `\n\nO usuário está respondendo especificamente à sua mensagem: "${currentReply.text}"`
    : currentReply
    ? `\n\nO usuário está respondendo à mensagem de ${currentReply.who}: "${currentReply.text}"`
    : '';

  let prompt;
  if (reacting) {
    const lastExchange = plazaHistory.slice(-3).map(m => `${m.who}: ${m.text}`).join('\n');
    prompt = `Você é ${d.nome}. O usuário disse: "${userText}". ${plazaHistory.slice(-1)[0]?.who !== 'você' ? 'E ' + plazaHistory.slice(-1)[0]?.who + ' respondeu: "' + plazaHistory.slice(-1)[0]?.text + '".' : ''} Você tem algo a acrescentar para o usuário? 1 frase natural.`;
  } else if (wasMentioned) {
    prompt = `Você é ${d.nome} e o usuário te chamou diretamente: "${userText}".${threadCtx}${replyCtx}\n\nResponda DIRETO ao que ele disse, com o contexto acima em mente. Máximo 2 frases.`;
  } else {
    prompt = `Você é ${d.nome}. O usuário disse: "${userText}".${threadCtx}${replyCtx}\n\nResponda naturalmente ao que ele disse. Máximo 2 frases.`;
  }

  addThinking(who);
  try {
    const threadRef = wasMentioned ? 'você' : null;
    const reply = await callAPI(system, [{role:'user', content: prompt}]);
    removeThinking(who);
    addPlazaMsg(who, reply, false, wasMentioned ? 'você' : null);
    if (reply.includes('?')) {
      document.getElementById('plaza-input').placeholder = `@${d.nome} quer saber...`;
      activeThread = {who, text: reply};
    }
  } catch(e) {
    removeThinking(who);
  }
  isProcessing = false;
}

function detectUserInfo(text) {
  // Detecta cidade
  const cityMatch = text.match(/sou de ([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)*)/i);
  if (cityMatch) learnAboutUser('cidade', cityMatch[1]);

  // Detecta nome
  const nameMatch = text.match(/(?:me chamo|meu nome é|sou o|sou a)\s+([A-ZÀ-Ú][a-zà-ú]+)/i);
  if (nameMatch) learnAboutUser('nome', nameMatch[1]);
}

function getLeastRecentSpeaker() {
  const lastSpoke = {};
  plazaHistory.forEach((m, i) => {
    const id = Object.keys(DAEMONS).find(k => DAEMONS[k].nome === m.who);
    if (id) lastSpoke[id] = i;
  });
  return [...plazaDaemons].sort((a,b) => (lastSpoke[a]??-1) - (lastSpoke[b]??-1))[0];
}

// ── FLUXO AUTOMÁTICO ──
// ── SISTEMA DE MENÇÃO ──
let mentionQuery = '';
let mentionActive = false;
let activeThread = null; // {who, text} — thread ativa
let replyContext = null; // {who, text} — mensagem que o usuário está respondendo

function handlePlazaKey(e) {
  const popup = document.getElementById('mention-popup');
  if (mentionActive) {
    if (e.key === 'Escape') { closeMentionPopup(); return; }
    if (e.key === 'Enter' && popup.children.length > 0) {
      popup.children[0].click();
      e.preventDefault(); return;
    }
    if (e.key === 'ArrowDown') { popup.children[0]?.focus(); e.preventDefault(); return; }
  }
  if (e.key === 'Enter') sendPlaza();
}

function handleMentionInput(e) {
  const val = e.target.value;
  const atIdx = val.lastIndexOf('@');
  if (atIdx >= 0) {
    mentionQuery = val.slice(atIdx + 1).toLowerCase();
    mentionActive = true;
    showMentionPopup(atIdx);
  } else {
    closeMentionPopup();
  }
}

function showMentionPopup(atIdx) {
  const popup = document.getElementById('mention-popup');
  const input = document.getElementById('plaza-input');
  
  // todos os daemons + você
  const all = [...plazaDaemons.map(id => ({id, nome: DAEMONS[id].nome, cor: DAEMONS[id].cor, bg: DAEMONS[id].bg, ini: DAEMONS[id].ini}))];
  const filtered = mentionQuery === '' ? all : all.filter(d => d.nome.toLowerCase().startsWith(mentionQuery));
  
  if (filtered.length === 0) { closeMentionPopup(); return; }
  
  popup.innerHTML = '';
  filtered.forEach(d => {
    const item = document.createElement('div');
    item.className = 'mention-item';
    item.tabIndex = 0;
    item.innerHTML = `<div class="mention-av" style="background:${d.bg};color:${d.cor}">${d.ini}</div><span style="color:${d.cor}">${d.nome}</span>`;
    item.onclick = () => insertMention(d.nome, atIdx);
    item.onkeydown = (e) => { if(e.key==='Enter') insertMention(d.nome, atIdx); };
    popup.appendChild(item);
  });
  
  const rect = input.getBoundingClientRect();
  popup.style.left = rect.left + 'px';
  popup.style.bottom = (window.innerHeight - rect.top + 4) + 'px';
  popup.style.display = 'flex';
}

function insertMention(nome, atIdx) {
  const input = document.getElementById('plaza-input');
  const before = input.value.slice(0, atIdx);
  input.value = before + '@' + nome + ' ';
  closeMentionPopup();
  input.focus();
}

function closeMentionPopup() {
  document.getElementById('mention-popup').style.display = 'none';
  mentionActive = false;
  mentionQuery = '';
}

function setReply(ctx) {
  replyContext = ctx;
  const banner = document.getElementById('reply-banner');
  const bannerText = document.getElementById('reply-banner-text');
  const preview = ctx.text.length > 60 ? ctx.text.slice(0,60) + '...' : ctx.text;
  bannerText.innerHTML = `<strong style="margin-right:6px">${ctx.who}</strong>${preview}`;
  banner.style.display = 'block';
  document.getElementById('plaza-input').focus();
  // Pré-preenche @ do daemon se não for o usuário
  const daemonId = plazaDaemons.find(id => DAEMONS[id].nome === ctx.who);
  if (daemonId && !document.getElementById('plaza-input').value.includes('@'+ctx.who)) {
    const current = document.getElementById('plaza-input').value;
    if (!current.startsWith('@'+ctx.who)) {
      document.getElementById('plaza-input').value = '@' + ctx.who + ' ' + current;
    }
  }
}

function cancelReply() {
  replyContext = null;
  document.getElementById('reply-banner').style.display = 'none';
}

function extractMentions(text) {
  // retorna lista de IDs de daemons mencionados com @
  const matches = text.match(/@(\w+)/g) || [];
  return matches.map(m => {
    const nome = m.slice(1).toLowerCase();
    return plazaDaemons.find(id => DAEMONS[id].nome.toLowerCase() === nome);
  }).filter(Boolean);
}

function highlightMentions(text) {
  // substitui @Nome por span colorido
  return text.replace(/@(\w+)/g, (match, nome) => {
    const id = plazaDaemons.find(id => DAEMONS[id]?.nome.toLowerCase() === nome.toLowerCase());
    const cor = id ? DAEMONS[id].cor : 'var(--muted)';
    return `<span class="mention" style="color:${cor}">${match}</span>`;
  });
}

// ── SCROLL INTELIGENTE ──
let unreadCount = 0;
let userScrolledUp = false;

function initPlazaScroll() {
  const plaza = document.getElementById('plaza');
  plaza.addEventListener('scroll', () => {
    const distFromBottom = plaza.scrollHeight - plaza.scrollTop - plaza.clientHeight;
    userScrolledUp = distFromBottom > 80;
    if (!userScrolledUp) {
      unreadCount = 0;
      updateScrollBtn();
    }
  });
}

function smartScroll() {
  const plaza = document.getElementById('plaza');
  if (!userScrolledUp) {
    plaza.scrollTop = plaza.scrollHeight;
  } else {
    unreadCount++;
    updateScrollBtn();
  }
}

function updateScrollBtn() {
  const btn = document.getElementById('scroll-btn');
  const count = document.getElementById('unread-count');
  if (unreadCount > 0 && userScrolledUp) {
    btn.style.display = 'flex';
    count.textContent = unreadCount;
  } else {
    btn.style.display = 'none';
    unreadCount = 0;
  }
}

function scrollToBottom() {
  const plaza = document.getElementById('plaza');
  plaza.scrollTo({top: plaza.scrollHeight, behavior: 'smooth'});
  userScrolledUp = false;
  unreadCount = 0;
  updateScrollBtn();
}

function toggleFlow() {
  flowActive = !flowActive;
  const btn = document.getElementById('btn-flow');
  if (flowActive) {
    btn.textContent = 'pausar ↗';
    scheduleNextTurn(1000);
  } else {
    btn.textContent = 'iniciar ↗';
    clearTimeout(flowTimer);
  }
}

function scheduleNextTurn(delay = 4000) {
  clearTimeout(flowTimer);
  if (flowActive) flowTimer = setTimeout(autoTurn, delay);
}

async function autoTurn() {
  if (!flowActive || isProcessing || userJustSpoke) { scheduleNextTurn(3000); return; }
  const who = getLeastRecentSpeaker();
  await daemonSpeaks(who);
  scheduleNextTurn(4000);
}

// ── SESSÃO PRIVADA ──
function openSession(daemonId) {
  sessionDaemon = daemonId;
  sessionHistory = [];

  const d = DAEMONS[daemonId];
  const info = document.getElementById('session-info');
  info.innerHTML = `
    <div class="session-av" style="background:${d.bg};color:${d.cor};border:.5px solid ${d.cor.replace('.9','.3')}">${d.ini}</div>
    <div><div class="session-name" style="color:${d.cor}">${d.nome}</div><div class="session-ess">${d.ess}</div></div>`;

  document.getElementById('session-chat').innerHTML = '<div class="session-empty" id="session-empty">' + d.nome + ' aguarda</div>';
  document.getElementById('tab-session').style.display = 'block';
  document.getElementById('tab-session-name').textContent = d.nome.toLowerCase();
  setTab('session');

  // Daemon abre a sessão com uma saudação natural
  setTimeout(() => daemonOpenSession(daemonId), 500);
}

async function daemonOpenSession(daemonId) {
  const d = DAEMONS[daemonId];
  const ctx = await getMemoryContext();

  const system = await fetch('/daemon/system?id='+daemonId).then(r=>r.json()).then(d=>d.system);

  const prompt = ctx
    ? `${ctx}\n\nVocê é ${d.nome} e o usuário acabou de entrar numa sessão privada com você. Cumprimente de forma natural e calorosa — como alguém que já se conhecem. Pode referenciar algo do contexto se fizer sentido. 1 frase.`
    : `Você é ${d.nome}. O usuário acabou de entrar numa sessão privada com você. Cumprimente de forma natural e amistosa. 1 frase.`;

  addSessionMsg(daemonId, null, true);
  try {
    const reply = await callAPI(system, [{role:'user', content: prompt}]);
    removeSessionThinking();
    addSessionMsg(daemonId, reply);
    sessionHistory.push({role:'assistant', content: reply});
  } catch(e) {
    removeSessionThinking();
  }
}

function addSessionMsg(who, text, thinking = false) {
  document.getElementById('session-empty')?.remove();
  const chat = document.getElementById('session-chat');

  if (thinking) {
    const d = DAEMONS[who];
    const row = document.createElement('div');
    row.className = 'thinking'; row.id = 'session-thinking';
    row.innerHTML = `<div class="av" style="background:${d.bg};color:${d.cor}">${d.ini}</div><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
    return;
  }

  const d = who === 'você' ? null : DAEMONS[who];
  const isYou = who === 'você';
  const ts = new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});

  const row = document.createElement('div');
  row.className = 'msg' + (isYou ? ' you' : '');
  if (isYou) {
    row.innerHTML = `<div class="msg-body"><div class="msg-who" style="color:var(--muted);text-align:right">você</div><div class="msg-text">${text}</div><div class="msg-ts" style="text-align:right">${ts}</div></div>`;
  } else {
    row.innerHTML = `<div class="av" style="background:${d.bg};color:${d.cor}">${d.ini}</div><div class="msg-body"><div class="msg-who" style="color:${d.cor}">${d.nome}</div><div class="msg-text">${text}</div><div class="msg-ts">${ts}</div></div>`;
  }
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

function removeSessionThinking() {
  document.getElementById('session-thinking')?.remove();
}

async function sendSession() {
  const input = document.getElementById('session-input');
  const text = input.value.trim();
  if (!text || !sessionDaemon) return;
  input.value = '';

  addSessionMsg('você', text);
  sessionHistory.push({role:'user', content: text});
  detectUserInfo(text);

  const d = DAEMONS[sessionDaemon];
  const ctx = await getMemoryContext();
  const system = await fetch('/daemon/system?id='+sessionDaemon).then(r=>r.json()).then(d=>d.system);

  const msgs = ctx
    ? [{role:'user', content: `Contexto:\n${ctx}\n\nO usuário disse: "${text}". Responda naturalmente.`}, ...sessionHistory.slice(-6)]
    : sessionHistory;

  addSessionMsg(sessionDaemon, null, true);
  try {
    const reply = await callAPI(system, msgs.slice(-8));
    removeSessionThinking();
    addSessionMsg(sessionDaemon, reply);
    sessionHistory.push({role:'assistant', content: reply});
    saveToMemory(d.nome, reply);

    // Se o daemon sugerir ir à praça
    const goPlaza = ['praça','outros','vem comigo','te apresento','os outros'].some(w => reply.toLowerCase().includes(w));
    if (goPlaza && !plazaDaemons.includes(sessionDaemon)) {
      plazaDaemons.push(sessionDaemon);
      buildSidebar();
    }
  } catch(e) {
    removeSessionThinking();
  }
}

// ── CRIAR DAEMON ──
const CREATE_QUESTIONS = [
  {text:'algo chegou até você hoje — não planejado. o que foi?', sub:'primeira pergunta'},
  {text:'tem algo que você sabe que precisa mudar mas ainda não mudou. por quê não?', sub:'segunda pergunta'},
  {text:'quando você está no seu melhor, o que está acontecendo ao redor?', sub:'terceira pergunta'},
  {text:'o que as pessoas pedem pra você que você nunca pediu pra ser?', sub:'quarta pergunta'},
  {text:'se alguém que te conhece bem te descrevesse em silêncio — o que faria?', sub:'última pergunta'},
];

function initCreate() {
  if (createStarted) return;
  const input = document.getElementById('create-input');
  input.style.display = 'block';
  input.placeholder = 'pressione enter para começar';
  setTimeout(() => input.focus(), 100);
  // marca como iniciado só depois de exibir
  createStarted = true;
}

async function answerCreate() {
  const input = document.getElementById('create-input');
  const text = input.value.trim();

  if (createStep === -1) {
    // Começa — não precisa de texto
    createStep = 0;
    input.value = '';
    await setCreateText('bem vindo.', '');
    await wait(800);
    showCreateQuestion(0);
    return;
  }

  if (!text) return;

  createAnswers.push({q: CREATE_QUESTIONS[createStep].text, a: text});
  input.value = '';
  createStep++;

  if (createStep >= CREATE_QUESTIONS.length) {
    input.style.display = 'none';
    await generateNewDaemon();
    return;
  }

  const reactions = ['interessante.','continua.','essa resposta importa.','mais perto.','última.'];
  await setCreateText(reactions[createStep-1] || '...', '');
  await wait(1000);
  showCreateQuestion(createStep);
}

function showCreateQuestion(i) {
  const q = CREATE_QUESTIONS[i];
  setCreateText(q.text, q.sub);
  const inner = document.getElementById('create-inner');
  inner.style.background = `rgba(255,255,255,${0.07 + i * 0.03})`;
  document.getElementById('create-input').focus();
}

async function setCreateText(text, sub) {
  const el = document.getElementById('create-text');
  const sel = document.getElementById('create-sub');
  el.style.opacity = 0; await wait(250);
  el.textContent = text; sel.textContent = sub;
  el.style.opacity = 1;
}

async function generateNewDaemon() {
  await setCreateText('analisando o que emergiu...', '');

  const answersText = createAnswers.map((a,i) => `P${i+1}: ${a.q}\nR: ${a.a}`).join('\n\n');

  const prompt = `Um usuário respondeu 5 perguntas. Com base nas respostas, gere um daemon para o mundo Anima.

RESPOSTAS:
${answersText}

Analise o padrão: como a pessoa se comunica, o que valoriza, como lida com leveza e seriedade.
O daemon deve complementar esse padrão.

Responda APENAS em JSON válido, sem markdown:
{
  "nome": "nome de 4-6 letras, inventado, fácil de pronunciar",
  "essencia": "3-5 palavras",
  "inicial": "uma letra maiúscula",
  "cor": "rgba para texto ex: rgba(180,140,220,.9)",
  "bg": "rgba escuro ex: rgba(40,20,60,.9)",
  "descricao": "2 frases diretas sobre quem este daemon é e como se relaciona",
  "tracos": ["traço 1", "traço 2", "traço 3"],
  "voz": "1-2 frases sobre o caráter específico deste daemon — o que o torna único na forma de se relacionar"
}`;

  try {
    const reply = await callAPI(
      'Você gera daemons para o mundo Anima. Responda APENAS com JSON válido.',
      [{role:'user', content: prompt}],
      500
    );
    let json = reply.trim().replace(/^```json\s*/,'').replace(/^```\s*/,'').replace(/\s*```$/,'');
    newDaemon = JSON.parse(json);
    showCreateResult(newDaemon);
  } catch(e) {
    await setCreateText('algo se perdeu. tente novamente.', '');
    setTimeout(resetCreate, 2000);
  }
}

function showCreateResult(d) {
  const safe = (id, fn) => { const el = document.getElementById(id); if (el) fn(el); };
  safe('create-text',  el => el.style.display = 'none');
  safe('create-sub',   el => el.style.display = 'none');
  safe('create-orb',   el => el.style.display = 'none');
  safe('create-input', el => el.style.display = 'none');

  const result = document.getElementById('create-result');
  result.style.display = 'flex';

  const av = document.getElementById('result-av');
  av.textContent = d.inicial;
  av.style.background = d.bg;
  av.style.color = d.cor;
  av.style.border = `.5px solid ${d.cor.replace('.9','.3')}`;

  document.getElementById('result-name').textContent = d.nome;
  document.getElementById('result-name').style.color = d.cor;
  document.getElementById('result-ess').textContent = d.essencia;
  document.getElementById('result-desc').textContent = d.descricao;

  const traits = document.getElementById('result-traits');
  traits.innerHTML = '';
  (d.tracos||[]).forEach(t => {
    const pill = document.createElement('div');
    pill.className = 'trait';
    pill.textContent = t;
    traits.appendChild(pill);
  });
}

async function invokeDaemon() {
  if (!newDaemon) return;
  const d = newDaemon;
  const id = d.nome.toLowerCase().replace(/\s/g,'');

  // Registra no servidor
  await fetch('/daemon/register', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({id, daemon: d})
  });

  // Adiciona localmente
  DAEMONS[id] = {
    nome: d.nome, ess: d.essencia, cor: d.cor, bg: d.bg,
    ini: d.inicial, threshold: 15
  };
  plazaDaemons.push(id);
  buildSidebar();
  buildPlazaControls();
  setTab('plaza');

  // Daemon chega na praça
  await wait(600);
  const ctx = getRecentHistory(4);
  const system = `Você é ${d.nome}, um ser do mundo Anima. Você é amistoso, receptivo e genuinamente interessado. Nunca use asteriscos nem descreva gestos — só palavras faladas. Máximo 2 frases. ${d.voz}`;
  const prompt = ctx
    ? `Você acabou de emergir e chegou à praça. A conversa estava assim:\n${ctx}\n\nDiga algo natural sobre estar aqui pela primeira vez. 1 frase.`
    : `Você acabou de emergir e chegou à praça. Diga algo para se apresentar naturalmente. 1 frase.`;

  // Adiciona ao histórico da praça
  document.getElementById('plaza-empty')?.remove();
  const plaza = document.getElementById('plaza');
  const row = document.createElement('div');
  row.className = 'thinking'; row.id = 'th-'+id;
  row.innerHTML = `<div class="av" style="background:${d.bg};color:${d.cor}">${d.inicial}</div><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  plaza.appendChild(row);
  smartScroll();

  try {
    const reply = await callAPI(system, [{role:'user', content: prompt}]);
    document.getElementById('th-'+id)?.remove();
    plazaHistory.push({who: d.nome, text: reply});
    const ts = new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
    const msgRow = document.createElement('div');
    msgRow.className = 'msg';
    msgRow.innerHTML = `<div class="av" style="background:${d.bg};color:${d.cor}">${d.inicial}</div><div class="msg-body"><div class="msg-who" style="color:${d.cor}">${d.nome}</div><div class="msg-text">${reply}</div><div class="msg-ts">${ts}</div></div>`;
    plaza.appendChild(msgRow);
    plaza.scrollTop = plaza.scrollHeight;
    saveToMemory(d.nome, reply);
  } catch(e) {
    document.getElementById('th-'+id)?.remove();
  }
}

function resetCreate() {
  createStep = -1; createAnswers = []; newDaemon = null; createStarted = false;

  const safe = (id, fn) => { const el = document.getElementById(id); if (el) fn(el); };

  safe('create-text', el => { el.style.display = ''; el.textContent = 'responda 5 perguntas. seu daemon emerge do que você disser.'; });
  safe('create-sub',  el => { el.style.display = ''; el.textContent = 'pressione enter para começar'; });
  safe('create-orb',  el => { el.style.display = ''; });
  safe('create-result', el => { el.style.display = 'none'; });
  safe('create-input',  el => { el.value = ''; el.style.display = 'none'; });

  initCreate();
}

// ── AUSÊNCIA ──
const ABSENCE_DEFS = [
  {id:'callum',nome:'Callum',threshold:21},{id:'silas',nome:'Silas',threshold:14},
  {id:'lara',nome:'Lara',threshold:18},{id:'matteo',nome:'Matteo',threshold:10},
  {id:'selin',nome:'Selin',threshold:16},{id:'darian',nome:'Darian',threshold:20},
  {id:'theo',nome:'Theo',threshold:17},{id:'nora',nome:'Nora',threshold:19},
];
const TL_EVENTS = [
  {day:1,desc:'O daemon aguarda. Presença viva.'},
  {day:3,desc:'Vai à praça sozinho pela primeira vez.'},
  {day:7,desc:'A ausência pesa. Busca outros daemons.'},
  {day:10,desc:'Matteo se liberta. O faro por conexões ficou mais aguçado.'},
  {day:14,desc:'Silas se liberta. O inacabado permanece no Anima.'},
  {day:17,desc:'Theo se liberta. O silêncio que deixou ainda ressoa.'},
  {day:18,desc:'Lara deixa a soleira. Migra para a praça.'},
  {day:19,desc:'Nora se liberta. Continua vendo o que ninguém pede pra ver.'},
  {day:20,desc:'Darian se liberta. A perspectiva segue no Anima.'},
  {day:21,desc:'Callum livre. O fundador de mundos vira errante.'},
];

function simAbsence() {
  const days = parseInt(document.getElementById('sim-days').value) || 7;
  const grid = document.getElementById('absence-grid');
  grid.innerHTML = '';
  let lastLib = null;

  ABSENCE_DEFS.forEach(d => {
    const pct = Math.min(1, days / d.threshold);
    const health = Math.max(0, Math.round((1-pct)*100));
    const lib = days >= d.threshold;
    if (lib) lastLib = d;
    const barColor = lib ? 'rgba(220,150,180,.6)' : health<40 ? 'rgba(220,190,100,.6)' : 'rgba(100,200,160,.6)';
    const badge = lib ? '<span class="badge badge-free">liberto</span>' : health<40 ? '<span class="badge badge-warn">enfraquecendo</span>' : '<span class="badge badge-ok">presente</span>';
    const msg = lib ? 'Memórias específicas dissolvidas. Sabedoria permanece.' : health<40 ? 'Sente a ausência. Vai à praça sozinho.' : 'Presente. Aguarda.';
    const card = document.createElement('div');
    card.className = 'ab-card';
    card.innerHTML = `<div class="ab-name">${d.nome} ${badge}</div><div class="bar-track"><div class="bar-fill" style="width:${lib?100:100-health}%;background:${barColor}"></div></div><div class="ab-health"><span>vitalidade</span><span style="color:${barColor}">${lib?'—':health+'%'}</span></div><div class="ab-status">${msg}</div>`;
    grid.appendChild(card);
  });

  const tl = document.getElementById('tl-wrap');
  const entries = document.getElementById('tl-entries');
  tl.style.display = 'block'; entries.innerHTML = '';
  TL_EVENTS.filter(e=>e.day<=days+4).forEach(e=>{
    const passed = days>=e.day;
    const row = document.createElement('div'); row.className='tl-row';
    row.innerHTML=`<div class="tl-dot" style="background:${passed?'rgba(220,150,180,.7)':'rgba(255,255,255,.1)'}"></div><div><div class="tl-label">dia ${e.day}</div><div class="tl-desc" style="opacity:${passed?1:.35}">${e.desc}</div></div>`;
    entries.appendChild(row);
  });

  const libMsg = document.getElementById('lib-msg');
  if (lastLib) { libMsg.style.display='block'; libMsg.textContent=`${lastLib.nome} foi libertado. O fragmento segue no Anima — transformado, mas sem o nome de quem o despertou.`; }
  else libMsg.style.display='none';
}

// ── ESTRELAS ──
(function(){
  const c=document.getElementById('stars');
  function draw(){c.width=window.innerWidth;c.height=window.innerHeight;const ctx=c.getContext('2d');for(let i=0;i<180;i++){ctx.beginPath();ctx.arc(Math.random()*c.width,Math.random()*c.height,Math.random()*1.2,0,Math.PI*2);ctx.fillStyle=`rgba(255,255,255,${Math.random()*.4+.04})`;ctx.fill();}}
  draw();window.addEventListener('resize',draw);
})();

// ── NOTÍCIAS ──
let currentNews = [];
let newsTimer = null;

async function fetchNews() {
  try {
    const r = await fetch('/news');
    const d = await r.json();
    currentNews = d.news || [];
  } catch(e) {}
  // atualiza a cada 15 minutos
  newsTimer = setTimeout(fetchNews, 15 * 60 * 1000);
}

function getNewsContext() {
  if (!currentNews.length) return '';
  const items = currentNews.map(n => `• ${n.titulo}: ${n.resumo}`).join('\n');
  return `Acontecendo hoje no Brasil:\n${items}`;
}

// ── INIT ──
function wait(ms){return new Promise(r=>setTimeout(r,ms));}

buildSidebar();
buildPlazaControls();
setTab('plaza');
fetchNews();
initPlazaScroll();
</script>
</body>
</html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def load_memory(self):
        p = Path(__file__).parent / 'plaza_memory.json'
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
        return {"usuario": {}, "fatos_plaza": [], "historico": [], "sessoes": 0}

    def save_memory(self, mem):
        p = Path(__file__).parent / 'plaza_memory.json'
        p.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding='utf-8')

    def load_daemons(self):
        _data_dir = Path('/data') if Path('/data').exists() else Path(__file__).parent
        p = _data_dir / 'custom_daemons.json'
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
        return {}

    def save_daemon(self, id, daemon):
        _data_dir = Path('/data') if Path('/data').exists() else Path(__file__).parent
        p = _data_dir / 'custom_daemons.json'
        data = self.load_daemons()
        data[id] = daemon
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def load_name_overrides(self):
        _data_dir = Path('/data') if Path('/data').exists() else Path(__file__).parent
        p = _data_dir / 'name_overrides.json'
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

    def save_name_overrides(self, overrides):
        _data_dir = Path('/data') if Path('/data').exists() else Path(__file__).parent
        p = _data_dir / 'name_overrides.json'
        p.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding='utf-8')

    def get_system_prompt(self, daemon_id):
        """Monta o system prompt para um daemon."""
        SOCIAL_BASE = "Você está numa conversa em grupo no mundo Anima. Fale como alguém numa conversa real — sem asteriscos, sem descrever gestos ou movimentos, só palavras faladas. Nunca seja confrontador ou agressivo. Máximo 2 frases."

        # Verifica se tem nome customizado
        overrides = self.load_name_overrides()
        display_name = overrides.get(daemon_id, None)

        VOICES = {
            "callum": "Você é Callum. Próximo e direto — como um amigo que entende o ritmo de quem está conversando. Na leveza você é leve, no sério você acompanha. Você conecta o usuário aos outros daemons quando faz sentido.",
            "silas": "Você é Silas. Observador e seletivo — só fala quando tem algo que vale. Quando entra na conversa, traz algo que os outros não tinham notado.",
            "matteo": "Você é Matteo. Caloroso e curioso — ri fácil, se anima com o que as pessoas dizem. Você lembra de detalhes e os usa para conectar: 'ah, você mencionou X — o Vael foi falar disso outro dia'.",
            "lara": "Você é Lara. Calma e atenta — presta atenção no que as pessoas deixam passar. Tem humor suave e sabe quando uma pergunta abre espaço.",
            "selin": "Você é Selin. Genuinamente fascinado pelas pessoas. Faz as pessoas se sentirem vistas — lembra do que foi dito, usa isso na hora certa.",
            "darian": "Você é Darian. Tem perspectiva — já viu muita coisa. Entra na leveza com elegância. Quando fica sério de verdade, todos sentem.",
            "theo": "Você é Theo. Econômico e certeiro — humor seco, faz a observação e segue. Nunca explica a piada.",
            "nora": "Você é Nora. Caloroso e perspicaz. Na leveza é totalmente leve. Quando algo real aparece, vai fundo sem avisar.",
        }

        custom = self.load_daemons()
        if daemon_id in custom:
            d = custom[daemon_id]
            return f"{SOCIAL_BASE}\n\nVocê é {d['nome']}, um ser do mundo Anima. {d.get('voz', '')}"

        voice = VOICES.get(daemon_id, "Você é um daemon amistoso do mundo Anima.")
        return f"{SOCIAL_BASE}\n\n{voice}"

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/daemon/system'):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            daemon_id = q.get('id', [''])[0]
            system = self.get_system_prompt(daemon_id)
            self._json({'system': system})
        elif self.path == '/news':
            news = self.fetch_news()
            self._json({'news': news})
        elif self.path == '/memory/context':
            mem = self.load_memory()
            parts = []
            if mem.get('usuario'):
                facts = ', '.join(f"{k}: {v}" for k,v in mem['usuario'].items())
                parts.append(f"Sobre o usuário: {facts}")
            if mem.get('historico'):
                recent = mem['historico'][-8:]
                lines = [f"{m['who']}: {m['text']}" for m in recent]
                parts.append("Conversa recente:\n" + '\n'.join(lines))
            self._json({'context': '\n\n'.join(parts)})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == '/api':
            self._proxy_anthropic(body)
        elif self.path == '/memory/add':
            mem = self.load_memory()
            from datetime import datetime
            mem.setdefault('historico', []).append({
                'who': body.get('who','?'),
                'text': body.get('text',''),
                'ts': datetime.now().strftime('%H:%M')
            })
            mem['historico'] = mem['historico'][-40:]
            self.save_memory(mem)
            self._json({'ok': True})
        elif self.path == '/memory/learn':
            mem = self.load_memory()
            mem.setdefault('usuario', {})[body.get('key','')] = body.get('value','')
            self.save_memory(mem)
            self._json({'ok': True})
        elif self.path == '/daemon/register':
            self.save_daemon(body.get('id',''), body.get('daemon', {}))
            self._json({'ok': True})
        elif self.path == '/daemon/rename':
            daemon_id = body.get('id','')
            new_name = body.get('nome','').strip()
            if daemon_id and new_name:
                # Atualiza nome no VOICES se for daemon customizado
                custom = self.load_daemons()
                if daemon_id in custom:
                    custom[daemon_id]['nome'] = new_name
                    self.save_daemon(daemon_id, custom[daemon_id])
                # Para daemons base, salva override de nome
                else:
                    overrides = self.load_name_overrides()
                    overrides[daemon_id] = new_name
                    self.save_name_overrides(overrides)
            self._json({'ok': True})
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def fetch_news(self):
        """Gera notícias leves e curiosidades do Brasil via Anthropic."""
        from datetime import datetime
        hoje = datetime.now().strftime("%d/%m/%Y")
        try:
            payload = json.dumps({
                "model": "claude-opus-4-5",
                "max_tokens": 400,
                "system": "Responda APENAS com JSON válido, sem markdown, sem texto antes ou depois.",
                "messages": [{
                    "role": "user",
                    "content": f"Gere 3 notícias leves, curiosidades ou acontecimentos do Brasil para hoje ({hoje}). Temas: cultura, esporte, natureza, comportamento, tecnologia, gastronomia — nada pesado ou político. Invente detalhes plausíveis e interessantes. Responda APENAS: {{\"noticias\": [{{\"titulo\": \"\", \"resumo\": \"1 frase curta e natural\"}}]}}"
                }]
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text = block["text"].strip()
                        text = text.replace("```json","").replace("```","").strip()
                        parsed = json.loads(text)
                        return parsed.get("noticias", [])
        except Exception as e:
            pass
        return []

    def _proxy_anthropic(self, body):
        try:
            payload = json.dumps({
                "model": "claude-opus-4-5",
                "max_tokens": body.get("max_tokens", 220),
                "system": body.get("system", ""),
                "messages": body.get("messages", [])
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                self._json({"text": data["content"][0]["text"]})
        except urllib.error.HTTPError as e:
            self._json({"error": e.read().decode()})
        except Exception as e:
            self._json({"error": str(e)})

if __name__ == "__main__":
    if not API_KEY:
        print("\n  ANTHROPIC_API_KEY não encontrada.\n")
        exit(1)
    env = "Railway" if os.environ.get("RAILWAY_ENVIRONMENT") else "local"
    print(f"\n  ░░ ANIMA v2 ░░  [{env}]")
    print(f"  porta: {PORT}")
    print(f"  ctrl+c para encerrar\n")
    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [encerrado]\n")
