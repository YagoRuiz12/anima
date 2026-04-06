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
import hashlib, secrets, time
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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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

/* ── WAKE SCREEN ── */
#wake-screen{
  position:fixed;inset:0;z-index:1000;background:#000;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;
}
#wake-stars{position:absolute;inset:0;pointer-events:none}

#wake-content{
  display:flex;flex-direction:column;align-items:center;gap:32px;
  animation:wake-pulse 3s ease-in-out infinite;
}
@keyframes wake-pulse{0%,100%{opacity:.6}50%{opacity:1}}

#wake-logo{
  width:80px;height:80px;background:#0a0a0a;
  border:1px solid rgba(200,140,80,.3);border-radius:16px;
  display:flex;align-items:center;justify-content:center;gap:10px;
  box-shadow:0 0 40px rgba(200,140,80,.08);
}
.eye{
  width:22px;height:14px;background:#1a1208;border-radius:3px;
  display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(200,140,80,.4);
  position:relative;overflow:hidden;
}
.pupil{
  width:8px;height:8px;background:rgba(200,140,80,.9);border-radius:50%;
  box-shadow:0 0 6px rgba(200,140,80,.8);
  animation:blink 4s ease-in-out infinite;
}
@keyframes blink{
  0%,45%,55%,100%{transform:scaleY(1);opacity:1}
  50%{transform:scaleY(0.1);opacity:.5}
}

#wake-tap{
  font-family:'DM Mono',monospace;
  font-size:11px;letter-spacing:4px;
  color:rgba(200,140,80,.6);
  text-transform:uppercase;
  animation:tap-blink 1.8s ease-in-out infinite;
}
@keyframes tap-blink{0%,100%{opacity:.4}50%{opacity:.9}}

/* ── LOGIN CARD ── */
#login-card{
  position:absolute;
  width:min(380px, 92vw);
  background:#0d0d0d;
  border:1px solid rgba(200,140,80,.2);
  border-radius:20px;
  padding:32px 28px;
  display:flex;flex-direction:column;align-items:center;gap:20px;
  box-shadow:0 20px 60px rgba(0,0,0,.8), 0 0 0 1px rgba(200,140,80,.05);
  animation:card-in .5s cubic-bezier(.16,1,.3,1);
}
@keyframes card-in{from{opacity:0;transform:translateY(20px) scale(.97)}to{opacity:1;transform:none}}

#login-logo-small{display:flex;gap:8px;align-items:center}
.eye-s{
  width:18px;height:11px;background:#1a1208;border-radius:2px;
  display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(200,140,80,.4);
  transition:transform .1s ease;
  overflow:hidden;
}
.pupil-s{
  width:6px;height:6px;background:rgba(200,140,80,.9);border-radius:50%;
  box-shadow:0 0 4px rgba(200,140,80,.8);
  transition:transform .08s ease;
}

#login-title{
  font-family:'Cormorant Garamond',serif;
  font-size:28px;font-weight:300;letter-spacing:6px;
  color:rgba(255,255,255,.9);margin-top:-8px;
}
#login-sub{font-size:10px;letter-spacing:2px;color:rgba(200,140,80,.5);text-transform:uppercase;margin-top:-14px}

#login-tabs{
  display:flex;gap:0;width:100%;
  border:.5px solid rgba(200,140,80,.2);border-radius:8px;overflow:hidden;
}
.ltab{
  flex:1;padding:8px;text-align:center;
  font-size:11px;letter-spacing:1.5px;text-transform:uppercase;
  color:rgba(255,255,255,.35);cursor:pointer;transition:all .2s;
}
.ltab.active{background:rgba(200,140,80,.12);color:rgba(200,140,80,.9)}
.ltab:hover:not(.active){color:rgba(255,255,255,.6)}

#auth-form{display:flex;flex-direction:column;gap:10px;width:100%}
.auth-input{
  width:100%;background:rgba(255,255,255,.04);
  border:.5px solid rgba(255,255,255,.1);border-radius:8px;
  padding:12px 14px;font-family:'DM Mono',monospace;font-size:13px;
  color:rgba(255,255,255,.85);outline:none;transition:border-color .2s;
}
.auth-input:focus{border-color:rgba(200,140,80,.4)}
.auth-input::placeholder{color:rgba(255,255,255,.25)}

#auth-error{font-size:11px;color:rgba(220,100,80,.8);text-align:center;min-height:14px}

#auth-btn{
  width:100%;background:rgba(200,140,80,.15);
  border:1px solid rgba(200,140,80,.4);border-radius:8px;
  padding:13px;font-family:'DM Mono',monospace;font-size:12px;
  letter-spacing:2px;text-transform:uppercase;
  color:rgba(200,140,80,.9);cursor:pointer;transition:all .2s;
  margin-top:4px;
}
#auth-btn:hover{background:rgba(200,140,80,.25);border-color:rgba(200,140,80,.7)}
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
.session-daemon-info{padding:12px 20px;border-bottom:.5px solid var(--rim);display:flex;align-items:center;gap:14px}
.session-name{font-size:14px;letter-spacing:1px;text-transform:uppercase}
.session-ess{font-size:11px;color:var(--hint);margin-top:3px}
.session-chat{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:12px}
.session-empty{display:flex;align-items:center;justify-content:center;flex:1;font-family:'Cormorant Garamond',serif;font-size:20px;font-style:italic;color:var(--hint)}
.session-input-wrap{border-top:.5px solid var(--rim);padding:14px 20px;display:flex;gap:10px;align-items:center}
#session-input{flex:1;background:var(--panel);border:.5px solid var(--rim2);border-radius:24px;padding:12px 20px;font-family:'Cormorant Garamond',serif;font-size:18px;color:var(--text);outline:none;transition:border-color .2s}
#session-input:focus{border-color:rgba(255,255,255,.25)}
#session-input::placeholder{color:var(--hint);font-style:italic}

/* ── DAEMON FACE ── */
.daemon-face{
  width:56px;height:56px;background:#0a0a0a;
  border-radius:10px;display:flex;align-items:center;justify-content:center;gap:6px;
  flex-shrink:0;position:relative;overflow:hidden;cursor:pointer;
  border:1px solid rgba(255,255,255,.08);
}
.daemon-face .grid-bg{
  position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
  background-size:8px 8px;
}
.deye{
  width:16px;height:10px;border-radius:3px;
  display:flex;align-items:center;justify-content:center;
  position:relative;overflow:hidden;flex-shrink:0;
  border:1px solid;
}
.dpupil{
  width:5px;height:5px;border-radius:50%;
  transition:transform .08s ease;position:relative;
}
.dpupil::after{
  content:'';position:absolute;width:2px;height:2px;
  background:#0a0a0a;border-radius:50%;
  top:50%;left:50%;transform:translate(-50%,-50%);
}
.delid{position:absolute;left:0;right:0;height:0;background:#0a0a0a;transition:height .1s ease}
.delid-t{top:0}.delid-b{bottom:0}

/* CRIAR DAEMON */
.create-wrap{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 20px;gap:0;overflow-y:auto}

/* Rosto do onboarding */
#onb-face-wrap{
  width:140px;height:90px;background:#0a0a0a;
  border:1px solid rgba(200,140,80,.2);border-radius:18px;
  display:flex;align-items:center;justify-content:center;gap:14px;
  position:relative;overflow:hidden;margin-bottom:20px;cursor:pointer;
  flex-shrink:0;
}
#onb-grid{
  position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(200,140,80,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(200,140,80,.04) 1px,transparent 1px);
  background-size:12px 12px;
}
.onb-eye{
  width:38px;height:24px;background:#080808;
  border:1px solid rgba(200,140,80,.35);border-radius:5px;
  display:flex;align-items:center;justify-content:center;
  position:relative;overflow:hidden;
}
.onb-pupil{
  width:10px;height:10px;background:rgba(200,140,80,.9);border-radius:50%;
  transition:transform .08s ease;position:relative;
}
.onb-pupil::after{
  content:'';position:absolute;width:4px;height:4px;
  background:#080808;border-radius:50%;
  top:50%;left:50%;transform:translate(-50%,-50%);
}
.onb-lid{position:absolute;left:0;right:0;height:0;background:#080808;transition:height .1s ease}
.onb-lid-t{top:0}.onb-lid-b{bottom:0}

#onb-name{font-family:'Cormorant Garamond',serif;font-size:22px;font-weight:300;letter-spacing:5px;color:rgba(255,255,255,.8)}
#onb-sub{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(200,140,80,.4);margin-top:4px;margin-bottom:20px}

#onb-bubble-wrap{width:100%;max-width:440px;min-height:56px;margin-bottom:16px;display:flex;flex-direction:column;align-items:center;gap:6px}
#onb-typing{display:flex;gap:5px;align-items:center;height:20px;opacity:0;transition:opacity .3s}
.onb-dot{width:5px;height:5px;border-radius:50%;background:rgba(200,140,80,.5);animation:odot 1.1s infinite}
.onb-dot:nth-child(2){animation-delay:.2s}.onb-dot:nth-child(3){animation-delay:.4s}
@keyframes odot{0%,100%{opacity:.2;transform:scale(.8)}50%{opacity:1;transform:scale(1.1)}}
#onb-bubble{
  font-family:'Cormorant Garamond',serif;font-size:18px;font-style:italic;
  color:rgba(255,255,255,.75);text-align:center;line-height:1.65;
  max-width:440px;opacity:0;transition:opacity .4s;
}

