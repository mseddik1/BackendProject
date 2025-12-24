import threading
import time
from fastapi import FastAPI, Depends, Request, HTTPException, status
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session

from src.app.db.base import get_db
from src.app.models import dbmodels
from src.app.schemas import schemas
from src.app.Limiter.limiter import setup_rate_limiting
from src.app.workers import jobs
from src.app.views.auth import auth_router
from src.app.views.users import users_router
from src.app.views.products import products_router
from src.app.services import services



app = FastAPI(title="Integration with SQL!")
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)

setup_rate_limiting(app)



@app.get("/")
def root() :
    return services.root()


@app.on_event("startup")
def start_background_workers():
    # Start the publish_product worker in a background thread
    t = threading.Thread(target=jobs.worker_loop, daemon=True)
    t.start()
    print("[MAIN] Background worker thread started")



@app.middleware("http")
async def log_requests(request: Request, call_next):

    start = time.time()

    ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
    ua = request.headers.get("user-agent", "")
    method = request.method
    path = request.url.path

    response = await call_next(request)

    duration_ms = int((time.time() - start) * 1000)

    # Replace print with proper logging / DB insert if you want
    # print({
    #     "ip": ip,
    #     "ua": ua,
    #     "method": method,
    #     "path": path,
    #     "status": response.status_code,
    #     "duration_ms": duration_ms,
    # })

    return response




# 1) GET /track  -> returns HTML + JS (runs in browser)
@app.get("/track", response_class=HTMLResponse)
async def track_page(request: Request, token: Optional[str] = None):
    # token can come from ?token=... in the email link
    token_js = token.replace('"', '\\"') if token else ""

    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Tracking…</title>
