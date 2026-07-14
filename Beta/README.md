# SMTC Player (Beta)

Windows 媒体控制器 — 通过局域网用手机/网页遥控电脑播放音乐。  
Beta 版新增：**歌曲搜索**、**歌单浏览与播放**、**Cookie 持久化登录**、**netease-watcher 自动集成**。

## 功能特性

- 🎵 **播放控制**：播放/暂停、上一首、下一首
- 📊 **进度显示**：实时显示播放进度和时长
- 🎨 **专辑封面**：圆形封面，播放时旋转动画
- 🔊 **音量控制**：系统音量 + 应用音量调节，支持静音切换
- 📱 **PWA 支持**：可添加到手机桌面，像原生 App 一样使用
- 🎵 **网易云增强**：自动拉起 netease-watcher，提供精确进度、封面、歌名
- 🔍 **歌曲搜索**（Beta）：搜索网易云曲库，点击直接播放
- 📋 **歌单浏览**（Beta）：查看网易云歌单，支持歌单内选歌播放
- 🔑 **Cookie 登录**（Beta）：粘贴浏览器 MUSIC_U Cookie 登录，一次登录持久有效

## 架构说明

```
手机/浏览器 (PWA)
       │
       │ HTTP (局域网)
       ▼
┌─────────────────────────────┐
│  Flask 服务端 (app.py)       │
│  ├── smtc_controller.py     │  ← Windows SMTC API
│  ├── netease_watcher.py     │  ← 连接 netease-watcher
│  ├── ncm_music_api.py       │  ← 网易云 API（搜索/歌单）
│  └── volume_controller.py   │  ← pycaw 音量控制
└─────────────────────────────┘
       │                │
       ▼                ▼
  SMTC Session    netease-watcher.exe
  (Windows API)   (Rust 进程监控)
       │                │
       ▼                ▼
  网易云音乐客户端 ◄── webdb.dat + 内存读取
```

## 快速开始

### 1. 安装依赖

```bash
cd Beta\server
pip install -r requirements.txt
```

### 2. 启动服务

双击 `Beta\start_server.bat`，或：

```bash
cd Beta\server
python app.py
```

启动后会显示：

```
  本地访问: http://127.0.0.1:8888
  局域网访问: http://192.168.x.x:8888
  SMTC可用: 是
  网易云增强: 已启用 (netease-watcher)
  网易云API: 已加载
```

netease-watcher 会自动在后台启动，无需手动运行。

### 3. 登录网易云（使用歌单功能）

1. 用浏览器打开 https://music.163.com 并登录
2. 按 F12 → Application → Cookies → 找到 `MUSIC_U`
3. 复制其**值**，粘贴到控制页面的「歌单」→ Cookie 登录输入框
4. 点击登录

Cookie 会持久化保存在本地，下次启动无需重新登录。

### 4. 手机控制

确保手机和电脑在同一局域网，用手机浏览器打开 `http://电脑IP:8888`。

## 使用说明

### 正在播放

显示当前播放的歌曲信息、进度、封面，提供播放控制和音量调节。

### 歌曲搜索

- 输入关键词实时搜索网易云曲库
- 点击搜索结果中的歌曲即可播放（需要电脑端网易云音乐已打开）
- 播放后自动关闭网页标签

### 歌单浏览

- 登录后显示所有个人歌单
- 点击歌单查看歌曲列表
- 点击列表中的歌曲即可播放

## PWA 安装（推荐）

### 安卓（Chrome）

1. 用 Chrome 打开控制页面
2. 点击右上角菜单 →「添加到主屏幕」/「安装应用」
3. 桌面会出现 SMTC 图标，点击全屏打开

### iOS（Safari）

1. 用 Safari 打开控制页面
2. 点击分享按钮 →「添加到主屏幕」
3. 桌面会出现 SMTC 图标

## API 接口

### 播放控制

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 获取播放状态 |
| `/api/play_pause` | POST | 播放/暂停 |
| `/api/play` | POST | 播放 |
| `/api/pause` | POST | 暂停 |
| `/api/next` | POST | 下一首 |
| `/api/previous` | POST | 上一首 |

### 音量控制

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/volume` | GET | 获取系统音量 |
| `/api/volume` | POST | 设置系统音量 `{volume: 50}` |
| `/api/volume/toggle_mute` | POST | 切换静音 |
| `/api/app_volume` | GET | 获取应用音量 |
| `/api/app_volume` | POST | 设置应用音量 |

### 网易云 API（Beta）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ncm/status` | GET | 检查登录状态 |
| `/api/ncm/login_cookie` | POST | Cookie 登录 `{cookie: "MUSIC_U值"}` |
| `/api/ncm/logout` | POST | 退出登录 |
| `/api/ncm/search?q=xx&limit=30` | GET | 搜索歌曲 |
| `/api/ncm/playlists` | GET | 获取用户歌单列表（需登录） |
| `/api/ncm/playlist/<id>` | GET | 获取歌单歌曲详情 |
| `/api/ncm/play` | POST | 播放歌曲 `{song_id: 123}` |

## 目录结构

```
Beta/
├── server/
│   ├── app.py              # Flask 主程序 + PWA 前端
│   ├── ncm_music_api.py    # 网易云 API 客户端（搜索/歌单/登录）
│   ├── smtc_controller.py  # SMTC 媒体控制
│   ├── netease_watcher.py  # 网易云增强客户端
│   ├── volume_controller.py# 音量控制
│   ├── requirements.txt    # Python 依赖
│   └── .ncm_cache/         # 登录状态缓存（自动生成）
├── netease-watcher/        # 网易云增强二进制文件
│   ├── netease-watcher.exe
│   └── wndhok.dll
├── netease-watcher-source/ # Rust 源码（v0.7.1）
│   ├── watcher/
│   ├── hooker/
│   └── Cargo.toml
├── start_server.bat        # 一键启动脚本
└── README.md               # 本文件
```

## 技术栈

- **后端**：Python + Flask
- **SMTC**：winrt (Windows Runtime)
- **网易云 API**：requests + pycryptodome（AES/RSA 加密）
- **音量控制**：pycaw + comtypes
- **前端**：原生 HTML/CSS/JS
- **PWA**：manifest.json + Service Worker
- **进程监控**：netease-watcher (Rust + Axum)

## 依赖项

```
flask>=2.3.0
requests>=2.28.0
pycryptodome>=3.18.0
winrt-Windows.Media.Control>=3.0.0    # Windows Only
winrt-Windows.Foundation>=3.0.0       # Windows Only
pycaw>=20235000                       # Windows Only
comtypes>=1.2.0                       # Windows Only
```

## 致谢

本项目引用了以下开源项目：

- [netease-watcher](https://github.com/YUCLing/netease-watcher) — 监控网易云音乐当前播放歌曲和播放进度，低资源消耗，几乎实时更新。