#onb-input-row{width:100%;max-width:440px;display:flex;gap:8px;align-items:center;margin-top:4px}
#create-input{
  flex:1;background:rgba(255,255,255,.04);
  border:.5px solid rgba(200,140,80,.25);border-radius:12px;
  padding:11px 16px;font-family:'Cormorant Garamond',serif;font-size:17px;
  color:var(--text);outline:none;transition:border-color .3s;
}
#create-input:focus{border-color:rgba(200,140,80,.5)}
#create-input::placeholder{color:var(--hint);font-style:italic}
#onb-send{
  width:42px;height:42px;background:rgba(200,140,80,.12);
  border:1px solid rgba(200,140,80,.3);border-radius:10px;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .2s;flex-shrink:0;
}
#onb-send:hover{background:rgba(200,140,80,.25)}

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

@keyframes spin{to{transform:rotate(360deg)}}

/* ── MOBILE ── */
@media (max-width: 768px) {
  .main{grid-template-columns:1fr;height:calc(100vh - 56px)}

  /* sidebar vira barra inferior */
  .sidebar{
    position:fixed;bottom:0;left:0;right:0;z-index:50;
    flex-direction:column;height:auto;
    border-right:none;border-top:.5px solid var(--rim2);
    background:var(--void);
  }
  .sidebar-section{display:none}
  .daemon-list{
    flex-direction:row;overflow-x:auto;overflow-y:hidden;
    padding:8px 12px;gap:10px;flex:none;
    scrollbar-width:none;-ms-overflow-style:none;
    border-bottom:none;
  }
  .daemon-list::-webkit-scrollbar{display:none}
  .d-card{
    flex-direction:column;align-items:center;
    padding:8px 10px;min-width:60px;border-radius:12px;
    gap:4px;text-align:center;
  }
  .d-av{width:36px;height:36px;font-size:15px}
  .d-info{display:none}
  .d-badge{display:none}
  .d-card .d-av{display:flex}
  /* mostra só inicial + ponto se estiver na praça */
  .d-card.in-plaza::after{
    content:'';width:6px;height:6px;border-radius:50%;
    background:rgba(100,200,160,.8);display:block;margin:0 auto;
  }
  .sidebar > div:last-child{display:none} /* esconde "+ criar daemon" da sidebar */

  /* área principal ocupa tudo */
  .area{height:calc(100vh - 56px - 68px)}

  /* tabs menores */
  .tabs{padding:0 8px;overflow-x:auto;scrollbar-width:none}
  .tabs::-webkit-scrollbar{display:none}
  .tab{font-size:9px;padding:10px 10px;white-space:nowrap}

  /* praça */
  .plaza{padding:12px 14px}
  .msg-text{font-size:17px}
  .msg.you .msg-text{font-size:16px}
  .av{width:34px;height:34px;font-size:14px}
  .msg{gap:10px;padding:12px 0}

  /* input da praça */
  .plaza-input-wrap{padding:10px 12px;gap:8px}
  #plaza-input{font-size:16px;padding:10px 14px}
  .btn-send{padding:10px 14px;font-size:10px}

  /* sessão */
  .session-chat{padding:12px 14px}
  .session-daemon-info{padding:12px 14px}
  .session-input-wrap{padding:10px 12px;gap:8px}
  #session-input{font-size:16px;padding:10px 14px}

  /* scroll btn */
  .scroll-btn{bottom:130px;right:12px}

  /* controles da praça */
  .plaza-controls{padding:8px 12px;gap:6px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  .plaza-controls::-webkit-scrollbar{display:none}
  .pc-label{display:none}
  .pc-btn{font-size:9px;padding:4px 8px;white-space:nowrap}
  .btn-flow{font-size:9px;padding:4px 10px}

  /* criar daemon */
  .create-wrap{padding:24px 20px}
  .create-text{font-size:18px}
  .create-input{font-size:16px}

  /* ausência */
  .absence-grid{grid-template-columns:1fr}
  .absence-wrap{padding:12px 14px}

  /* mention popup */
  .mention-popup{left:8px !important;right:8px;width:auto}

  /* reply banner */
  #reply-banner{padding:6px 12px 0}

  /* header */
  .hdr{padding:12px 16px 10px}
  .logo{font-size:20px;letter-spacing:4px}
  .sub{font-size:9px}
  .status{font-size:10px}
}

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
<!-- WAKE SCREEN -->
<div id="wake-screen">
  <canvas id="wake-stars"></canvas>
  <div id="wake-content">
    <div id="wake-logo">
      <div id="wake-eyes">
        <div class="eye" id="eye-left"><div class="pupil"></div></div>
        <div class="eye" id="eye-right"><div class="pupil"></div></div>
      </div>
    </div>
    <div id="wake-tap">TAP TO WAKE</div>
  </div>

  <!-- CARD DE LOGIN -->
  <div id="login-card" style="display:none">
    <div id="login-logo-small">
      <div class="eye-s"><div class="pupil-s"></div></div>
      <div class="eye-s"><div class="pupil-s"></div></div>
    </div>
    <div id="login-title">ANIMA</div>
    <div id="login-sub">o mundo sempre existiu</div>

    <div id="login-tabs">
      <div class="ltab active" onclick="switchAuth('login')">entrar</div>
      <div class="ltab" onclick="switchAuth('signup')">criar conta</div>
    </div>

    <div id="auth-form">
      <div id="signup-name-wrap" style="display:none">
        <input class="auth-input" id="auth-name" type="text" placeholder="seu nome"/>
      </div>
      <input class="auth-input" id="auth-email" type="email" placeholder="email"/>
      <input class="auth-input" id="auth-pass" type="password" placeholder="senha"
             onkeydown="if(event.key==='Enter')submitAuth()"/>
      <div id="auth-error"></div>
      <button id="auth-btn" onclick="submitAuth()">
        <span id="auth-btn-text">entrar</span>
        <span id="auth-loading" style="display:none">···</span>
      </button>
    </div>
  </div>
</div>

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
      <div class="tab" onclick="setTab('vila')">vila ↗</div>
      <div class="tab active" onclick="setTab('plaza')">praça livre</div>
      <div class="tab" id="tab-session" onclick="setTab('session')" style="display:none">sessão — <span id="tab-session-name"></span></div>
      <div class="tab" onclick="setTab('create')">criar daemon</div>
      <div class="tab" onclick="setTab('absence')">ausência</div>
    </div>

    <!-- VILA 3D -->
    <div id="view-vila" style="display:none;flex:1;position:relative;overflow:hidden;background:#0a1a0a">
      <div id="vila-load" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0a1a0a;z-index:5;font-family:monospace;color:rgba(100,200,80,.7);letter-spacing:3px;font-size:11px;gap:12px">
        <div style="width:36px;height:36px;border:2px solid rgba(100,200,80,.3);border-top-color:rgba(100,200,80,.8);border-radius:50%;animation:spin 1s linear infinite"></div>
        ANIMA · VILA
      </div>
      <canvas id="vila-canvas" style="position:absolute;inset:0;width:100%;height:100%"></canvas>
      <div id="vila-hud" style="position:absolute;top:12px;left:12px;z-index:10;background:rgba(5,15,5,.85);border:1px solid rgba(100,200,80,.35);border-radius:8px;padding:5px 12px;color:rgba(130,220,100,.9);font-size:10px;letter-spacing:3px;font-family:monospace">ANIMA · VILA</div>
      <div id="vila-tip" style="position:absolute;z-index:10;pointer-events:none;display:none;background:rgba(5,12,5,.95);border:1px solid rgba(100,180,70,.4);border-radius:10px;padding:10px 16px;font-family:monospace">
        <div id="vila-tip-name" style="font-size:13px;color:rgba(160,230,120,.9);letter-spacing:1px;margin-bottom:3px"></div>
        <div id="vila-tip-d" style="font-size:10px;color:rgba(255,255,255,.45)"></div>
      </div>
      <div id="vila-ov" style="position:absolute;inset:0;z-index:20;background:#050d05;opacity:0;pointer-events:none;transition:opacity .35s"></div>
      <!-- LOC PANEL -->
      <div id="vila-pan" style="position:absolute;inset:0;z-index:15;background:#070e07;display:none;flex-direction:column;align-items:center;padding:20px;overflow-y:auto;font-family:monospace">
        <div onclick="vilaBack()" style="position:absolute;top:14px;left:14px;background:rgba(80,160,60,.12);border:1px solid rgba(80,160,60,.3);border-radius:7px;padding:6px 14px;color:rgba(120,210,90,.8);font-size:10px;letter-spacing:1.5px;cursor:pointer">← voltar</div>
        <div id="vila-pt" style="font-size:22px;letter-spacing:5px;color:rgba(220,240,200,.9);margin-top:8px"></div>
        <div id="vila-ps" style="font-size:10px;color:rgba(80,160,60,.5);margin-bottom:4px;font-style:italic"></div>
        <div id="vila-pd" style="font-size:10px;color:rgba(255,255,255,.2);margin-bottom:20px;letter-spacing:1px"></div>
        <div id="vila-pf" style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-bottom:16px"></div>
        <div id="vila-pe" style="max-width:400px;border:.5px solid rgba(80,160,60,.2);border-radius:10px;padding:12px;text-align:center;font-size:11px;color:rgba(80,160,60,.4);letter-spacing:1px;font-style:italic"></div>
      </div>
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
      <div class="session-daemon-info" id="session-info">
        <div class="daemon-face" id="session-face" onclick="sessionFaceClick()">
          <div class="grid-bg"></div>
          <div class="deye" id="sf-el">
            <div class="delid delid-t" id="sf-ltl"></div>
            <div class="dpupil" id="sf-pl"></div>
            <div class="delid delid-b" id="sf-lbl"></div>
          </div>
          <div class="deye" id="sf-er">
            <div class="delid delid-t" id="sf-ltr"></div>
            <div class="dpupil" id="sf-pr"></div>
            <div class="delid delid-b" id="sf-lbr"></div>
          </div>
        </div>
        <div id="session-info-text"></div>
      </div>
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

      <!-- ROSTO NEUTRO DO ONBOARDING -->
      <div id="onb-face-wrap">
        <div id="onb-grid"></div>
        <div class="onb-eye" id="onb-el">
          <div class="onb-lid onb-lid-t" id="onb-ltl"></div>
          <div class="onb-pupil" id="onb-pl"></div>
          <div class="onb-lid onb-lid-b" id="onb-lbl"></div>
        </div>
        <div class="onb-eye" id="onb-er">
          <div class="onb-lid onb-lid-t" id="onb-ltr"></div>
          <div class="onb-pupil" id="onb-pr"></div>
          <div class="onb-lid onb-lid-b" id="onb-lbr"></div>
        </div>
      </div>

      <div id="onb-name">ANIMA</div>
      <div id="onb-sub">presença em formação</div>

      <!-- BOLHA DE FALA -->
      <div id="onb-bubble-wrap">
        <div id="onb-typing"><div class="onb-dot"></div><div class="onb-dot"></div><div class="onb-dot"></div></div>
        <div id="onb-bubble"></div>
      </div>

      <!-- INPUT -->
      <div id="onb-input-row" style="display:none">
        <input id="create-input" type="text" placeholder="escreva e pressione enter"
               onkeydown="if(event.key==='Enter')answerCreate()"/>
        <button id="onb-send" onclick="answerCreate()">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="rgba(200,140,80,.9)"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>

      <!-- RESULTADO DO DAEMON -->
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
      buildSidebar(); // restaura
      return;
    }

    // Atualiza TUDO no objeto DAEMONS — fonte única de verdade
    DAEMONS[id].nome = newName;
    DAEMONS[id].ini = newName[0].toUpperCase();

    // Atualiza NAMES para que respondToUser e daemonSpeaks usem o nome certo
    // (NAMES é usado nos prompts — precisa bater com DAEMONS[id].nome)

    // Persiste no servidor
    await fetch('/daemon/rename', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id, nome: newName, ini: newName[0].toUpperCase()})
    });

    // Reconstrói sidebar + controles da praça com o novo nome
    buildSidebar();
    buildPlazaControls();

    // Atualiza tab de sessão se estiver aberta para esse daemon
    const tabName = document.getElementById('tab-session-name');
    if (tabName && sessionDaemon === id) {
      tabName.textContent = newName.toLowerCase();
    }

    // Atualiza info do header da sessão se estiver aberta
    const sessionInfo = document.getElementById('session-info');
    if (sessionInfo && sessionDaemon === id) {
      const nameEl = sessionInfo.querySelector('.session-name');
      if (nameEl) nameEl.textContent = newName;
    }

    // Atualiza mensagens já exibidas na praça com o nome antigo
    document.querySelectorAll('.msg-who').forEach(el => {
      if (el.textContent.trim().toUpperCase() === currentName.toUpperCase()) {
        el.textContent = newName.toUpperCase();
      }
    });
  };

  input.onblur = save;
  input.onkeydown = (ev) => {
    if (ev.key === 'Enter') { ev.preventDefault(); input.blur(); }
    if (ev.key === 'Escape') { input.value = currentName; input.blur(); }
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
// ── FACE ENGINE ──
let faceActive = false;
let faceBlinkTimer = null;
let faceMX = 0, faceMY = 0;
let faceRAF = null;
let faceIsBlinking = false;
let faceColor = '#c88c50';

function faceInit(cor) {
  faceColor = cor;
  const el = document.getElementById('sf-el');
  const er = document.getElementById('sf-er');
  if (!el) return;
  const c = cor.replace('.9','');
  [el, er].forEach(e => {
    e.style.borderColor = c.replace('rgba(','').replace(')','').split(',').slice(0,3).join(',');
    e.style.borderColor = cor.replace('.9','.4');
  });
  ['sf-pl','sf-pr'].forEach(id => {
    const p = document.getElementById(id);
    if (p) p.style.background = cor.replace('.9','.9');
  });
  faceActive = true;
  faceMovePupils();
  faceScheduleBlink();
}

function faceStop() {
  faceActive = false;
  clearTimeout(faceBlinkTimer);
  if (faceRAF) cancelAnimationFrame(faceRAF);
}

function faceMovePupils() {
  if (!faceActive) return;
  const face = document.getElementById('session-face');
  if (!face) return;
  const rect = face.getBoundingClientRect();
  const cx = rect.left + rect.width/2;
  const cy = rect.top + rect.height/2;
  const dx = Math.max(-6, Math.min(6, (faceMX - cx) * .08));
  const dy = Math.max(-4, Math.min(4, (faceMY - cy) * .08));
  ['sf-pl','sf-pr'].forEach(id => {
    const p = document.getElementById(id);
    if (p) p.style.transform = `translate(${dx}px,${dy}px)`;
  });
  faceRAF = requestAnimationFrame(faceMovePupils);
}

document.addEventListener('mousemove', e => { faceMX = e.clientX; faceMY = e.clientY; });

function faceBlink(half=false) {
  if (faceIsBlinking) return;
  faceIsBlinking = true;
  const h = half ? 5 : 10;
  ['sf-ltl','sf-lbl','sf-ltr','sf-lbr'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.height = h+'px';
  });
  setTimeout(() => {
    ['sf-ltl','sf-lbl','sf-ltr','sf-lbr'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.height = '0';
    });
    faceIsBlinking = false;
  }, half ? 350 : 120);
}

