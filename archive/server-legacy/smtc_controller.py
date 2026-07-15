import asyncio
import sys
import platform


class SMTCController:
    def __init__(self):
        self._manager = None
        self._session = None
        self._available = False
        self._last_status = {
            "title": "未检测到媒体",
            "artist": "",
            "album_title": "",
            "status": "stopped",
            "position": 0,
            "duration": 0,
            "is_playing": False,
            "has_previous": False,
            "has_next": False,
        }
        self._init_smtc()

    def _init_smtc(self):
        if platform.system() != "Windows":
            print("[WARN] 非Windows平台，SMTC不可用，将使用模拟模式")
            self._available = False
            return

        try:
            import winrt.windows.media.control as wmc
            import winrt.windows.foundation  # noqa: F401
            import winrt.windows.foundation.collections  # noqa: F401

            self._wmc = wmc
            self._available = True
            print("[INFO] SMTC 初始化成功")
        except ImportError as e:
            print(f"[WARN] 无法导入 winrt: {e}")
            print("[WARN] 请运行: pip install winrt-Windows.Media.Control winrt-Windows.Foundation winrt-Windows.Foundation.Collections")
            self._available = False

    def _get_session(self):
        if not self._available:
            return None
        try:
            sessions = asyncio.run(self._get_sessions_async())
            if sessions and len(sessions) > 0:
                return sessions[0]
            return None
        except Exception as e:
            print(f"[ERROR] 获取会话失败: {e}")
            return None

    async def _get_sessions_async(self):
        manager = await self._wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        sessions = manager.get_sessions()
        return list(sessions)

    def get_session_source(self):
        if not self._available:
            return ""
        try:
            session = self._get_session()
            if session:
                return session.source_app_user_model_id or ""
        except Exception:
            pass
        return ""

    def get_status(self):
        if not self._available:
            return self._last_status

        try:
            session = self._get_session()
            if not session:
                self._last_status["status"] = "stopped"
                self._last_status["is_playing"] = False
                self._last_status["title"] = "未检测到媒体播放"
                self._last_status["artist"] = ""
                self._last_status["position"] = 0
                self._last_status["duration"] = 0
                return self._last_status

            info = asyncio.run(self._get_media_info_async(session))
            timeline = session.get_timeline_properties()
            playback = session.get_playback_info()

            status_map = {
                0: "closed",
                1: "opened",
                2: "changing",
                3: "stopped",
                4: "playing",
                5: "paused",
            }

            position = 0
            duration = 0
            if timeline:
                try:
                    pos = timeline.position
                    position = pos.total_seconds() if callable(pos.total_seconds) else pos.total_seconds
                except Exception:
                    pass
                try:
                    end = timeline.end_time
                    duration = end.total_seconds() if callable(end.total_seconds) else end.total_seconds
                except Exception:
                    pass

            self._last_status = {
                "title": info.get("title", "未知标题"),
                "artist": info.get("artist", "未知艺术家"),
                "album_title": info.get("album_title", ""),
                "status": status_map.get(int(playback.playback_status), "unknown"),
                "position": position,
                "duration": duration,
                "is_playing": int(playback.playback_status) == 4,
                "has_previous": bool(playback.controls.is_previous_enabled),
                "has_next": bool(playback.controls.is_next_enabled),
            }
            return self._last_status
        except Exception as e:
            print(f"[ERROR] 获取状态失败: {e}")
            return self._last_status

    async def _get_media_info_async(self, session):
        info = await session.try_get_media_properties_async()
        return {
            "title": info.title or "未知标题",
            "artist": info.artist or "未知艺术家",
            "album_title": info.album_title or "",
            "album_artist": info.album_artist or "",
            "track_number": info.track_number,
        }

    def play_pause(self):
        if not self._available:
            return False
        try:
            session = self._get_session()
            if not session:
                return False
            if hasattr(session, "try_toggle_play_pause_async"):
                session.try_toggle_play_pause_async()
            else:
                session.try_play_pause_toggle_async()
            return True
        except Exception as e:
            print(f"[ERROR] 播放暂停失败: {e}")
            return False

    def play(self):
        if not self._available:
            return False
        try:
            session = self._get_session()
            if not session:
                return False
            session.try_play_async()
            return True
        except Exception as e:
            print(f"[ERROR] 播放失败: {e}")
            return False

    def pause(self):
        if not self._available:
            return False
        try:
            session = self._get_session()
            if not session:
                return False
            session.try_pause_async()
            return True
        except Exception as e:
            print(f"[ERROR] 暂停失败: {e}")
            return False

    def next_track(self):
        if not self._available:
            return False
        try:
            session = self._get_session()
            if not session:
                return False
            session.try_skip_next_async()
            return True
        except Exception as e:
            print(f"[ERROR] 下一首失败: {e}")
            return False

    def previous_track(self):
        if not self._available:
            return False
        try:
            session = self._get_session()
            if not session:
                return False
            session.try_skip_previous_async()
            return True
        except Exception as e:
            print(f"[ERROR] 上一首失败: {e}")
            return False

    @property
    def available(self):
        return self._available
