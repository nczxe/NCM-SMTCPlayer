import platform


class VolumeController:
    def __init__(self):
        self._available = False
        self._sessions = {}
        self._init_volume()

    def _init_volume(self):
        if platform.system() != "Windows":
            print("[WARN] 非Windows平台，音量控制不可用")
            self._available = False
            return

        try:
            from pycaw.pycaw import AudioUtilities

            self._AudioUtilities = AudioUtilities
            self._available = True
            print("[INFO] 音量控制初始化成功")
        except ImportError as e:
            print(f"[WARN] 无法导入 pycaw: {e}")
            print("[WARN] 请运行: pip install pycaw comtypes")
            self._available = False

    def _get_master_volume(self):
        if not self._available:
            return None
        try:
            devices = self._AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            return volume
        except Exception as e:
            print(f"[ERROR] 获取主音量失败: {e}")
            return None

    def get_master_volume(self):
        if not self._available:
            return {"volume": 0, "muted": False, "available": False}
        try:
            volume = self._get_master_volume()
            if volume:
                current = volume.GetMasterVolumeLevelScalar()
                muted = volume.GetMute()
                return {
                    "volume": round(current * 100, 1),
                    "muted": bool(muted),
                    "available": True,
                }
        except Exception as e:
            print(f"[ERROR] 获取音量失败: {e}")
        return {"volume": 0, "muted": False, "available": False}

    def set_master_volume(self, percent):
        if not self._available:
            return False
        try:
            percent = max(0.0, min(100.0, float(percent)))
            volume = self._get_master_volume()
            if volume:
                volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return True
        except Exception as e:
            print(f"[ERROR] 设置音量失败: {e}")
        return False

    def toggle_mute(self):
        if not self._available:
            return False
        try:
            volume = self._get_master_volume()
            if volume:
                muted = volume.GetMute()
                volume.SetMute(0 if muted else 1, None)
                return True
        except Exception as e:
            print(f"[ERROR] 切换静音失败: {e}")
        return False

    def get_app_volume(self, process_name):
        if not self._available:
            return None
        try:
            sessions = self._AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() == process_name.lower():
                    volume = session.SimpleAudioVolume
                    return {
                        "volume": round(volume.GetMasterVolume() * 100, 1),
                        "muted": bool(volume.GetMute()),
                        "available": True,
                    }
        except Exception as e:
            print(f"[ERROR] 获取应用音量失败: {e}")
        return None

    def set_app_volume(self, process_name, percent):
        if not self._available:
            return False
        try:
            percent = max(0.0, min(100.0, float(percent)))
            sessions = self._AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() == process_name.lower():
                    volume = session.SimpleAudioVolume
                    volume.SetMasterVolume(percent / 100.0, None)
                    return True
        except Exception as e:
            print(f"[ERROR] 设置应用音量失败: {e}")
        return False

    @property
    def available(self):
        return self._available
