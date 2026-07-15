# SMTC Player

Windows 媒体远程控制器 —— 通过局域网用手机浏览器 / PWA 控制电脑上的媒体播放，并对网易云音乐提供增强支持（精准进度、封面、搜索、歌单）。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

---

## 目录

- [功能](#功能)
- [快速开始](#快速开始)
- [命令行参数](#命令行参数)
- [网易云音乐功能](#网易云音乐功能)
- [安全机制](#安全机制)
- [API 端点](#api-端点)
- [项目结构](#项目结构)
- [架构概述](#架构概述)
- [构建与发布](#构建与发布)
- [测试](#测试)
- [许可证](#许可证)

---

## 功能

### 媒体控制
- 播放 / 暂停、上一首、下一首
- 歌曲标题、艺术家、专辑、封面的实时显示
- 播放进度与总时长
- 系统音量控制与静音切换

### 网易云音乐信息获取增强
- 精确播放进度（通过 `netease-watcher` 原生进程注入获取，比系统 SMTC 更精准）
- 高清专辑封面
- 歌曲搜索
- 用户歌单浏览与播放
- 网页登录拉起播放（`MUSIC_U` Cookie，使用 Windows DPAPI 本地加密存储）

### 用户体验
- 手机浏览器 / PWA 均可访问，支持添加到手机主屏幕
- 深色主题、玻璃拟态 UI，响应式布局适配移动端
- 首次访问需要设置 PIN 码，后续通过 token 鉴权
- 桌面 GUI（Tkinter）：二维码配网、当前播放信息、封面的旋转动画、音量/进度条、系统托盘图标
- 无 GUI 模式（`--no-gui`），适合作为后台服务运行
- 服务状态诊断接口 `/api/health`

---

## 快速开始

### 环境要求

- Windows 10 / 11
- Python 3.8+
- 网易云音乐客户端 3.1.15+

### 安装与运行

```bat
cd server
pip install -r requirements.txt
python main.py
```

或使用脚本一键启动：

```bat
start_server.bat
```

启动后，在 GUI 窗口中点击「启动服务」，手机扫描二维码或直接访问界面中显示的局域网地址（如 `http://192.168.1.100:8888`）。首次打开网页会要求设置一个 4-16 位的 PIN 码。

### 无 GUI 模式

```bat
python server\main.py --no-gui
```

服务将在后台运行，按 `Ctrl+C` 退出。

### 直接运行预构建 EXE

下载 `dist/SMTCPlayer.exe`，双击运行即可（无需安装 Python）。

---

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--port <PORT>` | 指定 HTTP 服务端口（默认: 8888） |
| `--save-port` | 将 `--port` 指定的端口保存到 `config.json`，下次启动自动使用 |
| `--no-gui` | 不启动 GUI 窗口，仅运行 Flask 后台服务 |
| `--set-pin <PIN>` | 设置或重置访问 PIN（4-16 位） |

**环境变量：** `SMTC_PORT` 也可以用来指定端口，优先级低于 `--port` 命令行参数但高于 `config.json`。

**端口解析优先级：** `--port` > `SMTC_PORT` 环境变量 > `config.json` > `8888`（默认）

---

## 网易云音乐功能

### 登录

在手机网页端「搜索」或「歌单」标签页，输入网易云音乐的 `MUSIC_U` Cookie 进行登录。

> **获取 Cookie 方法：** 在浏览器中打开 [music.163.com](https://music.163.com) 并登录，然后从开发者工具（F12 → Application → Cookies）复制 `MUSIC_U` 的值。

Cookie 会被加密保存到 `%ProgramData%\SMTCPlayer\.ncm_cache\cookies.json`，使用 Windows DPAPI（`CryptProtectData`）加密，仅当前 Windows 用户可解密，其他用户或机器无法读取。

### 搜索

支持按关键词搜索歌曲，返回歌曲列表（包含标题、艺术家、专辑、封面）。

### 歌单

登录后可浏览自己的歌单，点击歌单查看歌曲列表，点击歌曲可通过网页拉起网易云客户端播放。

### 播放方式

采用「打开网易云歌曲网页，由网页拉起桌面客户端」的方案，因为 `orpheus://song/{id}` 协议在测试时无法正常触发播放。

---

## 安全机制

### PIN 认证

- PIN 长度：4-16 位，可包含字母、数字和 `!@#$%^&*()_-+=[]{}:;,.?/|~`
- 存储：使用 PBKDF2-SHA256（200,000 次迭代）生成 salt 和哈希值，保存在 `config.json`
- 验证：使用 HMAC 恒定时间比较，防止时序攻击
- 首次访问时强制设置 PIN，后续使用 PIN 换取 session token

### Token 认证

- 登录成功后返回 `X-SMTC-Token`，前端自动注入到所有 API 请求的 Header 中
- 本地回环地址（`127.0.0.1` / `localhost`）的请求无需认证
- Token 存储在 `localStorage`，浏览器关闭后需重新登录

### Cookie 加密

- 网易云 Cookie 使用 Windows DPAPI 加密存储
- 只有当前 Windows 用户会话可解密

---

## API 端点

所有 `/api/*` 端点需要 `X-SMTC-Token` Header 认证（auth 路由和本地回环请求除外）。

### 媒体控制

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/status` | 获取当前播放状态（歌曲信息、进度、音量等） |
| `POST` | `/api/play_pause` | 切换播放 / 暂停 |
| `POST` | `/api/next` | 下一首 |
| `POST` | `/api/previous` | 上一首 |
| `POST` | `/api/volume` | 设置系统音量（body: `{"level": 0-100}`） |
| `POST` | `/api/volume/toggle_mute` | 切换静音 |

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/auth/status` | 检查 PIN 是否已设置 |
| `POST` | `/api/auth/setup` | 首次设置 PIN（body: `{"pin": "..."}`） |
| `POST` | `/api/auth/login` | PIN 登录，返回 token（body: `{"pin": "..."}`） |

### 网易云音乐

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/ncm/login/cellphone` | 手机号登录 |
| `POST` | `/api/ncm/login/email` | 邮箱登录 |
| `POST` | `/api/ncm/login/cookie` | Cookie 登录（body: `{"cookie": "MUSIC_U=..."}`) |
| `GET` | `/api/ncm/search?keyword=xxx` | 搜索歌曲 |
| `GET` | `/api/ncm/user/playlist` | 获取用户歌单列表 |
| `GET` | `/api/ncm/playlist/detail?id=xxx` | 获取歌单详情 |
| `GET` | `/api/ncm/song/detail?id=xxx` | 获取歌曲详情 |
| `POST` | `/api/ncm/open_web` | 在网易云网页打开歌曲（body: `{"id": "..."}`) |

### 服务诊断

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 诊断 SMTC、音量、Watcher、NCM API 连通性 |

---

## 项目结构

```
NCM-SMTCPlayer/
├── server/                        # 当前主线源码
│   ├── main.py                    # 入口：参数解析、watcher 进程管理、Flask 及 GUI 启动
│   ├── app.py                     # Flask API 服务端 + 静态文件托管
│   ├── smtc_controller.py         # Windows SMTC API 封装（媒体信息读取与命令下发）
│   ├── netease_watcher.py         # netease-watcher.exe HTTP 客户端
│   ├── volume_controller.py       # 系统音量控制（pycaw）
│   ├── ncm_music_api.py           # 网易云音乐 API（登录、搜索、歌单、WEAPI 加密）
│   ├── security.py                # PIN 管理、Token 认证、DPAPI 加密
│   ├── gui.py                     # Tkinter 桌面 GUI（二维码、播放信息、系统托盘）
│   ├── config.json                # 运行时配置（端口、PIN 哈希）
│   ├── requirements.txt           # Python 依赖
│   └── static/                    # 移动端 Web 前端
│       ├── index.html             # 主页面（正在播放 / 搜索 / 歌单）
│       ├── api.js                 # fetch 拦截器，自动注入认证 Token
│       ├── auth.js                # PIN 登录 / 设置流程
│       ├── player.js              # 播放器核心逻辑（轮询、控制、搜索、歌单）
│       ├── style.css              # 样式（深色主题、玻璃拟态、响应式）
│       ├── service-worker.js      # PWA Service Worker（离线缓存）
│       ├── manifest.json          # PWA 清单
│       └── icon.svg               # SVG 图标
├── netease-watcher/               # netease-watcher
│   ├── netease-watcher.exe
│   └── wndhok.dll
├── tests/
│   └── test_security.py           # PIN/安全机制单元测试
├── archive/                       # 旧版代码归档
│   ├── server-legacy/
│   ├── Beta-source/
│   └── NCM-SMTCPlayer-copy/
├── build.bat                      # 构建脚本（PyInstaller）
├── release.bat                    # 发布脚本（语法检查 + 测试 + 构建）
├── start_server.bat               # 快速启动脚本
├── SMTCPlayer.spec                # PyInstaller 构建配置
├── LICENSE                        # MIT 许可证
└── README.md
```

---

## 架构概述

```
┌──────────────────────────────────────────────────────────────┐
│                     手机浏览器 / PWA                          │
│          http://<PC-IP>:8888  (局域网 HTTP)                  │
└──────────────────────────┬───────────────────────────────────┘
                           │  REST API (JSON + Token Auth)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   Flask Server (app.py)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ security.py  │  │ ncm_music_   │  │ netease_watcher.py  │ │
│  │ PIN/Token    │  │ api.py       │  │ HTTP 客户端          │ │
│  │ Auth + DPAPI │  │ 网易云 API    │  │ localhost:3574       │ │
│  └─────────────┘  └──────────────┘  └──────────┬──────────┘ │
│                                                  │            │
│  ┌────────────────┐  ┌──────────────────┐        │            │
│  │ smtc_controller│  │ volume_controller│        │            │
│  │ .py            │  │ .py              │        │            │
│  │ Windows SMTC   │  │ pycaw 音量控制    │        │            │
│  │ API (winrt)    │  │                  │        │            │
│  └────────────────┘  └──────────────────┘        │            │
└──────────────────────────────────────────────────┼────────────┘
                                                   │
                          ┌─────────────────────────▼──────────┐
                          │   netease-watcher.exe + wndhok.dll  │
                          │   注入网易云进程，提取精准进度/封面   │
                          └────────────────────────────────────┘
```

1. **`main.py`** 启动后：
   - 启动 `netease-watcher.exe` 后台进程（注入网易云客户端获取增强数据）
   - 在 daemon 线程中启动 Flask 服务器（监听 `0.0.0.0`）
   - 可选启动 Tkinter GUI（显示二维码、播放信息、系统托盘）

2. **手机** 通过局域网访问 `http://<PC-IP>:8888`：
   - 首次访问设置 PIN → 获取 session token
   - PWA 可「添加到主屏幕」，获得类原生体验

3. **状态轮询**：前端每 1 秒调用 `/api/status`，服务端合并以下数据源：
   - SMTC Controller → 系统级媒体信息（标题、艺术家、播放状态）
   - Netease Watcher → 网易云增强数据（精准进度、高清封面、歌曲 ID）
   - Volume Controller → 系统音量、静音状态

4. **控制指令**：通过 POST 请求下发播放、音量等操作

5. **网易云功能**：登录、搜索、歌单通过 `ncm_music_api.py` 调用 [NeteaseCloudMusicApi](https://gitlab.com/Binaryify/neteasecloudmusicapi) 兼容接口

---

## 构建与发布

### 构建 EXE

```bat
build.bat
```

输出：`dist/SMTCPlayer.exe`（独立可执行文件，无需 Python 环境）

构建过程：检查 Python → 安装 PyInstaller → 安装依赖 → 执行 `pyinstaller --clean --noconfirm SMTCPlayer.spec`

### 发布流程

```bat
release.bat
```

完整发布流程：Python 语法检查 → 单元测试 → 构建 EXE

### PyInstaller 配置

构建配置位于 `SMTCPlayer.spec`，关键配置：
- **入口点：** `server/main.py`
- **数据文件：** `netease-watcher/`（exe + dll）、`server/static/`（Web 前端）
- **隐藏导入：** Crypto、PIL、qrcode、pystray 等
- **输出：** 无控制台窗口的 Windows GUI 程序，启用 UPX 压缩

---

## 测试

```bat
# 语法检查
python -m compileall server tests

# 单元测试（unittest）
python -m unittest discover -s tests

# 单元测试（pytest，如果已安装）
python -m pytest tests -v
```

当前测试覆盖 `security.py` 中的 PIN 策略验证与哈希校验。

---

## 许可证

[MIT License](LICENSE) © 2026 FR-NEXT

---

## 致谢

本项目的部分功能实现使用了以下开源项目的内容：

- [WinRT for Python](https://github.com/Microsoft/xlang/tree/master/src/tool/python) — Windows SMTC API 访问
- [pycaw](https://github.com/AndreMiras/pycaw) — Windows 音量控制
- [NeteaseCloudMusicApi](https://gitlab.com/Binaryify/neteasecloudmusicapi) — 网易云音乐 API 参考
