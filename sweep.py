"""Functional sweep: drive every interactive control on every page, desktop and mobile.

Not a static check. This clicks things and asserts what actually happened.
"""
import json, subprocess, time, urllib.request, socket, websocket, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                         f"--remote-debugging-port={port}", "--remote-allow-origins=*", "about:blank"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

_console = []
def cdp(ws, m, pr=None, _i=[0]):
    _i[0] += 1
    ws.send(json.dumps({"id": _i[0], "method": m, "params": pr or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("method") == "Runtime.consoleAPICalled":
            if msg["params"].get("type") in ("error", "warning"):
                _console.append(str(msg["params"].get("args"))[:120])
        if msg.get("method") == "Runtime.exceptionThrown":
            _console.append("EXCEPTION " + str(msg["params"])[:160])
        if msg.get("id") == _i[0]:
            return msg

t = [x for x in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json")) if x["type"] == "page"][0]
ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=90, max_size=200_000_000)
cdp(ws, "Page.enable"); cdp(ws, "Runtime.enable")

PAGES = ["index.html", "notarial-service.html", "for-business.html",
         "apostille-and-legalisation.html", "will-writing-service.html",
         "fees-and-disbursements.html", "legal-and-regulatory.html",
         "contact.html", "polski.html", "practice.html", "404.html"]

# ---- preflight: refuse to run against a dead server ------------------------
# A previous run silently "passed" because the local server had stopped and every
# selector matched nothing. Fail loudly instead.
try:
    _probe = urllib.request.urlopen("http://localhost:8123/index.html", timeout=5).read().decode("utf-8", "replace")
except Exception as e:
    sys.exit("PREFLIGHT FAILED: local server not reachable on :8123 (%s)" % e)
if 'class="nav"' not in _probe:
    sys.exit("PREFLIGHT FAILED: served page does not contain the nav, wrong server or wrong directory")
print("preflight ok: server serving the real site")

fails, checks = [], 0
def check(page, w, name, ok, detail=""):
    global checks
    checks += 1
    if not ok:
        fails.append("%-32s %4d  %-26s %s" % (page, w, name, detail))

def ev(expr):
    r = cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": False})
    res = r.get("result", {}).get("result", {})
    if r.get("result", {}).get("exceptionDetails"):
        return {"__err": str(r["result"]["exceptionDetails"])[:120]}
    return res.get("value")

def load(page, w):
    cdp(ws, "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": 900, "deviceScaleFactor": 1, "mobile": w < 900})
    cdp(ws, "Page.navigate", {"url": "http://localhost:8123/" + page})
    for _ in range(50):
        time.sleep(0.25)
        if ev("document.readyState") == "complete": break
    time.sleep(0.5)

for w in (1280, 390):
    for page in PAGES:
        _console.clear()
        load(page, w)

        # ---- every internal link points at something that exists -------------
        bad_links = ev("""
        (() => {
          const out = [];
          document.querySelectorAll('a[href]').forEach(a => {
            const h = a.getAttribute('href');
            if (!h || /^(https?:|mailto:|tel:)/.test(h)) return;
            if (h.startsWith('#')) {
              if (h.length > 1 && !document.querySelector(h.replace(/([^\\\\w-])/g,'\\\\$1'))) {
                if (!document.getElementById(h.slice(1))) out.push('dead anchor ' + h);
              }
              return;
            }
            const frag = h.split('#')[1];
            if (frag && h.split('#')[0] === '') { if (!document.getElementById(frag)) out.push('dead anchor ' + h); }
          });
          return out;
        })()""")
        check(page, w, "in-page anchors", not bad_links, str(bad_links))

        # ---- no dead-end links with empty or placeholder hrefs ---------------
        placeholders = ev("""[...document.querySelectorAll('a[href="#"], a[href=""], a:not([href])')]
            .filter(a => a.textContent.trim()).map(a => a.textContent.trim().slice(0,26))""")
        check(page, w, "no placeholder links", not placeholders, str(placeholders))

        # ---- exactly one visible primary nav OR burger, never both -----------
        navstate = ev("""
        (() => {
          const nav = document.querySelector('.nav');
          const burger = document.querySelector('.burger');
          const vis = e => e && getComputedStyle(e).display !== 'none' && e.offsetParent !== null;
          return { nav: vis(nav), burger: vis(burger) };
        })()""")
        if navstate and not navstate.get("__err"):
            check(page, w, "one nav visible",
                  navstate["nav"] != navstate["burger"],
                  "nav=%s burger=%s" % (navstate["nav"], navstate["burger"]))

        if w >= 900:
            # ---- services dropdown: click opens, Escape closes ---------------
            r = ev("""
            (() => {
              const b = document.querySelector('.nav__toggle'); if (!b) return 'no toggle';
              const menu = document.getElementById(b.getAttribute('aria-controls'));
              b.click();
              const openA = b.getAttribute('aria-expanded') === 'true';
              const openV = getComputedStyle(menu).display !== 'none';
              document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
              const closedA = b.getAttribute('aria-expanded') === 'false';
              return {openA, openV, closedA};
            })()""")
            if isinstance(r, dict) and not r.get("__err"):
                check(page, w, "dropdown opens", r["openA"] and r["openV"], str(r))
                check(page, w, "Escape closes it", r["closedA"], str(r))
        else:
            # ---- burger opens the mobile nav ---------------------------------
            r = ev("""
            (() => {
              const b = document.querySelector('.burger'); if (!b) return 'no burger';
              const nav = document.getElementById('mobile-nav');
              b.click();
              const open = nav.getAttribute('data-open') === 'true';
              b.click();
              const closed = nav.getAttribute('data-open') !== 'true';
              return {open, closed};
            })()""")
            if isinstance(r, dict) and not r.get("__err"):
                check(page, w, "burger opens nav", r["open"], str(r))
                check(page, w, "burger closes nav", r["closed"], str(r))
            # ---- sticky call bar present on mobile ---------------------------
            cta = ev("(() => { const c = document.querySelector('.mobile-cta'); return !!c && getComputedStyle(c).display !== 'none'; })()")
            check(page, w, "mobile CTA visible", cta is True, str(cta))

        # ---- language toggle points somewhere real ---------------------------
        lang = ev("""(() => { const a = document.querySelector('.lang-toggle');
            return a ? {href:a.getAttribute('href'), text:a.textContent.trim()} : null; })()""")
        if lang and not lang.get("__err"):
            expect = "./" if page == "polski.html" else "polski.html"
            check(page, w, "language toggle", lang["href"] == expect,
                  "href=%s expected=%s" % (lang["href"], expect))

        # ---- FAQ accordions actually open ------------------------------------
        faq = ev("""
        (() => {
          const d = document.querySelector('.faq details'); if (!d) return 'none';
          d.querySelector('summary').click();
          const open = d.open;
          d.querySelector('summary').click();
          return {open, closed: !d.open};
        })()""")
        if isinstance(faq, dict) and not faq.get("__err"):
            check(page, w, "FAQ toggles", faq["open"] and faq["closed"], str(faq))

        # ---- reveal animation never leaves content invisible -----------------
        hidden = ev("""
        (() => {
          let n = 0;
          document.querySelectorAll('.reveal').forEach(e => {
            const cs = getComputedStyle(e);
            if (parseFloat(cs.opacity) < 0.05 && e.getBoundingClientRect().top < innerHeight) n++;
          });
          return n;
        })()""")
        check(page, w, "no stuck reveals", hidden == 0, "in-view but invisible: %s" % hidden)

        # ---- console clean ----------------------------------------------------
        time.sleep(0.2)
        check(page, w, "console clean", not _console, "; ".join(_console[:2]))

# ---- contact form behaviour, desktop only ---------------------------------
load("contact.html", 1280)
_console.clear()
r = ev("""
(() => {
  const form = document.getElementById('enquiry-form');
  const out = {};
  // business-only field hidden until "A business" is chosen
  const co = form.querySelector('[data-when="client_type:business"]');
  out.companyHiddenFirst = getComputedStyle(co).display === 'none';
  const biz = [...form.elements['client_type']].find(r => r.value === 'business');
  biz.checked = true; biz.dispatchEvent(new Event('change', {bubbles:true}));
  out.companyShown = getComputedStyle(co).display !== 'none';
  // empty submit must be blocked and must say something
  const ind = [...form.elements['client_type']].find(r => r.value === 'individual');
  ind.checked = true; ind.dispatchEvent(new Event('change', {bubbles:true}));
  form.elements['name'].value = '';
  form.requestSubmit();
  return out;
})()""")
time.sleep(0.6)
st = ev("(() => { const s = document.querySelector('.form-status'); return {state: s.getAttribute('data-state'), text: (s.textContent||'').slice(0,60)}; })()")
if isinstance(r, dict) and not r.get("__err"):
    check("contact.html", 1280, "business field hidden", r["companyHiddenFirst"], str(r))
    check("contact.html", 1280, "business field reveals", r["companyShown"], str(r))
if isinstance(st, dict) and "state" in st:
    check("contact.html", 1280, "guard blocks empty send", st["state"] == "error", str(st))
else:
    check("contact.html", 1280, "guard blocks empty send", False, "could not read status: " + str(st)[:100])

print("ran %d checks across %d pages x 2 viewports" % (checks, len(PAGES)))
if fails:
    print("\nFAILURES (%d):" % len(fails))
    for f in fails: print("  " + f)
else:
    print("\nALL PASS")
ws.close(); proc.terminate()