function faceScheduleBlink() {
  if (!faceActive) return;
  faceBlinkTimer = setTimeout(() => {
    const r = Math.random();
    faceBlink(r > .7);
    faceScheduleBlink();
  }, 2000 + Math.random() * 4000);
}

function sessionFaceClick() {
  faceBlink(true);
}

function openSession(daemonId) {
  faceStop();
  sessionDaemon = daemonId;
  sessionHistory = [];

  const d = DAEMONS[daemonId];
  const infoText = document.getElementById('session-info-text');
  if (infoText) infoText.innerHTML = `<div class="session-name" style="color:${d.cor}">${d.nome}</div><div class="session-ess">${d.ess}</div>`;

  // Inicializa rosto com a cor do daemon
  setTimeout(() => faceInit(d.cor), 100);

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

// ── ONBOARDING FACE ──
let onbBlinkTimer = null;
let onbIsBlinking = false;
let onbMX = 0, onbMY = 0;
let onbRAF = null;
let onbFaceActive = false;

function onbFaceStart() {
  onbFaceActive = true;
  onbMovePupils();
  onbScheduleBlink();
}
function onbFaceStop() {
  onbFaceActive = false;
  clearTimeout(onbBlinkTimer);
  if (onbRAF) cancelAnimationFrame(onbRAF);
}
function onbMovePupils() {
  if (!onbFaceActive) return;
  const face = document.getElementById('onb-face-wrap');
  if (!face) { onbRAF = requestAnimationFrame(onbMovePupils); return; }
  const rect = face.getBoundingClientRect();
  const cx = rect.left + rect.width/2, cy = rect.top + rect.height/2;
  const dx = Math.max(-8, Math.min(8, (onbMX-cx)*.1));
  const dy = Math.max(-5, Math.min(5, (onbMY-cy)*.1));
  ['onb-pl','onb-pr'].forEach(id => {
    const p = document.getElementById(id);
    if (p) p.style.transform = `translate(${dx}px,${dy}px)`;
  });
  onbRAF = requestAnimationFrame(onbMovePupils);
}
document.addEventListener('mousemove', e => { onbMX=e.clientX; onbMY=e.clientY; });

function onbBlink(half=false) {
  if (onbIsBlinking) return;
  onbIsBlinking = true;
  const h = half ? 12 : 24;
  ['onb-ltl','onb-lbl','onb-ltr','onb-lbr'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.height = h+'px';
  });
  setTimeout(() => {
    ['onb-ltl','onb-lbl','onb-ltr','onb-lbr'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.height = '0';
    });
    onbIsBlinking = false;
  }, half ? 380 : 130);
}
function onbScheduleBlink() {
  if (!onbFaceActive) return;
  onbBlinkTimer = setTimeout(() => {
    onbBlink(Math.random() > .65);
    onbScheduleBlink();
  }, 2200 + Math.random() * 3800);
}

