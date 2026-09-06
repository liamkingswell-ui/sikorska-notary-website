"""Walk every text element on every page and check it against its real backdrop.

Backdrop resolution: climb ancestors until an opaque background-color is found.
If an ancestor carries a gradient background-image, every colour stop in it is
treated as a candidate backdrop and the worst case is reported. Semi-transparent
backgrounds are composited over whatever is behind them.
"""
import json, subprocess, time, urllib.request, socket, websocket, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                         f"--remote-debugging-port={port}", "--remote-allow-origins=*", "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)
def cdp(ws, m, pr=None, _i=[0]):
    _i[0] += 1; ws.send(json.dumps({"id": _i[0], "method": m, "params": pr or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == _i[0]: return r
t = [x for x in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json")) if x["type"] == "page"][0]
ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=90, max_size=200_000_000)
cdp(ws, "Page.enable"); cdp(ws, "Runtime.enable")
cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})

CHECK = r"""
(() => {
  const rgb = s => { const m = (s||'').match(/[\d.]+/g); return m ? m.slice(0,4).map(Number) : null; };
  const lum = c => { const v = c.slice(0,3).map(x => { x/=255; return x<=0.03928 ? x/12.92 : Math.pow((x+0.055)/1.055, 2.4); });
                     return 0.2126*v[0] + 0.7152*v[1] + 0.0722*v[2]; };
  const ratio = (a,b) => { const L1=lum(a), L2=lum(b); return (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05); };
  const over = (fg, bg) => { const a = fg.length>3 ? fg[3] : 1;
                             return [0,1,2].map(i => Math.round(fg[i]*a + bg[i]*(1-a))); };

  // every colour stop declared in a gradient, as candidate backdrops
  const stops = img => {
    const out = [];
    (img.match(/rgba?\([^)]+\)/g) || []).forEach(c => { const p = rgb(c); if (p && (p.length<4 || p[3] > .5)) out.push(p); });
    return out;
  };

  const backdrops = (el, skipSelf) => {
    let node = skipSelf ? el.parentElement : el;
    const layers = [];
    while (node) {
      const cs = getComputedStyle(node);
      const bi = cs.backgroundImage;
      if (bi && bi !== 'none' && bi.indexOf('gradient') !== -1) {
        const st = stops(bi);
        if (st.length) { layers.push(st); }
      }
      const bc = rgb(cs.backgroundColor);
      if (bc && (bc.length < 4 || bc[3] > 0)) {
        layers.push([bc]);
        if (bc.length < 4 || bc[3] >= 1) break;
      }
      node = node.parentElement;
    }
    // resolve from the deepest opaque layer outward
    let cands = [[255,255,255]];
    for (let i = layers.length - 1; i >= 0; i--) {
      const next = [];
      layers[i].forEach(l => cands.forEach(b => next.push(over(l, b))));
      cands = next.slice(0, 12);
    }
    return cands;
  };

  const out = [];
  document.querySelectorAll('body *').forEach(el => {
    // only elements holding their own visible text
    const own = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(' ');
    if (!own) return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.opacity === '0') return;
    if (el.closest('.visually-hidden, .skip-link')) return;
    const fg = rgb(cs.color); if (!fg) return;
    const size = parseFloat(cs.fontSize);
    const weight = parseInt(cs.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3.0 : 4.5;
    let worst = 99, worstBg = null;
    backdrops(el, false).forEach(bg => { const cr = ratio(fg, bg); if (cr < worst) { worst = cr; worstBg = bg; } });
    if (worst < need) {
      out.push([el.tagName.toLowerCase() + '.' + (el.className||'').toString().split(' ').slice(0,2).join('.'),
                'rgb(' + fg.slice(0,3) + ')', 'on rgb(' + worstBg + ')',
                worst.toFixed(2) + ':1 need ' + need, Math.round(size) + 'px', own.slice(0, 34)]);
    }
  });
  return JSON.stringify(out);
})()
"""

PAGES = ["index.html", "notarial-service.html", "for-business.html",
         "apostille-and-legalisation.html", "will-writing-service.html",
         "fees-and-disbursements.html", "legal-and-regulatory.html",
         "contact.html", "polski.html", "practice.html", "404.html"]

total = 0
for page in PAGES:
    cdp(ws, "Page.navigate", {"url": "http://localhost:8123/" + page})
    for _ in range(40):
        time.sleep(0.3)
        r = cdp(ws, "Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True})
        if r["result"]["result"].get("value") == "complete": break
    time.sleep(0.6)
    cdp(ws, "Runtime.evaluate", {"expression":
        "document.querySelectorAll('.reveal').forEach(e=>e.setAttribute('data-shown','true'));"})
    r = cdp(ws, "Runtime.evaluate", {"expression": CHECK, "returnByValue": True})
    rows = json.loads(r["result"]["result"]["value"])
    # de-duplicate identical selector+colour pairs
    seen, uniq = set(), []
    for row in rows:
        k = (row[0], row[1], row[2])
        if k in seen: continue
        seen.add(k); uniq.append(row)
    if uniq:
        print("\n== " + page)
        for row in uniq:
            print("   %-30s %-16s %-20s %-18s %-6s %s" % tuple(row))
        total += len(uniq)

print("\n%d distinct contrast failures" % total if total else "\nNO CONTRAST FAILURES")
ws.close(); proc.terminate()
