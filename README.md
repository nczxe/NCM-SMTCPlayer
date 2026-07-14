# SMTC Player

Windows 媒体控制器 - 通过局域网用手机/网页遥控电脑播放音乐。

## 功能特性

- 🎵 **播放控制**：播放/暂停、上一首、下一首
- 📊 **进度显示**：实时显示播放进度和时长
- 🎨 **专辑封面**：圆形封面，播放时旋转动画
- 🔊 **音量控制**：系统音量控制
- 📱 **PWA 支持**：可添加到手机桌面，像原生 App 一样使用
- 🎵 **网易云信息获取增强**：集成 netease-watcher，获取精确进度、封面、歌名

## 架构说明

- **服务端（Windows）**：基于 Windows SMTC API + Flask HTTP 服务
- **客户端**：网页 / PWA
- **网易云信息获取增强**：使用netease-watcher 提供精确的网易云音乐数据

## 快速开始

### 1. 安装依赖（您需要先安装Python）

```bash
cd server
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

启动后会显示：

```
  本地访问: http://127.0.0.1:8888
  局域网访问: http://192.168.x.x:8888
```

### 3. 手机控制

确保手机和电脑在同一局域网，用浏览器打开 `http://电脑IP:8888`。

## PWA 安装（推荐）

### 安卓（Chrome）

1. 在浏览器访问网页点击菜单 →「添加到主屏幕」/「安装应用」
2. 桌面会出现 SMTC 图标，点击全屏打开

### iOS（Safari）

1. 用 Safari 打开控制页面
2. 点击分享按钮 →「添加到主屏幕」
3. 桌面会出现 SMTC 图标

## 网易云增强

网易云音乐的 SMTC 不提供准确时长，需要配合 netease-watcher 使用。

1. 下载并运行 `netease-watcher/netease-watcher.exe`
2. 启动服务端时会自动检测并连接
3. 成功后可获取：精确时长、进度、专辑封面、歌曲ID

## 音量控制

支持两种音量：
- **系统主音量**：调节整个系统的音量
- **应用音量**：单独调节当前播放器的音量（如网易云音乐）

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 获取播放状态 |
| `/api/play_pause` | POST | 播放/暂停 |
| `/api/next` | POST | 下一首 |
| `/api/previous` | POST | 上一首 |
| `/api/volume` | GET | 获取系统音量 |
| `/api/volume` | POST | 设置系统音量 `{volume: 50}` |
| `/api/volume/toggle_mute` | POST | 切换静音 |
| `/api/app_volume` | GET | 获取应用音量 |
| `/api/app_volume` | POST | 设置应用音量 |

## 目录结构

```
SMTCPlayer/
├── server/              # 服务端
│   ├── app.py           # Flask 主程序 + PWA
│   ├── smtc_controller.py    # SMTC 媒体控制
│   ├── netease_watcher.py    # 网易云增强客户端
│   ├── volume_controller.py  # 音量控制
│   └── requirements.txt
├── netease-watcher/     # 网易云增强工具
│   └── netease-watcher.exe
└── start_server.bat     # 一键启动脚本
```

## 技术栈

- **后端**：Python + Flask
- **SMTC**：winrt (Windows Runtime)
- **音量控制**：pycaw + comtypes
- **前端**：原生 HTML/CSS/JS
- **PWA**：manifest.json + Service Worker

## 致谢

本项目的部分功能实现使用了以下开源项目的内容：

- [netease-watcher](https://github.com/YUCLing/netease-watcher) — 监控网易云音乐当前播放歌曲和播放进度，低资源消耗，几乎实时更新。
