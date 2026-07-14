import os
import socket
import json
from flask import Flask, jsonify, request, send_from_directory, render_template_string
from smtc_controller import SMTCController
from netease_watcher import NeteaseWatcherClient
from volume_controller import VolumeController

app = Flask(__name__, static_folder=None)
smtc = SMTCController()

_netease_watcher_host = os.environ.get("NETEASE_WATCHER_HOST", "127.0.0.1")
_netease_watcher_port = int(os.environ.get("NETEASE_WATCHER_PORT", "3574"))
netease_watcher = NeteaseWatcherClient(host=_netease_watcher_host, port=_netease_watcher_port)

volume_ctrl = VolumeController()

IS_NETEASE_CLOUD_MUSIC = "cloudmusic"


def is_netease_cloud_music():
    source = smtc.get_session_source().lower()
    return IS_NETEASE_CLOUD_MUSIC in source


def get_merged_status():
    status = smtc.get_status().copy()
    status["source"] = smtc.get_session_source()
    status["netease_watcher_active"] = False

    if is_netease_cloud_music():
        ncm_status = netease_watcher.get_status()
        if ncm_status:
            if ncm_status["duration"] > 0:
                status["duration"] = ncm_status["duration"]
            if ncm_status["position"] > 0 or status["position"] == 0:
                status["position"] = ncm_status["position"]
            if not status["title"] or status["title"] == "未检测到媒体播放":
                status["title"] = ncm_status["title"]
            if not status["artist"]:
                status["artist"] = ncm_status["artist"]
            if not status["album_title"]:
                status["album_title"] = ncm_status["album_title"]
            if ncm_status.get("thumbnail"):
                status["thumbnail"] = ncm_status["thumbnail"]
            if ncm_status.get("song_id"):
                status["song_id"] = ncm_status["song_id"]
            status["netease_watcher_active"] = True

    master_vol = volume_ctrl.get_master_volume()
    status["volume"] = master_vol.get("volume", 0)
    status["muted"] = master_vol.get("muted", False)
    status["volume_available"] = master_vol.get("available", False)

    source = status.get("source", "")
    if source:
        app_vol = volume_ctrl.get_app_volume(source)
        if app_vol:
            status["app_volume"] = app_vol.get("volume", 100)
            status["app_muted"] = app_vol.get("muted", False)

    return status

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#1a1a2e">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="SMTC">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="application-name" content="SMTC Player">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/svg+xml" href="/icon.svg">
    <link rel="apple-touch-icon" href="/icon-192.png">
    <title>SMTC Player</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #fff;
        }

        .container {
            width: 100%;
            max-width: 400px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 32px 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .album-art {
            width: 220px;
            height: 220px;
            margin: 0 auto 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            overflow: hidden;
            position: relative;
        }

        .album-art.has-cover {
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }

        .album-art.has-cover::after {
            content: '';
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0);
            transition: background 0.3s ease;
        }

        .album-art.playing {
            animation: rotate 20s linear infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .volume-container {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding: 0 8px;
        }

        .volume-icon {
            font-size: 20px;
            cursor: pointer;
            width: 32px;
            text-align: center;
            user-select: none;
            flex-shrink: 0;
        }

        .volume-slider {
            flex: 1;
            -webkit-appearance: none;
            appearance: none;
            height: 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.15);
            outline: none;
            cursor: pointer;
        }

        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.5);
            transition: transform 0.15s ease;
        }

        .volume-slider::-webkit-slider-thumb:active {
            transform: scale(1.2);
        }

        .volume-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.5);
        }

        .volume-value {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
            width: 36px;
            text-align: right;
            flex-shrink: 0;
        }

        .song-info {
            text-align: center;
            margin-bottom: 24px;
        }

        .song-title {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .song-artist {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.6);
        }

        .progress-container {
            margin-bottom: 24px;
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 8px;
            cursor: pointer;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 3px;
            width: 0%;
            transition: width 0.3s ease;
        }

        .time-info {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
        }

        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 24px;
            margin-bottom: 24px;
        }

        .control-btn {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #fff;
            cursor: pointer;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        .control-btn:active {
            transform: scale(0.95);
        }

        .control-btn.small {
            width: 56px;
            height: 56px;
            font-size: 24px;
        }

        .control-btn.large {
            width: 72px;
            height: 72px;
            font-size: 32px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .control-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .status-bar {
            text-align: center;
            padding-top: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .status-text {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ade80;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(26, 26, 46, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999;
        }

        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
    </div>

    <div class="container">
        <div class="album-art" id="albumArt">🎵</div>

        <div class="song-info">
            <div class="song-title" id="songTitle">加载中...</div>
            <div class="song-artist" id="songArtist">-</div>
        </div>

        <div class="progress-container">
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="time-info">
                <span id="currentTime">0:00</span>
                <span id="totalTime">0:00</span>
            </div>
        </div>

        <div class="controls">
            <button class="control-btn small" id="prevBtn" onclick="control('previous')">⏮</button>
            <button class="control-btn large" id="playPauseBtn" onclick="control('play_pause')">▶</button>
            <button class="control-btn small" id="nextBtn" onclick="control('next')">⏭</button>
        </div>

        <div class="volume-container">
            <span class="volume-icon" id="volumeIcon" onclick="toggleMute()">🔊</span>
            <input type="range" class="volume-slider" id="volumeSlider" min="0" max="100" value="50" step="1">
            <span class="volume-value" id="volumeValue">50%</span>
        </div>

        <div class="status-bar">
            <div class="status-text">
                <span class="status-dot"></span>
                <span id="statusText">已连接</span>
            </div>
        </div>
    </div>

    <script>
        let currentStatus = null;
        let pollInterval = null;
        let currentThumbnail = '';
        let volumeChanging = false;
        let volumeChangeTimer = null;

        function formatTime(seconds) {
            if (!seconds || seconds < 0) return '0:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }

        function updateAlbumArt(thumbnail) {
            const albumArt = document.getElementById('albumArt');
            if (thumbnail && thumbnail !== currentThumbnail) {
                currentThumbnail = thumbnail;
                albumArt.style.backgroundImage = `url('${thumbnail}')`;
                albumArt.classList.add('has-cover');
                albumArt.textContent = '';
            } else if (!thumbnail && currentThumbnail) {
                currentThumbnail = '';
                albumArt.style.backgroundImage = '';
                albumArt.classList.remove('has-cover');
                albumArt.textContent = '🎵';
            }
        }

        function updateVolumeUI(volume, muted) {
            const slider = document.getElementById('volumeSlider');
            const valueText = document.getElementById('volumeValue');
            const icon = document.getElementById('volumeIcon');

            if (!volumeChanging) {
                slider.value = Math.round(volume);
            }
            valueText.textContent = Math.round(volume) + '%';

            if (muted || volume === 0) {
                icon.textContent = '🔇';
            } else if (volume < 50) {
                icon.textContent = '🔉';
            } else {
                icon.textContent = '🔊';
            }
        }

        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateUI(data);
                document.getElementById('loadingOverlay').classList.add('hidden');
                document.getElementById('statusText').textContent = '已连接';
            } catch (e) {
                document.getElementById('statusText').textContent = '连接失败，正在重试...';
                document.getElementById('loadingOverlay').classList.remove('hidden');
            }
        }

        function updateUI(status) {
            currentStatus = status;

            document.getElementById('songTitle').textContent = status.title || '未知标题';
            document.getElementById('songArtist').textContent = status.artist || '未知艺术家';

            updateAlbumArt(status.thumbnail);

            const progressPercent = status.duration > 0 
                ? (status.position / status.duration) * 100 
                : 0;
            document.getElementById('progressFill').style.width = `${progressPercent}%`;

            document.getElementById('currentTime').textContent = formatTime(status.position);
            document.getElementById('totalTime').textContent = formatTime(status.duration);

            const playPauseBtn = document.getElementById('playPauseBtn');
            if (status.is_playing) {
                playPauseBtn.textContent = '⏸';
                document.getElementById('albumArt').classList.add('playing');
            } else {
                playPauseBtn.textContent = '▶';
                document.getElementById('albumArt').classList.remove('playing');
            }

            document.getElementById('prevBtn').disabled = !status.has_previous;
            document.getElementById('nextBtn').disabled = !status.has_next;

            if (status.volume_available !== false) {
                updateVolumeUI(status.volume || 0, status.muted || false);
            }
        }

        async function control(action) {
            try {
                const response = await fetch(`/api/${action}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                const data = await response.json();
                if (data.success) {
                    setTimeout(fetchStatus, 200);
                }
            } catch (e) {
                console.error('控制失败:', e);
            }
        }

        async function setVolume(volume) {
            try {
                const response = await fetch('/api/volume', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ volume: volume })
                });
                const data = await response.json();
                return data.success;
            } catch (e) {
                console.error('设置音量失败:', e);
                return false;
            }
        }

        async function toggleMute() {
            try {
                const response = await fetch('/api/volume/toggle_mute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.success) {
                    setTimeout(fetchStatus, 100);
                }
            } catch (e) {
                console.error('切换静音失败:', e);
            }
        }

        function initVolumeControl() {
            const slider = document.getElementById('volumeSlider');
            const valueText = document.getElementById('volumeValue');

            slider.addEventListener('input', () => {
                volumeChanging = true;
                const vol = parseInt(slider.value);
                valueText.textContent = vol + '%';

                const icon = document.getElementById('volumeIcon');
                if (vol === 0) {
                    icon.textContent = '🔇';
                } else if (vol < 50) {
                    icon.textContent = '🔉';
                } else {
                    icon.textContent = '🔊';
                }

                if (volumeChangeTimer) {
                    clearTimeout(volumeChangeTimer);
                }
                volumeChangeTimer = setTimeout(() => {
                    setVolume(vol);
                    volumeChanging = false;
                }, 150);
            });

            slider.addEventListener('change', () => {
                const vol = parseInt(slider.value);
                setVolume(vol);
                volumeChanging = false;
            });
        }

        function startPolling() {
            fetchStatus();
            pollInterval = setInterval(fetchStatus, 1000);
        }

        document.addEventListener('DOMContentLoaded', () => {
            initVolumeControl();
            startPolling();
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/service-worker.js').catch(() => {});
            }
        });
    </script>
</body>
</html>
"""


MANIFEST_JSON = {
    "name": "SMTC Player",
    "short_name": "SMTC",
    "description": "Windows媒体控制器 - 局域网遥控播放",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#1a1a2e",
    "theme_color": "#1a1a2e",
    "orientation": "portrait",
    "icons": [
        {
            "src": "/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}

SERVICE_WORKER_JS = r"""
const CACHE_NAME = 'smtc-player-v1';
const urlsToCache = ['/'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        caches.match(event.request).then((response) => {
            if (response) {
                fetch(event.request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, networkResponse.clone());
                        });
                    }
                }).catch(() => {});
                return response;
            }
            return fetch(event.request).then((networkResponse) => {
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                return networkResponse;
            }).catch(() => {
                return caches.match('/');
            });
        })
    );
});
"""

ICON_SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea"/>
      <stop offset="100%" style="stop-color:#764ba2"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <circle cx="256" cy="256" r="140" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="8"/>
  <circle cx="256" cy="256" r="50" fill="rgba(255,255,255,0.9)"/>
  <path d="M256 116 L256 206" stroke="rgba(255,255,255,0.9)" stroke-width="12" stroke-linecap="round"/>
</svg>'''

import base64
import struct
import zlib


def make_png_icon(size=192):
    svg_bytes = ICON_SVG.encode('utf-8')
    try:
        from PIL import Image
        import io
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = Image.ImageDraw(img)
    except ImportError:
        pass

    r1, g1, b1 = 102, 126, 234
    r2, g2, b2 = 118, 75, 162
    cx, cy = size // 2, size // 2
    outer_r = int(size * 0.45)
    inner_r = int(size * 0.16)
    line_len = int(size * 0.35)
    line_width = max(4, int(size * 0.04))
    ring_width = max(4, int(size * 0.03))

    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            bg_t = (x + y) / (2 * size)
            bg_t = max(0, min(1, bg_t))
            br = int(r1 + (r2 - r1) * bg_t)
            bg = int(g1 + (g2 - g1) * bg_t)
            bb = int(b1 + (b2 - b1) * bg_t)

            corner_r = size * 0.1875
            in_corner = True
            for cx_c, cy_c in [(corner_r, corner_r), (size - corner_r, corner_r),
                               (corner_r, size - corner_r), (size - corner_r, size - corner_r)]:
                dxc, dyc = x - cx_c, y - cy_c
                if (x < corner_r and y < corner_r and dxc * dxc + dyc * dyc > corner_r * corner_r):
                    in_corner = False
                if (x > size - corner_r and y < corner_r and dxc * dxc + dyc * dyc > corner_r * corner_r):
                    in_corner = False
                if (x < corner_r and y > size - corner_r and dxc * dxc + dyc * dyc > corner_r * corner_r):
                    in_corner = False
                if (x > size - corner_r and y > size - corner_r and dxc * dxc + dyc * dyc > corner_r * corner_r):
                    in_corner = False

            if not in_corner:
                raw.extend([0, 0, 0, 0])
                continue

            if outer_r - ring_width <= dist <= outer_r:
                alpha = 230
                raw.extend([255, 255, 255, alpha])
            elif dist <= inner_r:
                raw.extend([255, 255, 255, 230])
            elif abs(dx) <= line_width // 2 and y < cy and y > cy - line_len:
                raw.extend([255, 255, 255, 230])
            else:
                raw.extend([br, bg, bb, 255])

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw))
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')


PNG_192 = make_png_icon(192)
PNG_512 = make_png_icon(512)


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/manifest.json")
def manifest():
    return jsonify(MANIFEST_JSON)


@app.route("/service-worker.js")
def service_worker():
    return SERVICE_WORKER_JS, 200, {'Content-Type': 'application/javascript', 'Cache-Control': 'no-cache'}


@app.route("/icon.svg")
def icon_svg():
    return ICON_SVG, 200, {'Content-Type': 'image/svg+xml'}


@app.route("/icon-192.png")
def icon_192():
    return PNG_192, 200, {'Content-Type': 'image/png'}


@app.route("/icon-512.png")
def icon_512():
    return PNG_512, 200, {'Content-Type': 'image/png'}


@app.route("/api/status", methods=["GET"])
def get_status():
    status = get_merged_status()
    return jsonify(status)


@app.route("/api/play_pause", methods=["POST"])
def api_play_pause():
    success = smtc.play_pause()
    return jsonify({"success": success})


@app.route("/api/play", methods=["POST"])
def api_play():
    success = smtc.play()
    return jsonify({"success": success})


@app.route("/api/pause", methods=["POST"])
def api_pause():
    success = smtc.pause()
    return jsonify({"success": success})


@app.route("/api/next", methods=["POST"])
def api_next():
    success = smtc.next_track()
    return jsonify({"success": success})


@app.route("/api/previous", methods=["POST"])
def api_previous():
    success = smtc.previous_track()
    return jsonify({"success": success})


@app.route("/api/volume", methods=["GET"])
def get_volume():
    vol = volume_ctrl.get_master_volume()
    return jsonify(vol)


@app.route("/api/volume", methods=["POST"])
def set_volume():
    data = request.get_json(silent=True) or {}
    volume = data.get("volume")
    if volume is None:
        return jsonify({"success": False, "error": "缺少 volume 参数"}), 400
    try:
        volume = float(volume)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "volume 必须是数字"}), 400
    success = volume_ctrl.set_master_volume(volume)
    return jsonify({"success": success})


@app.route("/api/volume/toggle_mute", methods=["POST"])
def toggle_mute():
    success = volume_ctrl.toggle_mute()
    return jsonify({"success": success})


@app.route("/api/app_volume", methods=["GET"])
def get_app_volume():
    source = smtc.get_session_source()
    if not source:
        return jsonify({"available": False, "volume": 100, "muted": False})
    vol = volume_ctrl.get_app_volume(source)
    if vol:
        return jsonify(vol)
    return jsonify({"available": False, "volume": 100, "muted": False})


@app.route("/api/app_volume", methods=["POST"])
def set_app_volume():
    data = request.get_json(silent=True) or {}
    volume = data.get("volume")
    if volume is None:
        return jsonify({"success": False, "error": "缺少 volume 参数"}), 400
    source = smtc.get_session_source()
    if not source:
        return jsonify({"success": False, "error": "没有活动的媒体会话"}), 400
    try:
        volume = float(volume)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "volume 必须是数字"}), 400
    success = volume_ctrl.set_app_volume(source, volume)
    return jsonify({"success": success})


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8888

    print("=" * 60)
    print("  SMTC Player - 媒体控制器服务端")
    print("=" * 60)
    print(f"  本地访问: http://127.0.0.1:{port}")
    print(f"  局域网访问: http://{local_ip}:{port}")
    print(f"  SMTC可用: {'是' if smtc.available else '否 (模拟模式)'}")
    if netease_watcher.available:
        print(f"  网易云增强: 已启用 (netease-watcher)")
    else:
        print(f"  网易云增强: 未检测到 (可选)")
    print(f"  音量控制: {'是' if volume_ctrl.available else '否'}")
    print("=" * 60)
    print("  提示: 确保手机/设备与电脑在同一局域网")
    print("  网易云增强: 启动 netease-watcher 可获取精确进度和封面")
    print("=" * 60)

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
