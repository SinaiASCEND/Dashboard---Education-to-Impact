"""Make the live (Strategic Plan dashboard) versions of a working group's kickoff guides.

python3 kickoff_live_build.py <participant.html> <facilitator.html> <out_dir> [room] [folder] [group label] [participant artifact url]
writes <out_dir>/index.html (members, open) and <out_dir>/facilitator.html (code box, reveal buttons).
Defaults are the G3.1 kickoff (room g31-kickoff, folder kickoff/). G2.2:
  ... kickoff-g22 g22-kickoff kickoff-g22 "G2.2 Curriculum Gap Working Group" https://claude.ai/artifact/D1ApPwsH8yEjfnRj4DvB1P
The room must be listed in ROOMS in the Support site's api/live.js.
"""
import re, sys, os
P_IN, F_IN, OUT = sys.argv[1:4]
LIVE = 'https://ascend-support-dashboard.vercel.app/api/live'
ARGS = sys.argv[4:] + [None] * 4
ROOM = ARGS[0] or 'g31-kickoff'
PUBLIC = 'https://sinaiascend.github.io/Dashboard---Education-to-Impact/%s/' % (ARGS[1] or 'kickoff')
GROUP = ARGS[2] or 'G3.1 Emerging Topics Working Group'
PG_ART = ARGS[3] or 'https://claude.ai/artifact/WXHAsXH7RCunKq9Eob6BGq'
HUB = 'https://sinaiascend.github.io/'
# SHA-256 of the uppercased presenter codes (same hashes as the Support site's api/unlock.js)
HASHES = ["b9b2b6f01aa767c022763ca563e0882c08635da21f2519dc7b02564aaf0aa9ba",
          "a42b8352b4c79f604f3ca0f8c703cbd08f648e86099ec682ce98bd4a11286741"]

p = open(P_IN, encoding='utf-8').read()
f = open(F_IN, encoding='utf-8').read()
TOTAL = len(re.findall(r'<div class="step" id="slide-\d+">', p))

common_meta = '<meta name="robots" content="noindex, nofollow">\n'

# ---------------- members' page ----------------
p_css = """
.livepill{position:sticky;top:8px;z-index:20;display:flex;justify-content:center;margin:0 0 12px;pointer-events:none}
.livepill span{pointer-events:auto;background:#221F72;color:#fff;font-size:13px;font-weight:600;padding:6px 14px;border-radius:999px;box-shadow:0 4px 14px rgba(34,31,114,.25)}
.livepill span i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#2fd17a;margin-right:7px;vertical-align:1px}
.livepill.off span{background:#5d5f6b}.livepill.off span i{background:#c9cbd3}
body.live .step.locked{display:none}
body.live section.empty{display:none}
#comingup{display:none;text-align:center;color:#5d5f6b;font-size:14px;border:2px dashed #d5dbe8;border-radius:12px;padding:16px;margin:0 0 18px;background:#fff}
body.live #comingup{display:block}
body.live.allshown #comingup{display:none}
</style>"""
p = p.replace('</style>', p_css, 1)
p = p.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + common_meta, 1)
p = p.replace('<main>', '<main>\n<div class="livepill" id="livepill"><span><i></i><b id="livetext">Connecting to the meeting…</b></span></div>', 1)
p = p.replace('<h2 class="appx">Terms Used Today</h2>', '<div id="comingup">More slides appear here as the meeting moves on.</div>\n<h2 class="appx">Terms Used Today</h2>', 1)
p_js = """<script>
(function(){
  var LIVE=%r, ROOM=%r, TOTAL=%d;
  var steps=[].slice.call(document.querySelectorAll('.step[id^="slide-"]'));
  var sections=[].slice.call(document.querySelectorAll('main > section'));
  var pill=document.getElementById('livepill'), txt=document.getElementById('livetext');
  var cur=null, fails=0, live=true;
  document.body.classList.add('live');
  function apply(n, all){
    steps.forEach(function(s){ var k=+s.id.slice(6); s.classList.toggle('locked', !all && k>n); });
    sections.forEach(function(sec){ var any=sec.querySelector('.step:not(.locked)')||!sec.querySelector('.step'); sec.classList.toggle('empty', !any); });
    document.body.classList.toggle('allshown', !!all || n>=TOTAL);
    var last=null; steps.forEach(function(s){ if(!s.classList.contains('locked')) last=s; });
    var cu=document.getElementById('comingup'); if(last && cu){ last.parentNode.insertBefore(cu, last.nextSibling); }
    return last;
  }
  function showAll(msg){ live=false; document.body.classList.remove('live'); apply(TOTAL,true); pill.classList.add('off'); txt.textContent=msg; }
  apply(1,false);
  var waited=setTimeout(function(){ if(cur===null) showAll('Showing all slides'); }, 6000);
  function tick(){
    fetch(LIVE+'?room='+encodeURIComponent(ROOM),{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){
      if(!j||!j.ok) throw 0;
      fails=0; clearTimeout(waited);
      if(!live){ live=true; document.body.classList.add('live'); pill.classList.remove('off'); }
      var n=j.all?TOTAL:Math.max(1,Math.min(TOTAL,j.slide|0));
      var grew=(cur!==null && n>cur);
      var last=apply(n, !!j.all);
      txt.textContent=j.all?'Live · all slides shown':'Live · following the presenter · slide '+n+' of '+TOTAL;
      if(grew && last){ last.scrollIntoView({behavior:'smooth',block:'start'}); }
      cur=n;
    }).catch(function(){ fails++; if(fails>=3 || cur===null && fails>=2) showAll('Showing all slides'); });
  }
  tick(); setInterval(tick, 3000);
})();
</script>
</body>""" % (LIVE, ROOM, TOTAL)
p = p.replace('</body>', p_js, 1)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(p)