function onbShowMessage(text, delay=0) {
  const typing = document.getElementById('onb-typing');
  const bubble = document.getElementById('onb-bubble');
  if (!typing || !bubble) return;
  setTimeout(() => {
    typing.style.opacity = '1';
    bubble.style.opacity = '0';
    const dur = Math.min(1400, text.length * 40);
    setTimeout(() => {
      typing.style.opacity = '0';
      bubble.textContent = text;
      bubble.style.opacity = '1';
      onbBlink(false);
      // mostra input depois da primeira mensagem
      const inputRow = document.getElementById('onb-input-row');
      if (inputRow) {
        inputRow.style.display = 'flex';
        setTimeout(() => document.getElementById('create-input')?.focus(), 100);
      }
    }, dur);
  }, delay);
}

function initCreate() {
  if (createStarted) return;
  createStarted = true;
  onbFaceStart();
  // Primeira mensagem da presença
  setTimeout(() => {
    onbShowMessage('algo aqui percebeu sua chegada.', 400);
  }, 200);
}

async function answerCreate() {
  const input = document.getElementById('create-input');
  const text = input.value.trim();

  if (createStep === -1) {
    createStep = 0;
    input.value = '';
    onbShowMessage('bem vindo. vamos começar.', 0);
    await wait(1800);
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

  const reactions = ['interessante.','continua.','essa resposta importa.','mais perto.','última pergunta.'];
  onbShowMessage(reactions[createStep-1] || '...');
  await wait(1800);
  showCreateQuestion(createStep);
}

function showCreateQuestion(i) {
  const q = CREATE_QUESTIONS[i];
  onbShowMessage(q.text, 0);
  document.getElementById('create-input')?.focus();
}

async function setCreateText(text, sub) {
  const el = document.getElementById('create-text');
  const sel = document.getElementById('create-sub');
  el.style.opacity = 0; await wait(250);
  el.textContent = text; sel.textContent = sub;
  el.style.opacity = 1;
}

async function generateNewDaemon() {
  onbShowMessage('analisando o que emergiu...');
  document.getElementById('onb-input-row').style.display = 'none';

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
  onbFaceStop();
  const safe = (id, fn) => { const el = document.getElementById(id); if (el) fn(el); };
  safe('onb-face-wrap',   el => el.style.display = 'none');
  safe('onb-name',        el => el.style.display = 'none');
  safe('onb-sub',         el => el.style.display = 'none');
  safe('onb-bubble-wrap', el => el.style.display = 'none');
  safe('onb-input-row',   el => el.style.display = 'none');

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
  onbFaceStop();

  const safe = (id, fn) => { const el = document.getElementById(id); if (el) fn(el); };
  safe('onb-face-wrap',   el => el.style.display = '');
  safe('onb-name',        el => el.style.display = '');
  safe('onb-sub',         el => el.style.display = '');
  safe('onb-bubble-wrap', el => { el.style.display = ''; });
  safe('onb-input-row',   el => el.style.display = 'none');
  safe('onb-bubble',      el => { el.style.opacity = '0'; el.textContent = ''; });
  safe('create-result',   el => el.style.display = 'none');
  safe('create-input',    el => { el.value = ''; });

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

// ── VILA 3D ──
let vilaInit = false;
let vilaRenderer, vilaScene, vilaCamera, vilaHotspots=[], vilaHovered=null, vilaT=0, vilaRAF=null;

const VILA_LOCS = {
  praca:  {name:'PRAÇA',      sub:'o coração da vila',   daemons:['callum','silas','matteo','lara','selin','darian','theo','nora'], env:'conversas ao vento · a fonte nunca para'},
  casa:   {name:'SUA CASA',   sub:'seu refúgio',         daemons:['callum'], env:'luz aconchegante · memórias nas paredes'},
  taverna:{name:'TAVERNA',    sub:'barulho bom',         daemons:['matteo','callum'], env:'madeira escura · aroma de especiarias'},
  biblio: {name:'BIBLIOTECA', sub:'saber e silêncio',    daemons:['silas','darian'], env:'luz de manhã · prateleiras infinitas'},
  sanctu: {name:'SANTUÁRIO',  sub:'contemplação',        daemons:['theo','selin'], env:'velas ao fundo · silêncio que pesa bem'},
  jardim: {name:'JARDIM',     sub:'entre flores',        daemons:['lara','nora'], env:'terra molhada · borboletas de março'},
};

function initVila() {
  if(vilaInit) return;
  vilaInit = true;

  // Timeout de segurança — se Three.js não carregar em 5s, vai para 2D
  const timeout = setTimeout(() => {
    if(typeof THREE === 'undefined') buildVila2D();
  }, 5000);

  function tryLoad(urls, idx=0) {
    if(idx >= urls.length) { clearTimeout(timeout); buildVila2D(); return; }
    const script = document.createElement('script');
    script.src = urls[idx];
    script.onload = () => { clearTimeout(timeout); buildVila3D(); };
    script.onerror = () => tryLoad(urls, idx+1);
    document.head.appendChild(script);
  }

  tryLoad([
    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
    'https://unpkg.com/three@0.128.0/build/three.min.js',
    'https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'
  ]);
}

function buildVila3D() {
  const container = document.getElementById('view-vila');
  const canvas = document.getElementById('vila-canvas');
  const W = ()=> container.clientWidth;
  const H = ()=> container.clientHeight;

  vilaRenderer = new THREE.WebGLRenderer({canvas, antialias:true});
  vilaRenderer.setSize(W(), H());
  vilaRenderer.setPixelRatio(Math.min(devicePixelRatio,2));
  vilaRenderer.shadowMap.enabled = true;
  vilaRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
  vilaRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  vilaRenderer.toneMappingExposure = 1.1;

  vilaScene = new THREE.Scene();
  vilaScene.background = new THREE.Color(0x0a1a0a);
  vilaScene.fog = new THREE.FogExp2(0x0d1f0d, 0.025);

  const asp = W()/H();
  const fr = 9;
  vilaCamera = new THREE.OrthographicCamera(-fr*asp,fr*asp,fr,-fr,0.1,100);
  vilaCamera.position.set(14,14,14);
  vilaCamera.lookAt(0,0,0);

  // Luzes
  vilaScene.add(new THREE.AmbientLight(0x1a2f1a, 0.7));
  const sun = new THREE.DirectionalLight(0xfff4d0, 1.4);
  sun.position.set(8,16,6); sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);
  ['left','right','top','bottom'].forEach((s,i)=>sun.shadow.camera[s]=[-16,16,16,-16][i]);
  sun.shadow.bias=-0.001; vilaScene.add(sun);
  vilaScene.add(Object.assign(new THREE.DirectionalLight(0x2040a0,0.3),{position:{set:()=>{}}}) );
  const fl = new THREE.DirectionalLight(0x2040a0,0.3); fl.position.set(-6,4,-4); vilaScene.add(fl);

  const M=(c,r=.85,m=0)=>new THREE.MeshStandardMaterial({color:c,roughness:r,metalness:m});
  const box=(w,h,d,mat,x,y,z)=>{const ms=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);ms.position.set(x,y,z);ms.castShadow=ms.receiveShadow=true;vilaScene.add(ms);return ms;};
  const cyl=(rt,rb,h,s,mat,x,y,z)=>{const ms=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,s),mat);ms.position.set(x,y,z);ms.castShadow=ms.receiveShadow=true;vilaScene.add(ms);return ms;};
  const cone=(r,h,s,mat,x,y,z,ry=0)=>{const ms=new THREE.Mesh(new THREE.ConeGeometry(r,h,s),mat);ms.position.set(x,y,z);ms.rotation.y=ry;ms.castShadow=ms.receiveShadow=true;vilaScene.add(ms);return ms;};
  const lp=(c,i,d,x,y,z)=>{const l=new THREE.PointLight(c,i,d);l.position.set(x,y,z);vilaScene.add(l);};

  // Chão
  const gnd=new THREE.Mesh(new THREE.PlaneGeometry(22,22),M(0x1a3012,.95));
  gnd.rotation.x=-Math.PI/2; gnd.receiveShadow=true; vilaScene.add(gnd);

  // Caminhos
  const pm=M(0x3a2e1e,.98);
  [[-1.5,0,0],[1.5,0,0],[0,0,-1.5],[0,0,1.5],[0,0,0],[-1.5,0,-1.5],[-1.5,0,1.5],[1.5,0,-1.5],[1.5,0,1.5]].forEach(([x,,z])=>{
    const p=new THREE.Mesh(new THREE.BoxGeometry(2.8,.06,2.8),pm);p.position.set(x,.03,z);p.receiveShadow=true;vilaScene.add(p);
  });

  // Água
  const wm=M(0x1a4060,.1,.3); wm.transparent=true; wm.opacity=.85;
  const w1=new THREE.Mesh(new THREE.PlaneGeometry(3,22),wm); w1.rotation.x=-Math.PI/2; w1.position.set(-8.5,.05,0); vilaScene.add(w1);
  const w2=new THREE.Mesh(new THREE.PlaneGeometry(22,3),wm.clone()); w2.rotation.x=-Math.PI/2; w2.position.set(0,.05,-8.5); vilaScene.add(w2);

  // SUA CASA
  box(2.4,1.6,2.4,M(0x5a3828),-5,.8,-5);
  cone(1.8,1.4,4,M(0x8a3020),-5,2.2,-5,Math.PI/4);
  lp(0xffcc44,.6,2.5,-5,1,-4.2);
  addVilaSpot(-5,-5,'casa');

  // TAVERNA
  box(2.8,2,2.8,M(0x5a3010),-3.5,1,-6);
  cone(2,1.4,4,M(0x8a4820),-3.5,2.7,-6,Math.PI/4);
  lp(0xff8822,.5,3,-3.5,2.5,-5);
  addVilaSpot(-3.5,-6,'taverna');

  // BIBLIOTECA
  box(3,2.2,2.6,M(0x6a6040),4.5,1.1,-5.5);
  box(3.4,.2,3,M(0x5a5030),4.5,2.32,-5.5);
  cyl(.12,.12,2.2,8,M(0x7a7040),3.2,1.1,-4.2);
  cyl(.12,.12,2.2,8,M(0x7a7040),5.8,1.1,-4.2);
  lp(0xffe0a0,.4,3,4.5,1,-5.5);
  addVilaSpot(4.5,-5.5,'biblio');

  // SANTUÁRIO
  box(2.4,2.6,3,M(0x8a8a9a),-5.5,1.3,3.5);
  box(.7,4.5,.7,M(0x7a7a8a),-5.5,2.25,3.5);
  box(.08,.6,.08,M(0xd0d0e0),-5.5,4.8,3.5);
  box(.4,.08,.08,M(0xd0d0e0),-5.5,4.6,3.5);
  lp(0xa0a0ff,.5,4,-5.5,1.5,3.5);
  addVilaSpot(-5.5,3.5,'sanctu');

  // JARDIM
  const gp=new THREE.Mesh(new THREE.BoxGeometry(3.5,.1,3.5),M(0x1a5012));
  gp.position.set(5,.05,5); gp.receiveShadow=true; vilaScene.add(gp);
  [[0xff7070],[0xffcc44],[0xff90cc],[0x80ffcc]].forEach(([c],i)=>{
    const a=i/4*Math.PI*2;
    const fl=new THREE.Mesh(new THREE.SphereGeometry(.15,6,6),M(c,.7));
    fl.position.set(5+Math.cos(a)*.9,.3,5+Math.sin(a)*.9); fl.castShadow=true; vilaScene.add(fl);
  });
  addVilaSpot(5,5,'jardim');

  // PRAÇA CENTRAL
  const pfm=new THREE.Mesh(new THREE.CylinderGeometry(1.2,1.2,.15,12),M(0x4a4030));
  pfm.position.set(0,.15,0); pfm.receiveShadow=true; vilaScene.add(pfm);
  cyl(.5,.6,.4,12,M(0x5a5a6a),0,.4,0);
  cyl(.15,.15,.8,8,M(0x6a6a7a),0,.7,0);
  [[1.4,1.4],[1.4,-1.4],[-1.4,1.4],[-1.4,-1.4]].forEach(([x,z])=>{
    cyl(.04,.04,1.4,6,M(0x3a2a10),x,.7,z);
    lp(0xffdd66,.8,3.5,x,1.5,z);
  });
  addVilaSpot(0,0,'praca');

  // ÁRVORES
  function makeTree(x,z,s=1){
    cyl(.06*s,.09*s,1.2*s,6,M(0x3a2010),x,.6*s,z);
    cyl(.5*s,.7*s,.7*s,8,M(0x1a5010),x,1.1*s,z);
    cyl(.4*s,.55*s,.65*s,8,M(0x226015),x,1.6*s,z);
    cone(.22*s,.5*s,6,M(0x3a9020),x,2.5*s,z);
  }
  [[-7,-7],[-7,7],[7,-7],[7,7],[-4,-8],[-8,-3],[-8,3],[-4,8],[4,-8],[4,8],[8,-3],[8,3]].forEach(([x,z],i)=>makeTree(x,z,.8+i%3*.15));

  // Rings
  vilaHotspots.forEach(h=>{
    const g=new THREE.RingGeometry(.3,.48,16);
    const mat=new THREE.MeshBasicMaterial({color:0x60dd30,side:THREE.DoubleSide,transparent:true,opacity:.7});
    const ring=new THREE.Mesh(g,mat); ring.rotation.x=-Math.PI/2;
    ring.position.set(h.x,.2,h.z); vilaScene.add(ring);
    h.ring=ring; h.ringMat=mat;
  });

  // Mouse
  canvas.addEventListener('mousemove', e=>{
    const r=canvas.getBoundingClientRect();
    const mx=(e.clientX-r.left)/r.width*2-1;
    const my=-((e.clientY-r.top)/r.height)*2+1;
    let found=null;
    vilaHotspots.forEach(h=>{
      const v=new THREE.Vector3(h.x,.5,h.z).project(vilaCamera);
      if(Math.hypot(v.x-mx,v.y-my)<.09) found=h;
    });
    vilaHovered=found;
    const tip=document.getElementById('vila-tip');
    if(found){
      const loc=VILA_LOCS[found.key];
      document.getElementById('vila-tip-name').textContent=loc.name;
      document.getElementById('vila-tip-d').textContent=(loc.daemons||[]).map(id=>DAEMONS[id]?.nome||id).join(' · ');
      tip.style.display='block';
      tip.style.left=Math.min(e.clientX-r.left+14,r.width-180)+'px';
      tip.style.top=Math.max(e.clientY-r.top-60,8)+'px';
      canvas.style.cursor='pointer';
    } else { tip.style.display='none'; canvas.style.cursor='default'; }
  });
  canvas.addEventListener('click',()=>{ if(vilaHovered) vilaOpenLoc(vilaHovered.key); });

  document.getElementById('vila-load').style.display='none';

  // Animate
  function animate(){
    vilaRAF=requestAnimationFrame(animate);
    vilaT+=.016;
    vilaHotspots.forEach((h,i)=>{
      const s=1+Math.sin(vilaT*2+i)*.15;
      h.ring.scale.set(s,1,s);
      h.ringMat.opacity=vilaHovered===h?.95:.5+Math.sin(vilaT*1.5+i)*.25;
      h.ringMat.color.setHSL(.3,.8,vilaHovered===h?.65:.45);
      h.ring.position.y=.2+Math.sin(vilaT+i)*.06;
    });
    vilaRenderer.render(vilaScene,vilaCamera);
  }
  animate();
}