</head>
<body>
  <h3>Opening…</h3>

  <script>
  (async () => {{
    const url = new URL(window.location.href);
    const token = url.searchParams.get("token") || null;

    const correlationId =
      (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + "-" + Math.random());

    // Persistent browser id (best-effort)
    let clientId = null;
    try {{
      clientId = localStorage.getItem("client_id");
      if (!clientId) {{
        clientId = (crypto.randomUUID ? crypto.randomUUID() : correlationId);
        localStorage.setItem("client_id", clientId);
      }}
    }} catch (e) {{}}

    const safe = (fn, fallback = null) => {{ try {{ return fn(); }} catch {{ return fallback; }} }};
    const storageAvailable = (store) => {{
      try {{
        const k = "__t_" + Math.random();
        store.setItem(k, "1");
        store.removeItem(k);
        return true;
      }} catch {{ return false; }}
    }};

    // ===== UA Client Hints =====
    let uaHints = null;
    try {{
      if (navigator.userAgentData?.getHighEntropyValues) {{
        uaHints = await navigator.userAgentData.getHighEntropyValues([
          "architecture","bitness","model","platform","platformVersion",
          "uaFullVersion","fullVersionList","mobile","wow64"
        ]);
      }}
    }} catch (e) {{}}

    // ===== Permissions =====
    async function perm(name) {{
      try {{
        if (!navigator.permissions?.query) return null;
        const r = await navigator.permissions.query({{ name }});
        return r.state;
      }} catch {{ return null; }}
    }}
    const permissions = {{
      geolocation: await perm("geolocation"),
      notifications: await perm("notifications"),
      camera: await perm("camera"),
      microphone: await perm("microphone"),
      clipboard_read: await perm("clipboard-read"),
      clipboard_write: await perm("clipboard-write"),
    }};

    // ===== Network =====
    const conn = safe(() => navigator.connection || navigator.mozConnection || navigator.webkitConnection, null);
    const network = conn ? {{
      effective_type: conn.effectiveType ?? null,
      downlink_mbps: conn.downlink ?? null,
      rtt_ms: conn.rtt ?? null,
      save_data: !!conn.saveData,
      type: conn.type ?? null
    }} : null;

    // ===== Battery =====
    let battery = null;
    try {{
      if (navigator.getBattery) {{
        const b = await navigator.getBattery();
        battery = {{
          charging: b.charging ?? null,
          level: b.level ?? null,
          charging_time: b.chargingTime ?? null,
          discharging_time: b.dischargingTime ?? null
        }};
      }}
    }} catch (e) {{}}

    // ===== Media devices =====
    let media = null;
    try {{
      if (navigator.mediaDevices?.enumerateDevices) {{
        const devices = await navigator.mediaDevices.enumerateDevices();
        const counts = devices.reduce((acc, d) => {{
          acc[d.kind] = (acc[d.kind] || 0) + 1;
          return acc;
        }}, {{}});
        media = {{
          device_counts: counts,
          labels_available: devices.some(d => !!d.label)
        }};
      }}
    }} catch (e) {{}}

    // ===== WebGL =====
    function getWebglInfo() {{
      try {{
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
        if (!gl) return null;
        const dbg = gl.getExtension("WEBGL_debug_renderer_info");
        const vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : null;
        const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null;
        const version = gl.getParameter(gl.VERSION) || null;
        const shading = gl.getParameter(gl.SHADING_LANGUAGE_VERSION) || null;
        return {{ vendor, renderer, version, shading_language_version: shading }};
      }} catch {{ return null; }}
    }}
    const webgl = getWebglInfo();

    // ===== Capabilities =====
    const capabilities = {{
      webdriver: safe(() => navigator.webdriver, null),
      cookie_enabled: safe(() => navigator.cookieEnabled, null),
      do_not_track: safe(() => navigator.doNotTrack, null),
      on_line: safe(() => navigator.onLine, null),
      java_enabled: safe(() => (navigator.javaEnabled ? navigator.javaEnabled() : null), null),

      clipboard_api: !!navigator.clipboard,
      share_api: !!navigator.share,
      vibrate: !!navigator.vibrate,
      service_worker: "serviceWorker" in navigator,
      webassembly: typeof WebAssembly !== "undefined",
      webrtc: !!window.RTCPeerConnection,
      bluetooth: !!navigator.bluetooth,
      usb: !!navigator.usb,
      hid: !!navigator.hid,
      serial: !!navigator.serial,
      geolocation: !!navigator.geolocation,
      media_devices: !!navigator.mediaDevices,
      webgl: !!webgl,
    }};

    // ===== Storage =====
    const storage = {{
      local_storage: safe(() => storageAvailable(localStorage), false),
      session_storage: safe(() => storageAvailable(sessionStorage), false),
      indexed_db: !!window.indexedDB,
      cache_api: "caches" in window,
    }};

    // ===== Display =====
    const display = {{
      screen: {{
        width: safe(() => screen.width, null),
        height: safe(() => screen.height, null),
        avail_width: safe(() => screen.availWidth, null),
        avail_height: safe(() => screen.availHeight, null),
        color_depth: safe(() => screen.colorDepth, null),
        pixel_depth: safe(() => screen.pixelDepth, null),
        orientation: safe(() => screen.orientation?.type || null, null),
      }},
      viewport: {{
        inner_width: safe(() => window.innerWidth, null),
        inner_height: safe(() => window.innerHeight, null),
        outer_width: safe(() => window.outerWidth, null),
        outer_height: safe(() => window.outerHeight, null),
        device_pixel_ratio: safe(() => window.devicePixelRatio, null),
      }},
    }};

    // ===== Time =====
    const intl = safe(() => Intl.DateTimeFormat().resolvedOptions(), null);
    const time = {{
      client_time: new Date().toISOString(),
      timezone: intl?.timeZone ?? null,
      locale: intl?.locale ?? null,
      tz_offset_minutes: new Date().getTimezoneOffset(),
    }};

    // ===== Identity =====
    const identity = {{
      token_present: !!token,
      correlation_id: correlationId,
      client_id: clientId,
      user_agent: safe(() => navigator.userAgent, null),
      user_agent_hints: uaHints,
      languages: safe(() => navigator.languages || [navigator.language].filter(Boolean), null),
      language: safe(() => navigator.language, null),
      platform: safe(() => navigator.platform, null),
      max_touch_points: safe(() => navigator.maxTouchPoints, null),
      hardware_concurrency: safe(() => navigator.hardwareConcurrency, null),
      device_memory_gb: safe(() => navigator.deviceMemory, null),
    }};

    // ===== Page =====
    const page = {{
      href: location.href,
      origin: location.origin,
      path: location.pathname,
      query: location.search,
      referrer: document.referrer || null,
      visibility_state: document.visibilityState || null,
      has_focus: safe(() => document.hasFocus(), null),
      history_length: safe(() => history.length, null),
    }};

    const payload = {{
      event: "track_page_open",
      ...identity,
      time,
      page,
      display,
      permissions,
      storage,
      capabilities,
      network,
      battery,
      media,
      webgl
    }};

    try {{
      await fetch("/track", {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json",
          "X-Client-Id": clientId || "",
          "X-Correlation-Id": correlationId,
          "ngrok-skip-browser-warning": "true"
        }},
        body: JSON.stringify(payload),
        keepalive: true
      }});
    }} catch (e) {{}}

    document.body.innerHTML = "<h2>Tracked ✅</h2>";
  }})();
  </script>
</body>


</html>
"""


# 2) POST /track -> receives the JSON payload sent by the JS



@app.post("/track")
async def track_collect(payload: schemas.TrackPayload, request: Request, db:Session = Depends(get_db)):
    # server-side HTTP info (what JS cannot guarantee)
    xff = request.headers.get("x-forwarded-for")
    ip = (xff.split(",")[0].strip() if xff else request.client.host)

    record = {
        "ip": ip,
        "http_user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "client_payload": payload.model_dump(),
    }
    track = dbmodels.Tracking(
        ip = ip,
        user_agent = request.headers.get("user-agent"),
        path = request.url.path,
        payload = payload.model_dump()
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    # For demo: print to terminal (later you can store in DB)
    print(record)

    return JSONResponse({"ok": True})