# ---------------- facilitator page ----------------
f_css = """
body.locked main{display:none}
#lock{display:none;max-width:460px;margin:12vh auto;padding:28px;background:#fff;border:1px solid #e3e4ea;border-radius:14px;font-family:'Inter Tight',system-ui,sans-serif}
body.locked #lock{display:block}
#lock h1{font-size:24px;margin:4px 0 12px}
#lock input{width:100%%;font:inherit;font-size:16px;padding:10px 12px;border:1px solid #cfd3de;border-radius:8px;margin:6px 0 10px}
#lock button{border:0;border-radius:999px;padding:10px 18px;background:#221F72;color:#fff;font:inherit;font-weight:700;cursor:pointer}
#lock .err{color:#c0392b;font-size:14px;min-height:20px;margin-top:8px}
#lock .own{font-size:13px;color:#5d5f6b;margin-top:14px}
.numrow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 6px}
.numrow .num{margin:0}
button.rv{border:0;border-radius:999px;padding:6px 14px;font:inherit;font-size:13px;font-weight:700;cursor:pointer;background:#D80B8C;color:#fff}
button.rv.done{background:#e9f8fb;color:#0089bd}
button.rv.here{background:#1d8a57;color:#fff}
button.rv:disabled{opacity:.6;cursor:wait}
#ctl{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:#221F72;color:#fff;padding:9px 14px;border-radius:0 0 12px 12px;margin:-22px 0 16px;box-shadow:0 4px 14px rgba(34,31,114,.25);font-size:14px}
#ctl b{margin-right:auto}
#ctl button{border:0;border-radius:999px;padding:6px 12px;font:inherit;font-size:13px;font-weight:700;cursor:pointer;background:rgba(255,255,255,.16);color:#fff}
#ctl button.go{background:#D80B8C}
#ctl .msg{flex-basis:100%%;font-size:12.5px;color:#ffd1ea;min-height:0}
</style>"""
f = f.replace('</style>', f_css.replace('%%', '%'), 1)
f = f.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + common_meta, 1)
f = f.replace('<body>', '''<body class="locked">
<div id="lock">
<div class="eyebrow">MD Strategic Plan · %s</div>
<h1>Kickoff facilitator guide</h1>
<form id="lockform"><label for="lockcode">Enter your access code</label>
<input id="lockcode" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false">
<button type="submit">Open</button><div class="err" id="lockerr"></div></form>
<p class="own">Office of Curricular Affairs, Icahn School of Medicine at Mount Sinai · <a href="%s">ASCEND Hub</a></p>
</div>''' % (GROUP, HUB), 1)
f = f.replace('<main>', '''<main>
<div id="ctl"><b id="ctltext">Members see: …</b><button type="button" id="cprev">&#8249; Back</button><button type="button" class="go" id="cnext">Next &#8250;</button><button type="button" id="call">Reveal all</button><button type="button" id="creset">Reset to slide 1</button><div class="msg" id="ctlmsg"></div></div>''', 1)
f = re.sub(r'<span class="num">Slide (\d+) of (\d+)</span>',
           lambda m: f'<div class="numrow"><span class="num">Slide {m.group(1)} of {m.group(2)}</span><button type="button" class="rv" data-n="{m.group(1)}">Reveal to members</button></div>', f)