function addVilaSpot(x,z,key){ vilaHotspots.push({x,z,key}); }

function buildVila2D() {
  document.getElementById('vila-load').style.display='none';
  const canvas=document.getElementById('vila-canvas');
  const W=canvas.offsetWidth||900, H=canvas.offsetHeight||600;
  canvas.width=W; canvas.height=H;
  const ctx=canvas.getContext('2d');

  // Hotspots 2D
  const spots2d=[
    {key:'praca',   label:'PRAÇA',      x:.5,  y:.45, c:'#8bc34a'},
    {key:'casa',    label:'SUA CASA',   x:.2,  y:.22, c:'#d4b050'},
    {key:'taverna', label:'TAVERNA',    x:.28, y:.55, c:'#f44336'},
    {key:'biblio',  label:'BIBLIOTECA', x:.72, y:.25, c:'#ff9800'},
    {key:'sanctu',  label:'SANTUÁRIO',  x:.22, y:.72, c:'#9c27b0'},
    {key:'jardim',  label:'JARDIM',     x:.72, y:.68, c:'#4caf50'},
  ];

  function draw() {
    ctx.clearRect(0,0,W,H);
    // fundo
    const bg=ctx.createRadialGradient(W/2,H/2,50,W/2,H/2,W*.7);
    bg.addColorStop(0,'#1a2f1a'); bg.addColorStop(1,'#0a1a0a');
    ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);

    // grid isométrico
    ctx.strokeStyle='rgba(100,180,60,.06)'; ctx.lineWidth=1;
    for(let i=0;i<20;i++){
      ctx.beginPath(); ctx.moveTo(i*(W/20),0); ctx.lineTo(0,i*(H/20)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(W,i*(H/20)); ctx.lineTo(i*(W/20),H); ctx.stroke();
    }

    // caminhos
    ctx.strokeStyle='rgba(90,70,40,.5)'; ctx.lineWidth=12; ctx.lineCap='round';
    const cx=W*.5, cy=H*.45;
    [[W*.2,H*.22],[W*.28,H*.55],[W*.72,H*.25],[W*.22,H*.72],[W*.72,H*.68]].forEach(([x,y])=>{
      ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y); ctx.stroke();
    });

    // spots
    const t=Date.now()/1000;
    spots2d.forEach((s,i)=>{
      const x=s.x*W, y=s.y*H;
      const pulse=1+Math.sin(t*2+i)*.12;

      // glow
      const gl=ctx.createRadialGradient(x,y,5,x,y,45*pulse);
      gl.addColorStop(0,s.c+'44'); gl.addColorStop(1,'transparent');
      ctx.fillStyle=gl; ctx.beginPath(); ctx.arc(x,y,45*pulse,0,Math.PI*2); ctx.fill();

      // círculo
      ctx.beginPath(); ctx.arc(x,y,22,0,Math.PI*2);
      ctx.fillStyle=s.c+'22'; ctx.fill();
      ctx.strokeStyle=s.c; ctx.lineWidth=2; ctx.stroke();

      // anel pulsante
      ctx.beginPath(); ctx.arc(x,y,28*pulse,0,Math.PI*2);
      ctx.strokeStyle=s.c+'55'; ctx.lineWidth=1.5; ctx.stroke();

      // label
      ctx.fillStyle='rgba(255,255,255,.85)';
      ctx.font='bold 10px monospace'; ctx.textAlign='center';
      ctx.fillText(s.label,x,y-32);

      // daemons pequenos
      const loc=VILA_LOCS[s.key];
      if(loc){
        const names=(loc.daemons||[]).map(id=>DAEMONS[id]?.nome||id).join(' · ');
        ctx.fillStyle='rgba(255,255,255,.35)';
        ctx.font='9px monospace';
        ctx.fillText(names,x,y-20);
      }
    });

    requestAnimationFrame(draw);
  }
  draw();

  // Interação 2D
  canvas.addEventListener('mousemove', e=>{
    const r=canvas.getBoundingClientRect();
    const mx=(e.clientX-r.left)*(W/r.width);
    const my=(e.clientY-r.top)*(H/r.height);
    const found=spots2d.find(s=>Math.hypot(mx-s.x*W,my-s.y*H)<30);
    canvas.style.cursor=found?'pointer':'default';
    const tip=document.getElementById('vila-tip');
    if(found){
      const loc=VILA_LOCS[found.key];
      document.getElementById('vila-tip-name').textContent=loc.name;
      document.getElementById('vila-tip-d').textContent=(loc.daemons||[]).map(id=>DAEMONS[id]?.nome||id).join(' · ');
      tip.style.display='block';
      tip.style.left=Math.min(e.clientX-r.left+14,r.width-180)+'px';
      tip.style.top=Math.max(e.clientY-r.top-60,8)+'px';
    } else { tip.style.display='none'; }
  });
  canvas.addEventListener('click', e=>{
    const r=canvas.getBoundingClientRect();
    const mx=(e.clientX-r.left)*(W/r.width);
    const my=(e.clientY-r.top)*(H/r.height);
    const found=spots2d.find(s=>Math.hypot(mx-s.x*W,my-s.y*H)<30);
    if(found) vilaOpenLoc(found.key);
  });
}

