let currentStatus = null;
let pollInterval = null;
let currentThumbnail = '';
let volumeChanging = false;
let volumeChangeTimer = null;
let searchTimer = null;
let currentPlaylistView = 'grid';
let ncmLoggedIn = false;
let ncmUserInfo = null;

function formatTime(seconds) {
    if (!seconds || seconds < 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(ms) {
    if (!ms) return '';
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
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
        albumArt.textContent = '\u{1F3B5}';
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
        icon.textContent = '\u{1F507}';
    } else if (volume < 50) {
        icon.textContent = '\u{1F509}';
    } else {
        icon.textContent = '\u{1F50A}';
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateUI(data);
        hideLoading();
        document.getElementById('statusText').textContent = '\u5DF2\u8FDE\u63A5';
    } catch (e) {
        document.getElementById('statusText').textContent = '\u8FDE\u63A5\u5931\u8D25\uFF0C\u6B63\u5728\u91CD\u8BD5...';
        showLoading();
    }
}

function updateUI(status) {
    currentStatus = status;
    document.getElementById('songTitle').textContent = status.title || '\u672A\u77E5\u6807\u9898';
    document.getElementById('songArtist').textContent = status.artist || '\u672A\u77E5\u827A\u672F\u5BB6';
    updateAlbumArt(status.thumbnail);

    const progressPercent = status.duration > 0
        ? (status.position / status.duration) * 100
        : 0;
    document.getElementById('progressFill').style.width = `${progressPercent}%`;
    document.getElementById('currentTime').textContent = formatTime(status.position);
    document.getElementById('totalTime').textContent = formatTime(status.duration);

    const playPauseBtn = document.getElementById('playPauseBtn');
    if (status.is_playing) {
        playPauseBtn.textContent = '\u23F8';
        document.getElementById('albumArt').classList.add('playing');
    } else {
        playPauseBtn.textContent = '\u25B6';
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
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            setTimeout(fetchStatus, 200);
        }
    } catch (e) {
        console.error('\u63A7\u5236\u5931\u8D25:', e);
    }
}

async function setVolume(volume) {
    try {
        const response = await fetch('/api/volume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ volume: volume })
        });
        return (await response.json()).success;
    } catch (e) {
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
        if (data.success) setTimeout(fetchStatus, 100);
    } catch (e) {}
}

function initVolumeControl() {
    const slider = document.getElementById('volumeSlider');
    const valueText = document.getElementById('volumeValue');
    slider.addEventListener('input', () => {
        volumeChanging = true;
        const vol = parseInt(slider.value);
        valueText.textContent = vol + '%';
        const icon = document.getElementById('volumeIcon');
        if (vol === 0) icon.textContent = '\u{1F507}';
        else if (vol < 50) icon.textContent = '\u{1F509}';
        else icon.textContent = '\u{1F50A}';
        if (volumeChangeTimer) clearTimeout(volumeChangeTimer);
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

// ========== Tab Switching ==========
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');

        if (btn.dataset.tab === 'playlist') {
            checkNcmStatus();
        }
    });
});

// ========== Search ==========
document.getElementById('searchInput').addEventListener('input', function() {
    const query = this.value.trim();
    if (searchTimer) clearTimeout(searchTimer);
    if (!query) {
        renderSearchResults([], 0);
        return;
    }
    searchTimer = setTimeout(() => searchSongs(query), 300);
});

async function searchSongs(keywords) {
    const container = document.getElementById('searchResults');
    container.innerHTML = '<div class="loading-dots">\u641C\u7D22\u4E2D...</div>';
    try {
        const resp = await fetch(`/api/ncm/search?q=${encodeURIComponent(keywords)}&limit=30`);
        const data = await resp.json();
        renderSearchResults(data.songs || [], data.songCount || 0);
    } catch (e) {
        container.innerHTML = '<div class="empty-state"><div class="icon">\u{1F61E}</div><div>\u641C\u7D22\u5931\u8D25\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5</div></div>';
    }
}