f = f.replace(f'href="{PG_ART}"', f'href="{PUBLIC}"')
f = f.replace('&#128214; Participant guide</a>', "&#128214; Participant guide (members' link)</a>")
f_js = """<script>
(function(){
  var LIVE=%r, ROOM=%r, TOTAL=%d, HASHES=%r;
  var KEY=%r, code=null, cur=1, all=false;
  function sha(s){ return crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)).then(function(b){ return [].map.call(new Uint8Array(b),function(x){return ('0'+x.toString(16)).slice(-2);}).join(''); }); }
  function unlock(c){ return sha(c.trim().toUpperCase()).then(function(h){ if(HASHES.indexOf(h)<0) return false; code=c.trim(); try{sessionStorage.setItem(KEY,code);}catch(e){} document.body.classList.remove('locked'); start(); return true; }); }
  document.getElementById('lockform').addEventListener('submit',function(e){ e.preventDefault(); var v=document.getElementById('lockcode').value; unlock(v).then(function(ok){ if(!ok) document.getElementById('lockerr').textContent='That code isn\\u2019t recognized. Check with the Office of Curricular Affairs.'; }); });
  var saved=null; try{saved=sessionStorage.getItem(KEY);}catch(e){} if(saved) unlock(saved);
  var btns, txt, msg;
  function paint(){
    txt.textContent = all ? 'Members see: all '+TOTAL+' slides' : 'Members see: slides 1\\u2013'+cur+' of '+TOTAL;
    btns.forEach(function(b){ var n=+b.dataset.n; b.classList.remove('done','here');
      if(all || n<cur){ b.classList.add('done'); b.textContent='\\u2713 Revealed'; }
      else if(n===cur){ b.classList.add('here'); b.textContent='\\u25CF Members are here'; }
      else { b.textContent='Reveal to members'; } });
  }
  function load(){ return fetch(LIVE+'?room='+ROOM,{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){ if(j&&j.ok){ cur=j.slide; all=!!j.all; paint(); msg.textContent=''; } }).catch(function(){ msg.textContent='Cannot reach the live reveal; members see all slides until it is back.'; }); }
  function send(body){
    body.room=ROOM; body.code=code; btns.forEach(function(b){b.disabled=true;});
    return fetch(LIVE,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return [r.status,j];});})
      .then(function(x){ if(x[1]&&x[1].ok){ cur=x[1].slide; all=!!x[1].all; paint(); msg.textContent=''; } else { msg.textContent=(x[1]&&x[1].error)||'The reveal did not go through. Try again.'; } })
      .catch(function(){ msg.textContent='The reveal did not go through. Check the connection and try again.'; })
      .then(function(){ btns.forEach(function(b){b.disabled=false;}); });
  }
  function start(){
    btns=[].slice.call(document.querySelectorAll('button.rv')); txt=document.getElementById('ctltext'); msg=document.getElementById('ctlmsg');
    btns.forEach(function(b){ b.addEventListener('click',function(){ send({slide:+b.dataset.n}); }); });
    document.getElementById('cnext').addEventListener('click',function(){ send({slide:Math.min(TOTAL,(all?TOTAL:cur)+1)}); });
    document.getElementById('cprev').addEventListener('click',function(){ send({slide:Math.max(1,(all?TOTAL:cur)-1)}); });
    document.getElementById('call').addEventListener('click',function(){ send({all:true}); });
    document.getElementById('creset').addEventListener('click',function(){ send({slide:1}); });
    load(); setInterval(load, 5000);
  }
})();
</script>
</body>""" % (LIVE, ROOM, TOTAL, HASHES, ROOM.replace('-', '') + '-code')
f = f.replace('</body>', f_js, 1)
open(os.path.join(OUT, 'facilitator.html'), 'w', encoding='utf-8').write(f)
print('slides', TOTAL, 'reveal buttons', f.count('class="rv"'))