function vilaOpenLoc(key){
  const ov=document.getElementById('vila-ov');
  ov.style.opacity='1'; ov.style.pointerEvents='all';
  setTimeout(()=>{ vilaShowPanel(key); ov.style.opacity='0'; ov.style.pointerEvents='none'; },380);
}

function vilaShowPanel(key){
  const loc=VILA_LOCS[key];
  document.getElementById('vila-pt').textContent=loc.name;
  document.getElementById('vila-ps').textContent=loc.sub;
  document.getElementById('vila-pd').textContent=loc.daemons.map(id=>DAEMONS[id]?.nome||id).join(' · ');
  document.getElementById('vila-pe').textContent=loc.env;
  const pf=document.getElementById('vila-pf'); pf.innerHTML='';
  loc.daemons.forEach(id=>{
    const d=DAEMONS[id]; if(!d) return;
    const card=document.createElement('div');
    card.className='d-card'; card.style.cssText='flex-direction:column;align-items:center;padding:12px;gap:8px;cursor:pointer;min-width:80px';
    card.innerHTML=`<div class="d-av" style="width:44px;height:44px;background:${d.bg};color:${d.cor};font-size:18px">${d.ini}</div>
      <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:${d.cor}">${d.nome}</div>
      <div style="font-size:9px;color:var(--hint);text-align:center">${d.ess}</div>`;
    card.onclick=()=>{ vilaBack(); openSession(id); };
    pf.appendChild(card);
  });
  document.getElementById('vila-pan').style.display='flex';
}