function renderSearchResults(songs, total) {
    const container = document.getElementById('searchResults');
    if (!songs.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">\u{1F50D}</div><div>\u672A\u627E\u5230\u76F8\u5173\u6B4C\u66F2</div></div>';
        return;
    }
    let html = '';
    songs.forEach((s, i) => {
        html += `<div class="song-item" onclick="playNcmSong(${s.id}, '${escapeHtml(s.name)}')">
            <div class="song-item-index">${i + 1}</div>
            <div class="song-item-cover" style="background-image:url('${s.cover || ''}')">${s.cover ? '' : '\u{1F3B5}'}</div>
            <div class="song-item-info">
                <div class="song-item-name">${escapeHtml(s.name)}</div>
                <div class="song-item-artist">${escapeHtml(s.artists)}${s.album ? ' \u00B7 ' + escapeHtml(s.album) : ''}</div>
            </div>
            <div class="song-item-duration">${formatDuration(s.duration)}</div>
        </div>`;
    });
    container.innerHTML = html;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ========== Playlist ==========
async function checkNcmStatus() {
    try {
        const resp = await fetch('/api/ncm/status');
        const data = await resp.json();
        ncmLoggedIn = data.logged_in;
        ncmUserInfo = data;
        updatePlaylistUI();
    } catch (e) {
        updatePlaylistUI();
    }
}

function updatePlaylistUI() {
    if (ncmLoggedIn) {
        document.getElementById('playlistLoginSection').classList.add('hidden');
        document.getElementById('playlistLoggedIn').classList.remove('hidden');
        document.getElementById('playlistUserInfo').textContent =
            `${ncmUserInfo.nickname || '\u7528\u6237'} \u7684\u6B4C\u5355`;
        fetchPlaylists();
    } else {
        document.getElementById('playlistLoginSection').classList.remove('hidden');
        document.getElementById('playlistLoggedIn').classList.add('hidden');
        document.getElementById('playlistDetail').classList.add('hidden');
    }
}

async function fetchPlaylists() {
    const grid = document.getElementById('playlistGrid');
    grid.innerHTML = '<div class="loading-dots">\u52A0\u8F7D\u6B4C\u5355\u4E2D...</div>';
    try {
        const resp = await fetch('/api/ncm/playlists');
        const data = await resp.json();
        if (data.code !== 200 && data.msg) {
            ncmLoggedIn = false;
            updatePlaylistUI();
            return;
        }
        renderPlaylists(data.playlists || []);
    } catch (e) {
        grid.innerHTML = '<div class="empty-state"><div class="icon">\u{1F61E}</div><div>\u52A0\u8F7D\u5931\u8D25</div></div>';
    }
}

function renderPlaylists(playlists) {
    const grid = document.getElementById('playlistGrid');
    if (!playlists.length) {
        grid.innerHTML = '<div class="empty-state"><div class="icon">\u{1F4CB}</div><div>\u6682\u65E0\u6B4C\u5355</div></div>';
        return;
    }
    let html = '';
    playlists.forEach(pl => {
        html += `<div class="playlist-card" onclick="fetchPlaylistDetail(${pl.id}, '${escapeHtml(pl.name)}')">
            <div class="playlist-card-cover" style="background-image:url('${pl.cover || ''}')">${pl.cover ? '' : '\u{1F3B5}'}</div>
            <div class="playlist-card-info">
                <div class="playlist-card-name">${escapeHtml(pl.name)}</div>
                <div class="playlist-card-count">${pl.trackCount}\u9996</div>
            </div>
        </div>`;
    });
    grid.innerHTML = html;
}

async function fetchPlaylistDetail(playlistId, playlistName) {
    currentPlaylistView = 'detail';
    document.getElementById('playlistGrid').parentElement.classList.add('hidden');
    document.getElementById('playlistDetail').classList.remove('hidden');
    document.getElementById('playlistLoggedIn').classList.add('hidden');

    const listEl = document.getElementById('playlistSongList');
    listEl.innerHTML = '<div class="loading-dots">\u52A0\u8F7D\u6B4C\u66F2\u4E2D...</div>';
    try {
        const resp = await fetch(`/api/ncm/playlist/${playlistId}`);
        const data = await resp.json();
        renderPlaylistSongs(data.tracks || []);
    } catch (e) {
        listEl.innerHTML = '<div class="empty-state"><div class="icon">\u{1F61E}</div><div>\u52A0\u8F7D\u5931\u8D25</div></div>';
    }
}

function renderPlaylistSongs(tracks) {
    const listEl = document.getElementById('playlistSongList');
    if (!tracks.length) {
        listEl.innerHTML = '<div class="empty-state"><div class="icon">\u{1F4CB}</div><div>\u6682\u65E0\u6B4C\u66F2</div></div>';
        return;
    }
    let html = '';
    tracks.forEach((t, i) => {
        html += `<div class="song-item" onclick="playNcmSong(${t.id}, '${escapeHtml(t.name)}')">
            <div class="song-item-index">${i + 1}</div>
            <div class="song-item-cover" style="background-image:url('${t.cover || ''}')">${t.cover ? '' : '\u{1F3B5}'}</div>
            <div class="song-item-info">
                <div class="song-item-name">${escapeHtml(t.name)}</div>
                <div class="song-item-artist">${escapeHtml(t.artists)}${t.album ? ' \u00B7 ' + escapeHtml(t.album) : ''}</div>
            </div>
            <div class="song-item-duration">${formatDuration(t.duration)}</div>
        </div>`;
    });
    listEl.innerHTML = html;
}

function backToPlaylists() {
    currentPlaylistView = 'grid';
    document.getElementById('playlistDetail').classList.add('hidden');
    document.getElementById('playlistLoggedIn').classList.remove('hidden');
    document.getElementById('playlistGrid').parentElement.classList.remove('hidden');
    fetchPlaylists();
}

async function playNcmSong(songId, songName) {
    switchTab('nowplaying');

    fetch('/api/ncm/open_web', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_id: songId })
    }).catch(() => {});

    setTimeout(() => {
        control('play');
    }, 2000);
    setTimeout(fetchStatus, 3500);
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
        c.classList.toggle('active', c.id === 'tab-' + tabName);
    });
}

// ========== Login ==========
async function doLogin(type) {
    hideLoginError();
    const cookie = document.getElementById('loginCookie').value.trim();
    if (!cookie) { showLoginError('\u8BF7\u7C98\u8D34 MUSIC_U cookie'); return; }

    try {
        const resp = await fetch('/api/ncm/login_cookie', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cookie })
        });
        const data = await resp.json();
        if (data.logged_in) {
            ncmLoggedIn = true;
            ncmUserInfo = data;
            updatePlaylistUI();
        } else {
            showLoginError(data.msg || 'Cookie \u65E0\u6548\u6216\u5DF2\u8FC7\u671F');
        }
    } catch (e) {
        showLoginError('\u7F51\u7EDC\u9519\u8BEF\uFF0C\u8BF7\u91CD\u8BD5');
    }
}

async function doLogout() {
    try {
        await fetch('/api/ncm/logout', { method: 'POST' });
    } catch (e) {}
    ncmLoggedIn = false;
    ncmUserInfo = null;
    updatePlaylistUI();
}

function showLoginError(msg) {
    const el = document.getElementById('loginError');
    el.textContent = msg;
    el.style.display = 'block';
}

function hideLoginError() {
    document.getElementById('loginError').style.display = 'none';
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