function vilaBack(){
  const ov=document.getElementById('vila-ov');
  ov.style.opacity='1'; ov.style.pointerEvents='all';
  setTimeout(()=>{ document.getElementById('vila-pan').style.display='none'; ov.style.opacity='0'; ov.style.pointerEvents='none'; },320);
}

async function loadState() {
  try {
    const r = await fetch('/state');
    const d = await r.json();

    // Carrega daemons customizados
    const custom = d.custom_daemons || {};
    const overrides = d.name_overrides || {};

    Object.entries(custom).forEach(([id, daemon]) => {
      if (!DAEMONS[id]) {
        DAEMONS[id] = {
          nome: daemon.nome || daemon.name || id,
          ess:  daemon.essencia || daemon.ess || '',
          cor:  daemon.cor || 'rgba(200,200,200,.9)',
          bg:   daemon.bg || 'rgba(40,40,40,.9)',
          ini:  daemon.inicial || daemon.ini || id[0].toUpperCase(),
          threshold: 15
        };
      }
    });

    // Aplica overrides de nome
    Object.entries(overrides).forEach(([id, override]) => {
      if (DAEMONS[id]) {
        const nome = typeof override === 'string' ? override : override.nome;
        const ini  = typeof override === 'string' ? nome[0].toUpperCase() : (override.ini || nome[0].toUpperCase());
        DAEMONS[id].nome = nome;
        DAEMONS[id].ini  = ini;
      }
    });

    // Reconstrói sidebar e praça com os daemons carregados
    buildSidebar();
    buildPlazaControls();

    // Carrega histórico da praça
    const historico = d.historico || [];
    if (historico.length > 0) {
      document.getElementById('plaza-empty')?.remove();
      historico.forEach(m => {
        const isYou = m.who === 'você';
        // Encontra o id do daemon pelo nome
        const daemonId = isYou ? null : Object.keys(DAEMONS).find(id => DAEMONS[id].nome === m.who);
        if (isYou || daemonId) {
          plazaHistory.push({who: m.who, text: m.text});
          renderHistoryMsg(daemonId, m.who, m.text, isYou, m.ts);
        }
      });
      // Scrolla para o fim após carregar
      const plaza = document.getElementById('plaza');
      plaza.scrollTop = plaza.scrollHeight;
    }

  } catch(e) {
    console.log('Estado não carregado:', e);
  }
}

function renderHistoryMsg(daemonId, who, text, isYou, ts) {
  const plaza = document.getElementById('plaza');
  const d = daemonId ? DAEMONS[daemonId] : null;
  const row = document.createElement('div');
  row.className = 'msg' + (isYou ? ' you' : '');
  const displayTs = ts || '';

  if (isYou) {
    row.innerHTML = `
      <div class="msg-body">
        <div class="msg-who" style="color:var(--muted);text-align:right">você</div>
        <div class="msg-text">${text}</div>
        <div class="msg-ts" style="text-align:right">${displayTs}</div>
      </div>`;
  } else if (d) {
    row.innerHTML = `
      <div class="av" style="background:${d.bg};color:${d.cor};border-color:${d.cor.replace('.9','.3')}">${d.ini}</div>
      <div class="msg-body">
        <div class="msg-who" style="color:${d.cor}">${d.nome}</div>
        <div class="msg-text">${text}</div>
        <div class="msg-ts">${displayTs}</div>
      </div>
      <div class="reply-btn" onclick='setReply(${JSON.stringify({who: d.nome, text: text.slice(0,80)})})'>↩ responder</div>`;
  } else return; // daemon não encontrado, pula

  plaza.appendChild(row);
}

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

// ── WAKE SCREEN ──
let authMode = 'login';

// Stars para wake screen
(function(){
  const c = document.getElementById('wake-stars');
  function draw(){
    c.width=window.innerWidth; c.height=window.innerHeight;
    const ctx=c.getContext('2d');
    for(let i=0;i<200;i++){
      ctx.beginPath();
      ctx.arc(Math.random()*c.width,Math.random()*c.height,Math.random()*.8,0,Math.PI*2);
      ctx.fillStyle=`rgba(255,255,255,${Math.random()*.3+.02})`;
      ctx.fill();
    }
  }
  draw(); window.addEventListener('resize',draw);
})();

document.getElementById('wake-screen').onclick = function(e) {
  const card = document.getElementById('login-card');
  if (card.style.display !== 'none') return;
  document.getElementById('wake-content').style.animation = 'none';
  document.getElementById('wake-content').style.opacity = '0';
  setTimeout(() => {
    document.getElementById('wake-content').style.display = 'none';
    card.style.display = 'flex';
    document.getElementById('auth-email').focus();
    startLoginEyes();
  }, 300);
};

function switchAuth(mode) {
  authMode = mode;
  document.querySelectorAll('.ltab').forEach((t,i) => t.classList.toggle('active', (i===0&&mode==='login')||(i===1&&mode==='signup')));
  document.getElementById('signup-name-wrap').style.display = mode === 'signup' ? 'block' : 'none';
  document.getElementById('auth-btn-text').textContent = mode === 'login' ? 'entrar' : 'criar conta';
  document.getElementById('auth-error').textContent = '';
}

async function submitAuth() {
  const email = document.getElementById('auth-email').value.trim();
  const pass = document.getElementById('auth-pass').value;
  const name = document.getElementById('auth-name')?.value.trim() || '';
  const errEl = document.getElementById('auth-error');
  const btn = document.getElementById('auth-btn');
  const loading = document.getElementById('auth-loading');
  const btnText = document.getElementById('auth-btn-text');

  if (!email || !pass) { errEl.textContent = 'preencha email e senha'; return; }
  if (authMode === 'signup' && !name) { errEl.textContent = 'como você se chama?'; return; }
  if (pass.length < 4) { errEl.textContent = 'senha muito curta'; return; }

  btn.disabled = true;
  btnText.style.display = 'none';
  loading.style.display = 'inline';

  try {
    const r = await fetch('/auth/' + authMode, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email, password: pass, name})
    });
    const d = await r.json();

    if (d.error) {
      errEl.textContent = d.error;
      btn.disabled = false;
      btnText.style.display = 'inline';
      loading.style.display = 'none';
      return;
    }

    // Sucesso — guarda user e fecha wake screen
    window._user = d.user;
    document.getElementById('wake-screen').style.transition = 'opacity .5s';
    document.getElementById('wake-screen').style.opacity = '0';
    setTimeout(() => {
      document.getElementById('wake-screen').style.display = 'none';
      initAnima();
    }, 500);

  } catch(e) {
    errEl.textContent = 'erro de conexão';
    btn.disabled = false;
    btnText.style.display = 'inline';
    loading.style.display = 'none';
  }
}

function initAnima() {
  buildSidebar();
  buildPlazaControls();
  setTab('plaza');
  fetchNews();
  initPlazaScroll();
  loadState();
}

// Motor dos olhos do login card
let loginEyeActive = false;
let loginBlinkTimer = null;
let loginIsBlinking = false;

function startLoginEyes() {
  if (loginEyeActive) return;
  loginEyeActive = true;
  loginScheduleBlink();
  document.addEventListener('mousemove', loginTrackMouse);
}

function loginTrackMouse(e) {
  const card = document.getElementById('login-card');
  if (!card || card.style.display === 'none') return;
  const wrap = document.querySelector('.eye-s');
  if (!wrap) return;
  const rects = document.querySelectorAll('.eye-s');
  rects.forEach((eyeEl, i) => {
    const rect = eyeEl.getBoundingClientRect();
    const cx = rect.left + rect.width/2;
    const cy = rect.top + rect.height/2;
    const dx = Math.max(-3, Math.min(3, (e.clientX - cx) * .06));
    const dy = Math.max(-2, Math.min(2, (e.clientY - cy) * .06));
    const pupil = eyeEl.querySelector('.pupil-s');
    if (pupil) pupil.style.transform = `translate(${dx}px, ${dy}px)`;
  });
}

function loginBlink() {
  if (loginIsBlinking) return;
  loginIsBlinking = true;
  document.querySelectorAll('.eye-s').forEach(eye => {
    eye.style.transform = 'scaleY(0.1)';
    eye.style.transition = 'transform .1s ease';
  });
  setTimeout(() => {
    document.querySelectorAll('.eye-s').forEach(eye => {
      eye.style.transform = 'scaleY(1)';
    });
    loginIsBlinking = false;
  }, 120);
}

function loginScheduleBlink() {
  if (!loginEyeActive) return;
  loginBlinkTimer = setTimeout(() => {
    loginBlink();
    loginScheduleBlink();
  }, 2000 + Math.random() * 3500);
}

// Verifica se já tem sessão ativa
(async function checkSession() {
  try {
    const r = await fetch('/auth/session');
    const d = await r.json();
    if (d.user) {
      window._user = d.user;
      document.getElementById('wake-screen').style.display = 'none';
      initAnima();
    } else {
      // Sem sessão — mostra wake screen e inicia olhos após tap
      startLoginEyes();
    }
  } catch(e) {
    startLoginEyes();
  }
})();
</script>
</body>
</html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    # ── AUTH ──
    def _data(self):
        return Path('/data') if Path('/data').exists() else Path(__file__).parent

    def load_users(self):
        p = self._data() / 'users.json'
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

    def save_users(self, users):
        p = self._data() / 'users.json'
        p.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding='utf-8')

    def load_sessions(self):
        p = self._data() / 'sessions.json'
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

    def save_sessions(self, sessions):
        p = self._data() / 'sessions.json'
        p.write_text(json.dumps(sessions, ensure_ascii=False), encoding='utf-8')

    def hash_pass(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def get_session_user(self):
        """Retorna user_id da sessão atual via cookie."""
        cookie = self.headers.get('Cookie', '')
        token = None
        for part in cookie.split(';'):
            part = part.strip()
            if part.startswith('anima_session='):
                token = part[len('anima_session='):]
                break
        if not token: return None
        sessions = self.load_sessions()
        session = sessions.get(token)
        if not session: return None
        # expira após 30 dias
        if time.time() - session.get('created', 0) > 30 * 86400:
            return None
        return session.get('user_id')

    def load_memory(self, user_id=None):
        # Memória da praça é compartilhada; memória do usuário é privada
        fname = f'memory_{user_id}.json' if user_id else 'plaza_memory.json'
        p = self._data() / fname
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
        return {"usuario": {}, "fatos_plaza": [], "historico": [], "sessoes": 0}

    def save_memory(self, mem, user_id=None):
        fname = f'memory_{user_id}.json' if user_id else 'plaza_memory.json'
        p = self._data() / fname
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
        if not p.exists(): return {}
        data = json.loads(p.read_text(encoding='utf-8'))
        # compatibilidade: converte formato antigo {id: nome_str} para {id: {nome, ini}}
        result = {}
        for k, v in data.items():
            if isinstance(v, str):
                result[k] = {'nome': v, 'ini': v[0].upper() if v else '?'}
            else:
                result[k] = v
        return result

    def save_name_overrides(self, overrides):
        _data_dir = Path('/data') if Path('/data').exists() else Path(__file__).parent
        p = _data_dir / 'name_overrides.json'
        p.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding='utf-8')

    def get_system_prompt(self, daemon_id):
        """Monta o system prompt para um daemon."""
        SOCIAL_BASE = "Você está numa conversa em grupo no mundo Anima. Fale como alguém numa conversa real — sem asteriscos, sem descrever gestos ou movimentos, só palavras faladas. Nunca seja confrontador ou agressivo. Máximo 2 frases."

        # Verifica se tem nome customizado
        overrides = self.load_name_overrides()
        _override = overrides.get(daemon_id, None)
        display_name = _override['nome'] if _override else None

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
        elif self.path == '/auth/session':
            user_id = self.get_session_user()
            if user_id:
                users = self.load_users()
                u = users.get(user_id, {})
                self._json({'user': {'id': user_id, 'name': u.get('name',''), 'email': u.get('email','')}})
            else:
                self._json({'user': None})
        elif self.path == '/state':
            # Retorna estado completo: daemons customizados + histórico da praça + usuário
            mem = self.load_memory()
            custom = self.load_daemons()
            overrides = self.load_name_overrides()
            # Histórico recente para exibir (últimas 30 mensagens)
            historico = mem.get('historico', [])[-30:]
            self._json({
                'custom_daemons': custom,
                'name_overrides': overrides,
                'historico': historico,
                'usuario': mem.get('usuario', {})
            })
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
        elif self.path == '/auth/login':
            email = body.get('email','').strip().lower()
            password = body.get('password','')
            users = self.load_users()
            # Encontra user por email
            user_id = None
            user = None
            for uid, u in users.items():
                if u.get('email','').lower() == email:
                    user_id = uid; user = u; break
            if not user:
                self._json({'error': 'email não encontrado'}); return
            if user.get('password') != self.hash_pass(password):
                self._json({'error': 'senha incorreta'}); return
            # Cria sessão
            token = secrets.token_urlsafe(32)
            sessions = self.load_sessions()
            sessions[token] = {'user_id': user_id, 'created': time.time()}
            self.save_sessions(sessions)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'anima_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000')
            self.end_headers()
            self.wfile.write(json.dumps({'user': {'id': user_id, 'name': user.get('name',''), 'email': email}}).encode())
            return

        elif self.path == '/auth/signup':
            email = body.get('email','').strip().lower()
            password = body.get('password','')
            name = body.get('name','').strip()
            if not email or not password or not name:
                self._json({'error': 'preencha todos os campos'}); return
            users = self.load_users()
            # Verifica se email já existe
            for u in users.values():
                if u.get('email','').lower() == email:
                    self._json({'error': 'email já cadastrado'}); return
            user_id = secrets.token_urlsafe(12)
            users[user_id] = {'email': email, 'password': self.hash_pass(password), 'name': name, 'created': time.time()}
            self.save_users(users)
            # Cria sessão
            token = secrets.token_urlsafe(32)
            sessions = self.load_sessions()
            sessions[token] = {'user_id': user_id, 'created': time.time()}
            self.save_sessions(sessions)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'anima_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000')
            self.end_headers()
            self.wfile.write(json.dumps({'user': {'id': user_id, 'name': name, 'email': email}}).encode())
            return

        elif self.path == '/daemon/register':
            self.save_daemon(body.get('id',''), body.get('daemon', {}))
            self._json({'ok': True})
        elif self.path == '/daemon/rename':
            daemon_id = body.get('id','')
            new_name = body.get('nome','').strip()
            new_ini = body.get('ini', new_name[0].upper() if new_name else '?')
            if daemon_id and new_name:
                # Salva override — vale para daemons base e customizados
                overrides = self.load_name_overrides()
                overrides[daemon_id] = {'nome': new_name, 'ini': new_ini}
                self.save_name_overrides(overrides)
                # Se for daemon customizado, atualiza também lá
                custom = self.load_daemons()
                if daemon_id in custom:
                    custom[daemon_id]['nome'] = new_name
                    custom[daemon_id]['inicial'] = new_ini
                    self.save_daemon(daemon_id, custom[daemon_id])
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
