"""Pulse Music — a compact multi-source desktop music player."""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen


_VLC_DLL_DIRECTORY = None


def configure_bundled_vlc() -> None:
    global _VLC_DLL_DIRECTORY
    bundle_root = getattr(sys, "_MEIPASS", "")
    if not bundle_root:
        return
    vlc_dir = Path(bundle_root) / "vlc"
    libvlc = vlc_dir / "libvlc.dll"
    plugins = vlc_dir / "plugins"
    if not libvlc.is_file() or not plugins.is_dir():
        return
    if hasattr(os, "add_dll_directory"):
        _VLC_DLL_DIRECTORY = os.add_dll_directory(str(vlc_dir))
    os.environ["PYTHON_VLC_LIB_PATH"] = str(libvlc)
    os.environ["PYTHON_VLC_MODULE_PATH"] = str(plugins)


configure_bundled_vlc()

import vlc
import yt_dlp
from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRectF, QSequentialAnimationGroup, QObject, QPointF, QRunnable, QSize, QThreadPool, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF, QRadialGradient
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSlider, QInputDialog, QFileDialog, QAbstractItemView,
    QToolButton, QVBoxLayout, QWidget, QStackedWidget, QMenu,
)


ACCENT = "#c96442"
BACKGROUND = "#faf9f5"
MUTED = "#83827d"
TEXT = "#141413"
NANO_SIZE = QSize(380, 260)
EXPANDED_SIZE = QSize(1020, 720)


@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    source: str
    webpage_url: str
    duration: int = 0
    resolver_query: str = ""
    thumbnail_url: str = ""

    @property
    def label(self) -> str:
        return f"{self.artist} — {self.title}" if self.artist else self.title


class IconFactory:
    SIZE = 24

    @classmethod
    def icon(cls, name: str, color: str = "#3d3929") -> QIcon:
        return QIcon(cls.pixmap(name, color))

    @classmethod
    def pixmap(cls, name: str, color: str = "#3d3929") -> QPixmap:
        pixmap = QPixmap(cls.SIZE, cls.SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        pen = QPen(QColor(color), 2)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if name == "play":
            cls._fill_polygon(painter, ((8, 5), (19, 12), (8, 19)), color)
        elif name == "pause":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRect(7, 5, 4, 14)
            painter.drawRect(13, 5, 4, 14)
        elif name in {"previous", "next", "rewind", "forward"}:
            cls._draw_transport(painter, name, color)
        elif name == "stop":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRect(6, 6, 12, 12)
        elif name == "search":
            painter.drawEllipse(4, 4, 10, 10)
            painter.drawLine(12, 12, 19, 19)
        elif name == "bell":
            painter.drawArc(7, 4, 10, 12, 25 * 16, 130 * 16)
            painter.drawLine(6, 15, 18, 15)
            painter.drawLine(12, 18, 12, 19)
        elif name == "close":
            painter.drawLine(7, 7, 17, 17)
            painter.drawLine(17, 7, 7, 17)
        elif name == "history":
            painter.drawEllipse(5, 5, 14, 14)
            painter.drawLine(12, 8, 12, 12)
            painter.drawLine(12, 12, 15, 14)
        elif name == "discover":
            painter.drawEllipse(5, 5, 14, 14)
            painter.drawLine(9, 15, 15, 9)
            cls._fill_polygon(painter, ((14, 8), (17, 7), (16, 10)), color)
        elif name == "playlist":
            painter.drawLine(6, 7, 18, 7)
            painter.drawLine(6, 12, 18, 12)
            painter.drawLine(6, 17, 14, 17)
            painter.drawEllipse(16, 15, 3, 3)
        elif name == "plus":
            painter.drawLine(12, 6, 12, 18)
            painter.drawLine(6, 12, 18, 12)
        elif name == "volume":
            cls._fill_polygon(painter, ((5, 10), (9, 10), (14, 6), (14, 18), (9, 14), (5, 14)), color)
            painter.drawArc(11, 8, 8, 8, -45 * 16, 90 * 16)
        elif name == "shuffle":
            painter.drawLine(5, 7, 8, 7)
            painter.drawLine(8, 7, 16, 17)
            painter.drawLine(16, 17, 19, 17)
            cls._fill_polygon(painter, ((17, 14), (21, 17), (17, 20)), color)
            painter.drawLine(5, 17, 8, 17)
            painter.drawLine(8, 17, 11, 13)
            painter.drawLine(13, 10, 16, 7)
            painter.drawLine(16, 7, 19, 7)
            cls._fill_polygon(painter, ((17, 4), (21, 7), (17, 10)), color)
        elif name == "up":
            painter.drawLine(12, 18, 12, 7)
            cls._fill_polygon(painter, ((7, 11), (12, 6), (17, 11)), color)
        elif name == "down":
            painter.drawLine(12, 6, 12, 17)
            cls._fill_polygon(painter, ((7, 13), (12, 18), (17, 13)), color)
        elif name == "image":
            painter.drawRect(4, 5, 16, 14)
            painter.drawEllipse(7, 8, 3, 3)
            painter.drawPolyline(QPolygonF([QPointF(6, 17), QPointF(10, 13), QPointF(13, 16), QPointF(16, 12), QPointF(19, 17)]))
        elif name == "expand":
            painter.drawLine(5, 10, 5, 5)
            painter.drawLine(5, 5, 10, 5)
            painter.drawLine(14, 5, 19, 5)
            painter.drawLine(19, 5, 19, 10)
            painter.drawLine(5, 14, 5, 19)
            painter.drawLine(5, 19, 10, 19)
            painter.drawLine(14, 19, 19, 19)
            painter.drawLine(19, 14, 19, 19)
        elif name == "collapse":
            painter.drawLine(10, 5, 10, 10)
            painter.drawLine(5, 10, 10, 10)
            painter.drawLine(14, 5, 14, 10)
            painter.drawLine(14, 10, 19, 10)
            painter.drawLine(5, 14, 10, 14)
            painter.drawLine(10, 14, 10, 19)
            painter.drawLine(14, 14, 19, 14)
            painter.drawLine(14, 14, 14, 19)
        elif name == "pulse":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            for x, height in ((4, 8), (8, 14), (12, 19), (16, 13), (20, 7)):
                painter.drawRect(x, (24 - height) // 2, 3, height)
        painter.end()
        return pixmap

    @staticmethod
    def _fill_polygon(painter: QPainter, points: tuple[tuple[int, int], ...], color: str) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))

    @classmethod
    def _draw_transport(cls, painter: QPainter, name: str, color: str) -> None:
        if name in {"previous", "rewind"}:
            triangles = [((15, 5), (7, 12), (15, 19))]
            if name == "rewind":
                triangles.append(((21, 5), (13, 12), (21, 19)))
            else:
                painter.drawLine(5, 5, 5, 19)
        else:
            triangles = [((9, 5), (17, 12), (9, 19))]
            if name == "forward":
                triangles.append(((3, 5), (11, 12), (3, 19)))
            else:
                painter.drawLine(19, 5, 19, 19)
        for triangle in triangles:
            cls._fill_polygon(painter, triangle, color)


class LibraryStore:
    def __init__(self) -> None:
        app_data = Path(os.getenv("LOCALAPPDATA", Path.home())) / "PulseMusic"
        self.path = app_data / "library.json"
        self.data = self._load()

    def playlist_names(self) -> list[str]:
        return sorted(self.data["playlists"], key=str.casefold)

    def create_playlist(self, name: str) -> bool:
        name = name.strip()
        if not name or name in self.data["playlists"]:
            return False
        self.data["playlists"][name] = {"tracks": [], "cover": ""}
        self._save()
        return True

    def add_to_playlist(self, name: str, track: Track) -> bool:
        playlist = self.data["playlists"].get(name)
        if not isinstance(playlist, dict):
            return False
        items = playlist["tracks"]
        if any(item.get("webpage_url") == track.webpage_url for item in items):
            return False
        items.append(asdict(track))
        self._save()
        return True

    def remove_from_playlist(self, name: str, webpage_url: str) -> bool:
        playlist = self.data["playlists"].get(name)
        if not isinstance(playlist, dict) or not webpage_url:
            return False
        items = playlist.get("tracks")
        if not isinstance(items, list):
            return False
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("webpage_url") == webpage_url:
                del items[index]
                self._save()
                return True
        return False

    def move_playlist_track(self, name: str, webpage_url: str, offset: int) -> bool:
        playlist = self.data["playlists"].get(name)
        if not isinstance(playlist, dict) or offset == 0:
            return False
        items = playlist.get("tracks")
        if not isinstance(items, list):
            return False
        for index, item in enumerate(items):
            if not isinstance(item, dict) or item.get("webpage_url") != webpage_url:
                continue
            destination = index + offset
            if not 0 <= destination < len(items):
                return False
            items[index], items[destination] = items[destination], items[index]
            self._save()
            return True
        return False

    def reorder_playlist_tracks(self, name: str, webpage_urls: list[str]) -> bool:
        playlist = self.data["playlists"].get(name)
        if not isinstance(playlist, dict):
            return False
        items = playlist.get("tracks")
        if not isinstance(items, list) or len(items) != len(webpage_urls):
            return False
        by_url = {item.get("webpage_url"): item for item in items if isinstance(item, dict)}
        if len(by_url) != len(items) or set(by_url) != set(webpage_urls):
            return False
        playlist["tracks"] = [by_url[url] for url in webpage_urls]
        self._save()
        return True

    def playlist_tracks(self, name: str) -> list[Track]:
        playlist = self.data["playlists"].get(name, {})
        return self._tracks_from(playlist.get("tracks", []) if isinstance(playlist, dict) else [])

    def playlist_cover(self, name: str) -> str:
        playlist = self.data["playlists"].get(name, {})
        return str(playlist.get("cover", "")) if isinstance(playlist, dict) else ""

    def set_playlist_cover(self, name: str, cover_path: str) -> bool:
        playlist = self.data["playlists"].get(name)
        if not isinstance(playlist, dict):
            return False
        playlist["cover"] = cover_path
        self._save()
        return True

    def record_recent(self, track: Track) -> None:
        recent = self.data["recent"]
        recent[:] = [item for item in recent if item.get("webpage_url") != track.webpage_url]
        recent.insert(0, asdict(track))
        del recent[30:]
        self._save()

    def recent_tracks(self) -> list[Track]:
        return self._tracks_from(self.data["recent"])

    def update_thumbnail(self, webpage_url: str, thumbnail_url: str) -> None:
        if not webpage_url or not thumbnail_url:
            return
        changed = False
        collections = [self.data["recent"]]
        collections.extend(
            playlist.get("tracks", [])
            for playlist in self.data["playlists"].values()
            if isinstance(playlist, dict)
        )
        for items in collections:
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("webpage_url") == webpage_url:
                    if item.get("thumbnail_url") != thumbnail_url:
                        item["thumbnail_url"] = thumbnail_url
                        changed = True
        if changed:
            self._save()

    def _load(self) -> dict[str, Any]:
        default = {"playlists": {}, "recent": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default
        if not isinstance(payload, dict):
            return default
        playlists = payload.get("playlists")
        recent = payload.get("recent")
        valid_playlists = {}
        if isinstance(playlists, dict):
            for name, value in playlists.items():
                if not isinstance(name, str):
                    continue
                if isinstance(value, list):
                    valid_playlists[name] = {"tracks": value, "cover": ""}
                elif isinstance(value, dict) and isinstance(value.get("tracks"), list):
                    valid_playlists[name] = {
                        "tracks": value["tracks"],
                        "cover": str(value.get("cover", "")),
                    }
        return {
            "playlists": valid_playlists,
            "recent": recent if isinstance(recent, list) else [],
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    @staticmethod
    def _tracks_from(items: Any) -> list[Track]:
        tracks: list[Track] = []
        if not isinstance(items, list):
            return tracks
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                tracks.append(
                    Track(
                        title=str(item["title"]),
                        artist=str(item.get("artist", "")),
                        source=str(item["source"]),
                        webpage_url=str(item["webpage_url"]),
                        duration=max(0, int(item.get("duration", 0))),
                        resolver_query=str(item.get("resolver_query", "")),
                        thumbnail_url=str(item.get("thumbnail_url") or item.get("thumbnail") or ""),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return tracks


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.result.emit(self.fn(*self.args))
        except Exception as exc:
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                pass
        finally:
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass


def _entry_thumbnail(item: dict[str, Any]) -> str:
    direct_url = item.get("thumbnail")
    if isinstance(direct_url, str) and direct_url:
        return direct_url
    thumbnails = item.get("thumbnails")
    if not isinstance(thumbnails, list):
        return ""
    candidates = [thumbnail for thumbnail in thumbnails if isinstance(thumbnail, dict) and thumbnail.get("url")]
    if not candidates:
        return ""

    def thumbnail_area(thumbnail: dict[str, Any]) -> int:
        try:
            return int(thumbnail.get("width") or 0) * int(thumbnail.get("height") or 0)
        except (TypeError, ValueError):
            return 0

    return str(max(candidates, key=thumbnail_area).get("url", ""))


def search_provider(query: str, source: str) -> list[Track]:
    prefix = "ytsearch8:" if source == "YouTube" else "scsearch8:"
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "socket_timeout": 15,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        data = ydl.extract_info(prefix + query, download=False) or {}
    tracks: list[Track] = []
    for item in data.get("entries", []):
        if not item:
            continue
        webpage_url = item.get("webpage_url") or item.get("original_url") or ""
        if not webpage_url and source == "YouTube" and item.get("id"):
            webpage_url = f"https://www.youtube.com/watch?v={item['id']}"
        if not webpage_url:
            continue
        tracks.append(
            Track(
                title=item.get("title", "Không có tiêu đề"),
                artist=item.get("uploader") or item.get("channel") or "",
                source=source,
                webpage_url=webpage_url,
                duration=int(item.get("duration") or 0),
                thumbnail_url=_entry_thumbnail(item),
            )
        )
    return tracks


def download_thumbnail(url: str) -> bytes:
    if not url:
        return b""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*"})
    with urlopen(request, timeout=10) as response:
        return response.read(2_000_000)


def load_track_thumbnail(track: Track, refresh: bool = False) -> tuple[str, bytes]:
    thumbnail_url = "" if refresh else track.thumbnail_url
    if not thumbnail_url:
        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 15,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(track.webpage_url, download=False) or {}
        thumbnail_url = _entry_thumbnail(info)
    if not thumbnail_url:
        raise RuntimeError("Nguồn không trả về ảnh bìa.")
    return thumbnail_url, download_thumbnail(thumbnail_url)


def search_everywhere(query: str) -> tuple[list[Track], list[str]]:
    results: list[Track] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(search_provider, query, "YouTube"): "YouTube",
            executor.submit(search_provider, query, "SoundCloud"): "SoundCloud",
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                results.extend(future.result())
            except Exception as exc:
                errors.append(f"{source}: {exc}")
    order = {"YouTube": 0, "SoundCloud": 1}
    results.sort(key=lambda track: (order.get(track.source, 99), track.label.lower()))
    return results, errors


def resolve_stream(track: Track) -> tuple[str, int, dict[str, str]]:
    target = track.webpage_url
    if track.source == "Spotify":
        matches = search_provider(track.resolver_query, "YouTube")
        if not matches:
            raise RuntimeError("Không tìm thấy bản YouTube tương ứng cho bài Spotify này.")
        target = matches[0].webpage_url
    options = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 20,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(target, download=False) or {}
    stream_url = info.get("url")
    if not stream_url:
        raise RuntimeError("Nguồn nhạc không trả về được luồng audio.")
    headers = {str(key): str(value) for key, value in info.get("http_headers", {}).items()}
    return stream_url, int(info.get("duration") or track.duration or 0), headers


class PlayerSignals(QObject):
    ended = Signal()
    failed = Signal()


class VlcPlayer:
    def __init__(self) -> None:
        self._configure_windows_vlc()
        self.signals = PlayerSignals()
        try:
            self.instance = vlc.Instance("--no-video", "--quiet", "--network-caching=1000")
            self.player = self.instance.media_player_new()
        except Exception as exc:
            raise RuntimeError("Không khởi tạo được VLC. Hãy cài VLC Media Player bản desktop.") from exc
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, lambda _event: self.signals.ended.emit())
        events.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda _event: self.signals.failed.emit())

    @staticmethod
    def _configure_windows_vlc() -> None:
        if sys.platform != "win32":
            return
        roots = [os.getenv("ProgramFiles", ""), os.getenv("ProgramFiles(x86)", ""), os.getenv("VLC_HOME", "")]
        for root in roots:
            candidate = Path(root) / "VideoLAN" / "VLC" if root and root != os.getenv("VLC_HOME") else Path(root)
            if (candidate / "libvlc.dll").exists():
                os.add_dll_directory(str(candidate))
                return

    def play(self, url: str, headers: dict[str, str]) -> None:
        media = self.instance.media_new(url)
        media.add_option(":network-caching=1000")
        if headers.get("User-Agent"):
            media.add_option(f":http-user-agent={headers['User-Agent']}")
        if headers.get("Referer"):
            media.add_option(f":http-referrer={headers['Referer']}")
        self.player.set_media(media)
        if self.player.play() == -1:
            raise RuntimeError("VLC không thể bắt đầu luồng audio này.")

    def stop(self) -> None:
        self.player.stop()

    def toggle_pause(self) -> None:
        self.player.pause()

    def set_time(self, milliseconds: int) -> None:
        self.player.set_time(max(0, milliseconds))

    def time(self) -> int:
        return max(0, self.player.get_time())

    def length(self) -> int:
        return max(0, self.player.get_length())

    def set_volume(self, volume: int) -> None:
        self.player.audio_set_volume(max(0, min(100, volume)))

    def is_playing(self) -> bool:
        return bool(self.player.is_playing())

    def close(self) -> None:
        self.player.stop()
        self.player.release()
        self.instance.release()


ART_PALETTE = ("#c96442", "#d97757", "#e0a458", "#8a9a5b", "#5d7a3a", "#3d3929", "#e8e5d9")


def art_pixmap(seed: str, size: int) -> QPixmap:
    rng = random.Random(seed)
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(rng.choice(("#f0eee6", "#e8e5d9", "#efe3d3"))))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    for _ in range(4):
        color = QColor(rng.choice(ART_PALETTE))
        color.setAlpha(rng.randint(150, 230))
        painter.setBrush(color)
        radius = size * rng.uniform(0.18, 0.45)
        painter.drawEllipse(QPointF(rng.uniform(0, size), rng.uniform(0, size)), radius, radius)
    painter.end()
    return pixmap


def fade_in(widget: QWidget, ms: int = 240, delay: int = 0) -> None:
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0)
    widget.setGraphicsEffect(effect)
    group = QSequentialAnimationGroup(widget)
    group.addPause(delay)
    fade = QPropertyAnimation(effect, b"opacity")
    fade.setDuration(ms)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)
    group.addAnimation(fade)
    group.finished.connect(lambda: widget.setGraphicsEffect(None))
    group.start(QSequentialAnimationGroup.DeletionPolicy.DeleteWhenStopped)


class Equalizer(QWidget):
    """Bars bounce only while playing; timer is stopped otherwise (idle CPU stays ~0)."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(18, 12)
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def set_active(self, active: bool) -> None:
        self.timer.start(90) if active else self.timer.stop()
        self.update()

    def _tick(self) -> None:
        self.phase += 0.7
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACCENT))
        live = self.timer.isActive()
        for i in range(4):
            height = 3 + 8 * abs(math.sin(self.phase + i * 1.3)) if live else 3
            painter.drawRoundedRect(QRectF(i * 5, 12 - height, 3, height), 1.5, 1.5)
        painter.end()


class TrackCard(QFrame):
    def __init__(self, track: Track) -> None:
        super().__init__()
        self.setObjectName("trackCard")
        self.thumbnail_url = track.thumbnail_url
        self.thumbnail_key = track.thumbnail_url or track.webpage_url
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        source_codes = {"YouTube": "YT", "SoundCloud": "SC", "Spotify": "SP"}
        self.thumbnail = QLabel()
        self.thumbnail.setObjectName("trackThumbnail")
        self.thumbnail.setFixedSize(46, 46)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setPixmap(art_pixmap(track.title, 48))
        row.addWidget(self.thumbnail)
        text = QVBoxLayout()
        text.setSpacing(2)
        title = QLabel(track.title)
        title.setObjectName("trackTitle")
        title.setWordWrap(True)
        subtitle = QLabel(f"{track.artist or 'Unknown artist'}  •  {format_time(track.duration)}")
        subtitle.setObjectName("trackSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        row.addLayout(text, 1)
        source = QLabel(source_codes.get(track.source, "•"))
        source.setObjectName(f"source{track.source}")
        source.setAlignment(Qt.AlignCenter)
        source.setFixedSize(30, 24)
        row.addWidget(source, 0, Qt.AlignVCenter)

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        size = self.thumbnail.size()
        scaled = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
        left = max(0, (scaled.width() - size.width()) // 2)
        top = max(0, (scaled.height() - size.height()) // 2)
        self.thumbnail.setPixmap(scaled.copy(left, top, size.width(), size.height()))

    @staticmethod
    def _placeholder_pixmap() -> QPixmap:
        return art_pixmap("pulse", 48)


class GlassBackdrop(QWidget):
    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#faf9f5"))
        for x, y, color in ((1.0, 0.0, "#c96442"), (0.0, 1.0, "#e0a458")):
            glow = QRadialGradient(self.width() * x, self.height() * y, max(self.width(), self.height()) * 0.7)
            tint = QColor(color)
            tint.setAlpha(46)
            glow.setColorAt(0, tint)
            tint.setAlpha(0)
            glow.setColorAt(1, tint)
            painter.fillRect(self.rect(), glow)
        painter.end()


def format_time(seconds: int | float) -> str:
    total = max(0, int(seconds))
    hours, total = divmod(total, 3600)
    minutes, seconds = divmod(total, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def shuffle_tracks(tracks: list[Track], rng: random.Random | None = None) -> list[Track]:
    shuffled = list(tracks)
    (rng or random).shuffle(shuffled)
    return shuffled


class MusicWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont("Segoe UI"))
        self.setWindowTitle("Pulse Music")
        self.resize(NANO_SIZE)
        self.setMinimumSize(360, 240)
        self.library = LibraryStore()
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(3)
        self.pool.setExpiryTimeout(1500)
        self.workers: list[Worker] = []
        self.notifications: list[str] = []
        self.tracks: list[Track] = []
        self.thumbnail_cache: dict[str, QPixmap] = {}
        self.thumbnail_inflight: set[str] = set()
        self.thumbnail_retries: dict[str, int] = {}
        self.current_index = -1
        self.current_playlist_name = ""
        self.search_generation = 0
        self.manual_stop = False
        self.playback_active = False
        self.compact_mode = True
        self.dragging_timeline = False
        self.current_duration_ms = 0
        self.player = VlcPlayer()
        self.player.signals.ended.connect(self._on_ended)
        self.player.signals.failed.connect(self._on_player_error)
        self._build_ui()
        self._apply_style()
        self._refresh_playlist_sidebar()
        self.notification_timer = QTimer(self)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.notification_toast.hide)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_player)

    def _build_ui(self) -> None:
        container = GlassBackdrop()
        self.setCentralWidget(container)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)
        self.pages = QStackedWidget()
        outer.addWidget(self.pages)
        full_view = QWidget()
        self.pages.addWidget(full_view)
        full_layout = QVBoxLayout(full_view)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(0)
        shell = QHBoxLayout()
        shell.setSpacing(0)
        shell.addWidget(self._build_sidebar())

        main = QWidget()
        root = QVBoxLayout(main)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        header = QHBoxLayout()
        location = QVBoxLayout()
        self.breadcrumb = QLabel("Khám phá / Tìm kiếm")
        self.breadcrumb.setObjectName("eyebrow")
        location.addWidget(self.breadcrumb)
        self.page_title = QLabel("KHÁM PHÁ & TÌM KIẾM")
        self.page_title.setObjectName("pageTitle")
        location.addWidget(self.page_title)
        header.addLayout(location)
        header.addStretch()
        self.connection = QLabel("●  HI-RES AUDIO")
        self.connection.setObjectName("connection")
        header.addWidget(self.connection, 0, Qt.AlignBottom)
        self.notification_button = QPushButton("Thông báo")
        self.notification_button.setObjectName("notificationButton")
        self.notification_button.setIcon(IconFactory.icon("bell", "#3d3929"))
        self.notification_button.setIconSize(QSize(16, 16))
        self.notification_button.clicked.connect(self.toggle_notifications)
        header.addWidget(self.notification_button, 0, Qt.AlignBottom)
        self.expand_button = QPushButton("PLAYER")
        self.expand_button.setObjectName("modeButton")
        self.expand_button.setIcon(IconFactory.icon("collapse", "#c96442"))
        self.expand_button.setIconSize(QSize(14, 14))
        self.expand_button.setToolTip("Switch to the compact player")
        self.expand_button.clicked.connect(self.toggle_compact_mode)
        header.addWidget(self.expand_button, 0, Qt.AlignBottom)
        root.addLayout(header)

        self.notification_toast = QFrame()
        self.notification_toast.setObjectName("notificationToast")
        toast_layout = QHBoxLayout(self.notification_toast)
        toast_layout.setContentsMargins(13, 9, 13, 9)
        toast_title = QLabel("THÔNG BÁO")
        toast_title.setObjectName("toastTitle")
        self.notification_toast_label = QLabel()
        self.notification_toast_label.setWordWrap(True)
        toast_layout.addWidget(toast_title)
        toast_layout.addWidget(self.notification_toast_label, 1)
        self.notification_toast.hide()
        root.addWidget(self.notification_toast)

        self.notification_panel = QFrame()
        self.notification_panel.setObjectName("notificationPanel")
        panel_layout = QVBoxLayout(self.notification_panel)
        panel_layout.setContentsMargins(13, 12, 13, 12)
        panel_header = QHBoxLayout()
        panel_title = QLabel("LỊCH SỬ THÔNG BÁO")
        panel_title.setObjectName("sectionTitle")
        panel_header.addWidget(panel_title)
        panel_header.addStretch()
        close_notifications = QToolButton()
        close_notifications.setObjectName("closeButton")
        close_notifications.setIcon(IconFactory.icon("close", "#3d3929"))
        close_notifications.setIconSize(QSize(15, 15))
        close_notifications.setToolTip("Đóng thông báo")
        close_notifications.clicked.connect(self.toggle_notifications)
        panel_header.addWidget(close_notifications)
        panel_layout.addLayout(panel_header)
        self.notification_list = QListWidget()
        self.notification_list.setObjectName("notificationList")
        self.notification_list.setMaximumHeight(150)
        panel_layout.addWidget(self.notification_list)
        self.notification_panel.hide()
        root.addWidget(self.notification_panel)

        self.playlist_header = QFrame()
        self.playlist_header.setObjectName("playlistHeader")
        self._add_shadow(self.playlist_header)
        playlist_header_layout = QHBoxLayout(self.playlist_header)
        playlist_header_layout.setContentsMargins(14, 14, 14, 14)
        playlist_header_layout.setSpacing(14)
        self.playlist_cover = QLabel()
        self.playlist_cover.setObjectName("playlistCover")
        self.playlist_cover.setFixedSize(148, 148)
        self.playlist_cover.setAlignment(Qt.AlignCenter)
        playlist_header_layout.addWidget(self.playlist_cover)
        playlist_info = QVBoxLayout()
        playlist_info.setSpacing(4)
        playlist_kicker = QLabel("PLAYLIST")
        playlist_kicker.setObjectName("eyebrow")
        playlist_info.addWidget(playlist_kicker)
        self.playlist_name = QLabel()
        self.playlist_name.setObjectName("playlistName")
        self.playlist_name.setWordWrap(True)
        playlist_info.addWidget(self.playlist_name)
        self.playlist_meta = QLabel()
        self.playlist_meta.setObjectName("muted")
        playlist_info.addWidget(self.playlist_meta)
        playlist_info.addStretch()
        playlist_actions = QHBoxLayout()
        playlist_actions.setSpacing(8)
        playlist_actions.addStretch()
        self.play_playlist_button = QPushButton("Phát playlist")
        self.play_playlist_button.setObjectName("playlistPlayButton")
        self.play_playlist_button.setIcon(IconFactory.icon("play", "#ffffff"))
        self.play_playlist_button.setIconSize(QSize(16, 16))
        self.play_playlist_button.clicked.connect(self.play_playlist)
        playlist_actions.addWidget(self.play_playlist_button)
        self.shuffle_playlist_button = QPushButton("Trộn playlist")
        self.shuffle_playlist_button.setObjectName("playlistEditButton")
        self.shuffle_playlist_button.setIcon(IconFactory.icon("shuffle", "#3d3929"))
        self.shuffle_playlist_button.setIconSize(QSize(16, 16))
        self.shuffle_playlist_button.clicked.connect(self.shuffle_playlist)
        playlist_actions.addWidget(self.shuffle_playlist_button)
        self.edit_cover_button = QPushButton("Đổi ảnh bìa")
        self.edit_cover_button.setObjectName("playlistEditButton")
        self.edit_cover_button.setIcon(IconFactory.icon("image", "#3d3929"))
        self.edit_cover_button.setIconSize(QSize(16, 16))
        self.edit_cover_button.clicked.connect(self.change_playlist_cover)
        playlist_actions.addWidget(self.edit_cover_button)
        playlist_info.addLayout(playlist_actions)
        playlist_header_layout.addLayout(playlist_info, 1)
        self.playlist_header.hide()
        root.addWidget(self.playlist_header)

        self.search_panel = QWidget()
        search = QHBoxLayout(self.search_panel)
        search.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm bài hát, nghệ sĩ hoặc album…")
        self.search_input.returnPressed.connect(self.search)
        search.addWidget(self.search_input, 1)
        self.search_button = QPushButton("Tìm mọi nguồn")
        self.search_button.setObjectName("searchButton")
        self.search_button.setIcon(IconFactory.icon("search", "#ffffff"))
        self.search_button.setIconSize(QSize(16, 16))
        self.search_button.clicked.connect(self.search)
        search.addWidget(self.search_button)
        root.addWidget(self.search_panel)

        self.result_header = QWidget()
        result_header = QHBoxLayout(self.result_header)
        result_header.setContentsMargins(0, 0, 0, 0)
        self.result_section_title = QLabel("KẾT QUẢ TỪ MỌI NGUỒN")
        self.result_section_title.setObjectName("sectionTitle")
        result_header.addWidget(self.result_section_title)
        result_header.addStretch()
        self.result_count = QLabel("Chờ tìm kiếm")
        self.result_count.setObjectName("muted")
        result_header.addWidget(self.result_count)
        root.addWidget(self.result_header)

        self.results = QListWidget()
        self.results.setObjectName("results")
        self.results.setSpacing(7)
        self.results.itemClicked.connect(self.play_selected)
        self.results.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.show_track_context_menu)
        self.results.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.results.model().rowsMoved.connect(self._on_playlist_reordered)
        self.thumbnail_queue_timer = QTimer(self)
        self.thumbnail_queue_timer.setSingleShot(True)
        self.thumbnail_queue_timer.timeout.connect(self._queue_visible_thumbnails)
        self.results.verticalScrollBar().valueChanged.connect(
            lambda _value: self.thumbnail_queue_timer.start(100)
        )
        root.addWidget(self.results, 5)

        player = QFrame()
        player.setObjectName("playerShell")
        player_layout = QHBoxLayout(player)
        player_layout.setContentsMargins(20, 8, 20, 8)
        player_layout.setSpacing(18)
        self.now_playing = QLabel("Chưa có bài nào được phát")
        self.now_playing.setObjectName("nowPlaying")
        self.now_playing.setMinimumWidth(145)
        self.now_playing.setMaximumWidth(230)
        player_layout.addWidget(self.now_playing)
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 1)
        self.timeline.sliderPressed.connect(self._begin_seek)
        self.timeline.sliderReleased.connect(self._end_seek)
        time_row = QHBoxLayout()
        self.elapsed = QLabel("0:00")
        self.elapsed.setObjectName("muted")
        self.total = QLabel("0:00")
        self.total.setObjectName("muted")
        time_row.addWidget(self.elapsed)
        time_row.addWidget(self.timeline, 1)
        time_row.addWidget(self.total)
        playback = QVBoxLayout()
        playback.setSpacing(0)
        playback.addLayout(time_row)
        controls = QHBoxLayout()
        controls.setSpacing(7)
        self._add_control(controls, "previous", "Bài trước", self.previous)
        self._add_control(controls, "rewind", "Lùi 10 giây", lambda: self.seek_relative(-10_000))
        self.play_button = QToolButton()
        self.play_button.setObjectName("primaryControl")
        self._set_play_button(False)
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        self._add_control(controls, "forward", "Tới 10 giây", lambda: self.seek_relative(10_000))
        self._add_control(controls, "next", "Bài sau", self.next_track)
        self._add_control(controls, "stop", "Dừng", self.stop)
        controls.addStretch()
        volume_label = QLabel()
        volume_label.setPixmap(IconFactory.pixmap("volume", "#3d3929"))
        volume_label.setToolTip("Âm lượng")
        controls.addWidget(volume_label)
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(85)
        self.volume.setFixedWidth(100)
        self.volume.valueChanged.connect(self.player.set_volume)
        controls.addWidget(self.volume)
        playback.addLayout(controls)
        player_layout.addLayout(playback, 1)
        shell.addWidget(main, 1)
        full_layout.addLayout(shell, 1)
        full_layout.addWidget(player)
        self.compact_view = self._build_compact_view()
        self.pages.addWidget(self.compact_view)
        self.pages.setCurrentWidget(self.compact_view)
        self._play_icon_state = None
        self._set_play_button(False)

    def _build_compact_view(self) -> QWidget:
        view = QFrame()
        view.setObjectName("nanoPanel")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)

        header = QHBoxLayout()
        self.nano_brand = QLabel("PULSE / RADIO")
        self.nano_brand.setObjectName("nanoBrand")
        header.addWidget(self.nano_brand)
        header.addStretch()
        self.collapse_button = QToolButton()
        self.collapse_button.setObjectName("nanoExpand")
        self.collapse_button.setIcon(IconFactory.icon("expand", "#c96442"))
        self.collapse_button.setToolTip("Open search and library")
        self.collapse_button.setAccessibleName("Open search and library")
        self.collapse_button.clicked.connect(self.toggle_compact_mode)
        header.addWidget(self.collapse_button)
        layout.addLayout(header)

        display = QFrame()
        display.setObjectName("nanoDisplay")
        display.setFixedHeight(88)
        display_layout = QHBoxLayout(display)
        display_layout.setContentsMargins(8, 8, 8, 8)
        display_layout.setSpacing(10)
        self.nano_cover = QLabel()
        self.nano_cover.setObjectName("nanoCover")
        self.nano_cover.setFixedSize(64, 64)
        self.nano_cover.setAlignment(Qt.AlignCenter)
        self.nano_cover.setPixmap(TrackCard._placeholder_pixmap().scaled(64, 64, Qt.KeepAspectRatio, Qt.FastTransformation))
        display_layout.addWidget(self.nano_cover)
        text = QVBoxLayout()
        text.setSpacing(4)
        self.nano_status = QLabel("READY  /  NO TRACK")
        self.nano_status.setObjectName("nanoStatus")
        self.nano_status.setFont(QFont("Consolas"))
        text.addStretch(1)
        self.equalizer = Equalizer()
        status_row = QHBoxLayout()
        status_row.addWidget(self.nano_status)
        status_row.addWidget(self.equalizer)
        status_row.addStretch(1)
        text.addLayout(status_row)
        self.nano_title = QLabel("Chưa phát bài")
        self.nano_title.setObjectName("nanoTitle")
        self.nano_title.setWordWrap(False)
        self.nano_title.setMinimumWidth(0)
        self.nano_artist = QLabel("Tìm nhạc trong thư viện mở rộng")
        self.nano_artist.setObjectName("nanoArtist")
        self.nano_artist.setWordWrap(False)
        text.addWidget(self.nano_title)
        text.addWidget(self.nano_artist)
        text.addStretch(1)
        display_layout.addLayout(text, 1)
        layout.addWidget(display)

        time_row = QHBoxLayout()
        self.nano_elapsed = QLabel("0:00")
        self.nano_elapsed.setObjectName("nanoTime")
        self.nano_elapsed.setFont(QFont("Consolas"))
        self.nano_timeline = QSlider(Qt.Horizontal)
        self.nano_timeline.setRange(0, 1)
        self.nano_timeline.setObjectName("nanoTimeline")
        self.nano_timeline.sliderPressed.connect(self._begin_seek)
        self.nano_timeline.sliderReleased.connect(self._end_seek)
        self.nano_total = QLabel("0:00")
        self.nano_total.setObjectName("nanoTime")
        self.nano_total.setFont(QFont("Consolas"))
        time_row.addWidget(self.nano_elapsed)
        time_row.addWidget(self.nano_timeline, 1)
        time_row.addWidget(self.nano_total)
        layout.addLayout(time_row)

        controls = QHBoxLayout()
        controls.setSpacing(4)
        self._add_nano_control(controls, "previous", "Previous track", self.previous)
        self._add_nano_control(controls, "rewind", "Back 10 seconds", lambda: self.seek_relative(-10_000))
        self.nano_play_button = QToolButton()
        self.nano_play_button.setObjectName("nanoPlay")
        self.nano_play_button.setFixedSize(36, 32)
        self.nano_play_button.setToolTip("Play")
        self.nano_play_button.setAccessibleName("Play or pause")
        self.nano_play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.nano_play_button)
        self._add_nano_control(controls, "forward", "Forward 10 seconds", lambda: self.seek_relative(10_000))
        self._add_nano_control(controls, "next", "Next track", self.next_track)
        self._add_nano_control(controls, "stop", "Stop", self.stop)
        controls.addStretch()
        self.nano_volume = QSlider(Qt.Horizontal)
        self.nano_volume.setObjectName("nanoVolume")
        self.nano_volume.setRange(0, 100)
        self.nano_volume.setValue(85)
        self.nano_volume.setFixedWidth(72)
        self.nano_volume.setToolTip("Volume")
        self.nano_volume.valueChanged.connect(self.player.set_volume)
        self.nano_volume.valueChanged.connect(self.volume.setValue)
        self.volume.valueChanged.connect(self.nano_volume.setValue)
        controls.addWidget(self.nano_volume)
        layout.addLayout(controls)
        self.nano_volume.setValue(self.volume.value())
        return view

    def _add_nano_control(
        self, layout: QHBoxLayout, icon: str, tip: str, callback: Callable[[], None]
    ) -> None:
        button = QToolButton()
        button.setObjectName("nanoControl")
        button.setFixedSize(28, 32)
        button.setIcon(IconFactory.icon(icon, "#3d3929"))
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def toggle_compact_mode(self) -> None:
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.pages.setCurrentWidget(self.compact_view)
            self.setMinimumSize(360, 240)
            self.resize(NANO_SIZE)
            self.expand_button.setToolTip("Open the compact player")
        else:
            self.pages.setCurrentWidget(self.pages.widget(0))
            self.setMinimumSize(820, 640)
            self.resize(EXPANDED_SIZE)
            self.expand_button.setToolTip("Switch to the compact player")
        fade_in(self.pages.currentWidget(), 280)
        self._sync_compact_track()

    def _sync_compact_track(self) -> None:
        if not hasattr(self, "nano_title"):
            return
        if not 0 <= self.current_index < len(self.tracks):
            self.nano_title.setText("Chưa phát bài")
            self.nano_artist.setText("Tìm nhạc trong thư viện mở rộng")
            self.nano_status.setText("READY  /  NO TRACK")
            self.nano_cover.setPixmap(
                TrackCard._placeholder_pixmap().scaled(64, 64, Qt.KeepAspectRatio, Qt.FastTransformation)
            )
            return
        track = self.tracks[self.current_index]
        self.nano_title.setText(track.title)
        self.nano_title.setToolTip(track.title)
        self.nano_artist.setText(track.artist or track.source)
        state = "PLAYING" if self.playback_active else "PAUSED"
        self.nano_status.setText(f"{state}  /  {track.source.upper()}")
        pixmap = self.thumbnail_cache.get(track.thumbnail_url or track.webpage_url)
        if pixmap is not None:
            self.nano_cover.setPixmap(
                pixmap.scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
            )
        else:
            self.nano_cover.setPixmap(
                TrackCard._placeholder_pixmap().scaled(64, 64, Qt.KeepAspectRatio, Qt.FastTransformation)
            )

    def _sync_player_polling(self) -> None:
        if self.playback_active and not self.isMinimized():
            if not self.timer.isActive():
                self.timer.start(500)
        else:
            self.timer.stop()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(198)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(8)
        brand_row = QHBoxLayout()
        brand_row.setSpacing(9)
        mark = QLabel()
        mark.setObjectName("appMark")
        mark.setPixmap(IconFactory.pixmap("pulse", ACCENT))
        mark.setFixedSize(24, 24)
        brand_row.addWidget(mark)
        brand = QLabel("Pulse")
        brand.setObjectName("sideBrand")
        brand_row.addWidget(brand)
        brand_row.addStretch()
        layout.addLayout(brand_row)
        caption = QLabel("YOUR LISTENING SPACE")
        caption.setObjectName("sideCaption")
        layout.addWidget(caption)
        layout.addSpacing(18)
        self.discover_button = self._sidebar_button("Khám phá / Discover", "discover", "navActive")
        self.discover_button.clicked.connect(self.show_discover)
        layout.addWidget(self.discover_button)
        self.recent_button = self._sidebar_button("Nghe gần đây", "history", "navItem")
        self.recent_button.clicked.connect(self.show_recent)
        layout.addWidget(self.recent_button)
        library_title = QLabel("PLAYLISTS")
        library_title.setObjectName("sideCaption")
        layout.addWidget(library_title)
        self.playlist_layout = QVBoxLayout()
        self.playlist_layout.setSpacing(4)
        self.playlist_buttons: dict[str, QPushButton] = {}
        layout.addLayout(self.playlist_layout)
        create_playlist = self._sidebar_button("Create playlist", "plus", "createPlaylist")
        create_playlist.clicked.connect(self.create_playlist)
        layout.addWidget(create_playlist)
        layout.addStretch()
        source_title = QLabel("AUDIO SOURCES")
        source_title.setObjectName("sideCaption")
        layout.addWidget(source_title)
        for source in ("YouTube", "SoundCloud", "Lossless stream"):
            source_label = QLabel(source)
            source_label.setObjectName("sourceLine")
            layout.addWidget(source_label)
        return sidebar

    @staticmethod
    def _add_shadow(widget: QWidget) -> None:
        widget.setGraphicsEffect(None)

    def _sidebar_button(self, text: str, icon_name: str, object_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setIcon(IconFactory.icon(icon_name, "#3d3929"))
        button.setIconSize(QSize(17, 17))
        return button

    def _add_control(self, layout: QHBoxLayout, icon_name: str, tip: str, callback: Callable[[], None]) -> None:
        button = QToolButton()
        button.setIcon(IconFactory.icon(icon_name))
        button.setIconSize(QSize(18, 18))
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        button.setObjectName("control")
        button.clicked.connect(callback)
        layout.addWidget(button)

    def _set_play_button(self, playing: bool) -> None:
        if getattr(self, "_play_icon_state", None) == playing:
            return
        self._play_icon_state = playing
        if hasattr(self, "equalizer"):
            self.equalizer.set_active(playing)
        self.play_button.setIcon(IconFactory.icon("pause" if playing else "play", "#ffffff"))
        self.play_button.setIconSize(QSize(19, 19))
        if hasattr(self, "nano_play_button"):
            self.nano_play_button.setIcon(IconFactory.icon("pause" if playing else "play", "#ffffff"))
            self.nano_play_button.setIconSize(QSize(18, 18))
            self.nano_play_button.setToolTip("Pause" if playing else "Play")
        self.play_button.setToolTip("Tạm dừng" if playing else "Phát")
        self.play_button.setAccessibleName(self.play_button.toolTip())

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: transparent; color: {TEXT}; font-family: "Segoe UI"; }}
            QStackedWidget, QLabel {{ background: transparent; }}
            QToolTip {{ background: #141413; color: #faf9f5; border: none; padding: 4px 8px; }}
            QFrame#sidebar {{ background: #f0eee6; border: none; border-right: 1px solid #e5e2d6; border-radius: 0; }}
            QLabel#appMark {{ color: {ACCENT}; font-size: 21px; font-weight: 700; }}
            QLabel#sideBrand {{ color: {TEXT}; font-family: Georgia, serif; font-size: 20px; font-weight: 500; }}
            QLabel#sideCaption {{ color: #83827d; font-size: 10px; font-weight: 600; letter-spacing: .6px; }}
            QPushButton#navItem, QPushButton#navActive, QPushButton#playlistItem, QPushButton#playlistActive {{ border: none; border-radius: 8px; padding: 0 10px; text-align: left; min-height: 34px; font-size: 12px; font-weight: 500; }}
            QPushButton#navItem, QPushButton#playlistItem {{ background: transparent; color: #3d3929; }}
            QPushButton#navItem:hover, QPushButton#playlistItem:hover {{ background: #e8e5d9; }}
            QPushButton#navActive, QPushButton#playlistActive {{ background: #e3dfd0; color: {TEXT}; font-weight: 600; }}
            QPushButton#createPlaylist {{ background: transparent; border: 1px dashed #c9c5b5; border-radius: 8px; min-height: 34px; color: #3d3929; font-size: 11px; font-weight: 600; }}
            QPushButton#createPlaylist:hover {{ background: #e8e5d9; border-color: {ACCENT}; }}
            QLabel#sourceLine {{ color: #83827d; font-size: 10px; padding: 4px 0 4px 9px; }}
            QLabel#eyebrow {{ color: #83827d; font-size: 11px; font-weight: 500; }}
            QLabel#pageTitle {{ color: {TEXT}; font-family: Georgia, serif; font-size: 30px; font-weight: 500; }}
            QLabel#connection {{ color: #5d7a3a; padding: 5px 9px; font-size: 10px; font-weight: 600; }}
            QPushButton#notificationButton, QPushButton#modeButton {{ background: #ffffff; border: 1px solid #e0ddd0; border-radius: 8px; padding: 7px 10px; color: #3d3929; font-size: 11px; font-weight: 600; min-height: 18px; }}
            QPushButton#notificationButton:hover, QPushButton#modeButton:hover {{ background: #f0eee6; }}
            QFrame#notificationToast {{ background: #fbeee8; border: 1px solid #efc9b9; border-radius: 10px; }}
            QLabel#toastTitle {{ color: {ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: .5px; }}
            QFrame#notificationPanel, QFrame#playlistHeader {{ background: #ffffff; border: 1px solid #e5e2d6; border-radius: 14px; }}
            QLabel#playlistCover {{ background: #f0eee6; border: none; border-radius: 12px; }}
            QLabel#playlistName {{ color: {TEXT}; font-family: Georgia, serif; font-size: 28px; font-weight: 500; }}
            QPushButton#playlistPlayButton, QPushButton#searchButton {{ background: {ACCENT}; border: none; border-radius: 10px; padding: 9px 16px; color: #ffffff; font-size: 11px; font-weight: 600; }}
            QPushButton#playlistPlayButton:hover, QPushButton#searchButton:hover {{ background: #b5573a; }}
            QPushButton#playlistPlayButton:disabled, QPushButton#searchButton:disabled {{ background: #e8e5d9; color: #a8a69c; }}
            QPushButton#playlistEditButton {{ background: #ffffff; border: 1px solid #e0ddd0; border-radius: 10px; padding: 9px 14px; color: #3d3929; font-size: 11px; font-weight: 600; }}
            QPushButton#playlistEditButton:hover {{ background: #f0eee6; }}
            QListWidget#notificationList {{ background: transparent; border: none; color: #3d3929; outline: none; font-size: 11px; }}
            QListWidget#notificationList::item {{ padding: 7px 5px; border-bottom: 1px solid #efede4; }}
            QToolButton#closeButton {{ background: #f0eee6; border: none; border-radius: 8px; min-width: 25px; min-height: 25px; }}
            QLineEdit {{ background: #ffffff; border: 1px solid #dcd8c9; border-radius: 12px; padding: 11px 14px; color: {TEXT}; font-size: 13px; selection-background-color: #f0cdbd; selection-color: {TEXT}; }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
            QMenu {{ background: #ffffff; border: 1px solid #e0ddd0; border-radius: 8px; padding: 5px; }}
            QMenu::item {{ color: {TEXT}; padding: 8px 26px 8px 12px; border-radius: 5px; }} QMenu::item:selected {{ background: #f0eee6; }}
            QLabel#sectionTitle {{ color: {TEXT}; font-family: Georgia, serif; font-size: 15px; font-weight: 500; }}
            QLabel#muted {{ color: {MUTED}; font-size: 11px; }}
            QListWidget#results {{ background: transparent; border: none; outline: none; }}
            QListWidget#results::item, QListWidget#results::item:selected {{ border: none; background: transparent; }}
            QFrame#trackCard {{ background: transparent; border: 1px solid transparent; border-radius: 12px; }}
            QFrame#trackCard:hover {{ background: #ffffff; border: 1px solid #e5e2d6; }}
            QLabel#trackThumbnail {{ background: #f0eee6; border: none; border-radius: 8px; }}
            QLabel#trackTitle {{ color: {TEXT}; font-size: 12px; font-weight: 600; }}
            QLabel#trackSubtitle {{ color: {MUTED}; font-size: 10px; }}
            QLabel#sourceBadge {{ background: #f0eee6; border-radius: 5px; color: #5e5d59; padding: 3px 6px; font-size: 9px; font-weight: 600; }}
            QLabel#sourceYouTube, QLabel#sourceSoundCloud, QLabel#sourceSpotify {{ color: #83827d; font-size: 9px; font-weight: 700; }}
            QLabel#nowPlaying {{ color: {TEXT}; font-size: 12px; font-weight: 600; }}
            QFrame#playerShell {{ background: #ffffff; border: none; border-top: 1px solid #e5e2d6; border-radius: 0; }}
            QSlider::groove:horizontal {{ height: 4px; background: #e5e2d6; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {ACCENT}; width: 12px; margin: -4px 0; border-radius: 6px; }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
            QToolButton#control {{ background: transparent; border: none; border-radius: 8px; min-width: 32px; min-height: 32px; }}
            QToolButton#control:hover {{ background: #f0eee6; }}
            QToolButton#primaryControl {{ background: {ACCENT}; border: none; border-radius: 18px; min-width: 36px; min-height: 36px; }}
            QToolButton#primaryControl:hover {{ background: #b5573a; }}
            QScrollBar:vertical {{ width: 6px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: #d3cfc0; border-radius: 3px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QFrame#nanoPanel {{ background: #faf9f5; border: 1px solid #e5e2d6; border-radius: 14px; }}
            QFrame#nanoDisplay {{ background: #f0eee6; border: none; border-radius: 12px; }}
            QLabel#nanoBrand {{ color: #83827d; font-size: 10px; font-weight: 600; letter-spacing: .6px; }}
            QLabel#nanoStatus {{ color: {ACCENT}; font-size: 9px; font-weight: 700; }}
            QLabel#nanoTitle {{ color: {TEXT}; font-family: Georgia, serif; font-size: 14px; font-weight: 500; }}
            QLabel#nanoArtist {{ color: #5e5d59; font-size: 10px; }}
            QLabel#nanoTime {{ color: #83827d; font-size: 9px; }}
            QLabel#nanoCover {{ background: #e3dfd0; border: none; border-radius: 8px; }}
            QToolButton#nanoExpand {{ background: #ffffff; border: 1px solid #e0ddd0; border-radius: 8px; min-width: 25px; min-height: 24px; }}
            QToolButton#nanoExpand:hover {{ background: #f0eee6; }}
            QToolButton#nanoControl {{ background: #ffffff; border: 1px solid #e0ddd0; border-radius: 8px; }}
            QToolButton#nanoControl:hover {{ background: #f0eee6; }}
            QToolButton#nanoPlay {{ background: {ACCENT}; border: none; border-radius: 8px; }}
            QToolButton#nanoPlay:hover {{ background: #b5573a; }}
            QToolButton:focus, QPushButton:focus {{ outline: none; }}
        """)

    def notify(self, message: str) -> None:
        entry = f"{time.strftime('%H:%M')}  ·  {message}"
        self.notifications.insert(0, entry)
        self.notification_list.clear()
        self.notification_list.addItems(self.notifications)
        self.notification_toast_label.setText(message)
        self.notification_toast.show()
        fade_in(self.notification_toast, 200)
        self.notification_timer.start(3000)
        self.notification_button.setText(f"Thông báo ({len(self.notifications)})")

    def toggle_notifications(self) -> None:
        visible = not self.notification_panel.isVisible()
        self.notification_panel.setVisible(visible)
        if visible:
            self.notification_toast.hide()
            self.notification_timer.stop()
            self.notification_button.setText("Đóng thông báo")
        else:
            self.notification_button.setText(
                f"Thông báo ({len(self.notifications)})" if self.notifications else "Thông báo"
            )

    def _refresh_playlist_sidebar(self) -> None:
        while self.playlist_layout.count():
            item = self.playlist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.playlist_buttons = {}
        for name in self.library.playlist_names():
            button = QPushButton(name)
            button.setObjectName("playlistItem")
            button.setIcon(IconFactory.icon("playlist", "#3d3929"))
            button.setIconSize(QSize(16, 16))
            button.clicked.connect(lambda _checked=False, playlist=name: self.show_playlist(playlist))
            self.playlist_layout.addWidget(button)
            self.playlist_buttons[name] = button
        self._set_sidebar_active("playlist", self.current_playlist_name) if self.current_playlist_name else self._set_sidebar_active("discover")

    @staticmethod
    def _refresh_widget_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _set_sidebar_active(self, section: str, playlist_name: str = "") -> None:
        self.discover_button.setObjectName("navActive" if section == "discover" else "navItem")
        self.recent_button.setObjectName("navActive" if section == "recent" else "navItem")
        self._refresh_widget_style(self.discover_button)
        self._refresh_widget_style(self.recent_button)
        for name, button in self.playlist_buttons.items():
            button.setObjectName("playlistActive" if section == "playlist" and name == playlist_name else "playlistItem")
            self._refresh_widget_style(button)

    def create_playlist(self) -> None:
        name, accepted = QInputDialog.getText(self, "Tạo danh sách phát", "Tên danh sách phát:")
        if not accepted:
            return
        if not name.strip():
            self.notify("Tên danh sách phát không được để trống.")
            return
        if not self.library.create_playlist(name):
            self.notify("Danh sách phát này đã tồn tại.")
            return
        self._refresh_playlist_sidebar()
        self.show_playlist(name.strip())
        self.notify(f"Đã tạo danh sách phát “{name.strip()}”.")

    def show_track_context_menu(self, position: Any) -> None:
        item = self.results.itemAt(position)
        if not item:
            return
        index = item.data(Qt.UserRole)
        if not isinstance(index, int) or not 0 <= index < len(self.tracks):
            return
        track = self.tracks[index]
        self._sync_compact_track()
        self.results.setCurrentItem(item)
        menu = QMenu(self)
        if self.current_playlist_name:
            up_action = menu.addAction("Đưa bài lên")
            up_action.setIcon(IconFactory.icon("up", "#3d3929"))
            up_action.triggered.connect(lambda: self.move_track_in_playlist(track, -1))
            down_action = menu.addAction("Đưa bài xuống")
            down_action.setIcon(IconFactory.icon("down", "#3d3929"))
            down_action.triggered.connect(lambda: self.move_track_in_playlist(track, 1))
            remove_action = menu.addAction("Xóa khỏi playlist này")
            remove_action.setIcon(IconFactory.icon("close", "#3d3929"))
            remove_action.triggered.connect(lambda: self.remove_track_from_playlist(track))
            menu.addSeparator()
        add_action = menu.addAction("Thêm vào playlist")
        add_action.setIcon(IconFactory.icon("plus", "#3d3929"))
        add_action.triggered.connect(lambda: self.add_track_to_playlist(track))
        menu.exec(self.results.viewport().mapToGlobal(position))

    def add_track_to_playlist(self, track: Track) -> None:
        names = self.library.playlist_names()
        if not names:
            self.notify("Hãy tạo danh sách phát trước.")
            return
        name, accepted = QInputDialog.getItem(self, "Thêm vào playlist", "Danh sách phát:", names, 0, False)
        if not accepted:
            return
        if self.library.add_to_playlist(name, track):
            if self.current_playlist_name == name:
                self.show_playlist(name)
            self.notify(f"Đã thêm “{track.title}” vào {name}.")
        else:
            self.notify("Bài này đã có trong playlist đó.")

    def remove_track_from_playlist(self, track: Track) -> None:
        name = self.current_playlist_name
        if not name:
            return
        if not self.library.remove_from_playlist(name, track.webpage_url):
            self.notify("Không tìm thấy bài này trong playlist.")
            return
        self.show_playlist(name)
        self.notify(f"Đã xóa “{track.title}” khỏi {name}.")

    def move_track_in_playlist(self, track: Track, offset: int) -> None:
        name = self.current_playlist_name
        if not name or not self.library.move_playlist_track(name, track.webpage_url, offset):
            return
        self.show_playlist(name)
        self.notify("Đã cập nhật thứ tự playlist.")

    def show_discover(self) -> None:
        self._hide_playlist_header()
        self._set_reordering_enabled(False)
        self._set_sidebar_active("discover")
        self.breadcrumb.setText("Khám phá / Tìm kiếm")
        self.page_title.setText("KHÁM PHÁ & TÌM KIẾM")
        self.search_panel.show()
        self.result_section_title.setText("KẾT QUẢ TỪ MỌI NGUỒN")
        self.search_input.setFocus()

    def show_recent(self) -> None:
        self._hide_playlist_header()
        self._set_reordering_enabled(False)
        self._set_sidebar_active("recent")
        self.breadcrumb.setText("Thư viện / Nghe gần đây")
        tracks = self.library.recent_tracks()
        self.page_title.setText("NGHE GẦN ĐÂY")
        self.search_panel.hide()
        self.result_section_title.setText("NGHE GẦN ĐÂY")
        self._render_tracks(tracks)
        self.result_count.setText(f"{len(tracks)} bài gần đây")

    def show_playlist(self, name: str) -> None:
        tracks = self.library.playlist_tracks(name)
        self.current_playlist_name = name
        self._set_reordering_enabled(True)
        self._set_sidebar_active("playlist", name)
        self.breadcrumb.setText("Thư viện / Playlist")
        self.page_title.setText("PLAYLIST")
        self.search_panel.hide()
        self.result_section_title.setText("BÀI HÁT TRONG PLAYLIST")
        self._update_playlist_header(name, tracks)
        self._render_tracks(tracks)
        self.result_count.setText(f"{len(tracks)} bài trong playlist")

    def _hide_playlist_header(self) -> None:
        self.current_playlist_name = ""
        self.playlist_header.hide()

    def _set_reordering_enabled(self, enabled: bool) -> None:
        self.results.setDragEnabled(enabled)
        self.results.setAcceptDrops(enabled)
        self.results.setDropIndicatorShown(enabled)
        self.results.setDragDropMode(QAbstractItemView.InternalMove if enabled else QAbstractItemView.NoDragDrop)

    def _on_playlist_reordered(self, *_args: Any) -> None:
        if not self.current_playlist_name:
            return
        reordered: list[Track] = []
        for row in range(self.results.count()):
            item = self.results.item(row)
            original_index = item.data(Qt.UserRole)
            if not isinstance(original_index, int) or not 0 <= original_index < len(self.tracks):
                return
            reordered.append(self.tracks[original_index])
        if not self.library.reorder_playlist_tracks(
            self.current_playlist_name,
            [track.webpage_url for track in reordered],
        ):
            return
        self.tracks = reordered
        for row in range(self.results.count()):
            self.results.item(row).setData(Qt.UserRole, row)
        self.notify("Đã cập nhật thứ tự playlist.")

    def _update_playlist_header(self, name: str, tracks: list[Track]) -> None:
        self.playlist_name.setText(name)
        self.playlist_meta.setText(f"{len(tracks)} bài  •  Playlist cá nhân")
        self.play_playlist_button.setEnabled(bool(tracks))
        self._set_playlist_cover(name)
        self.playlist_header.show()

    def _set_playlist_cover(self, name: str) -> None:
        cover_path = self.library.playlist_cover(name)
        pixmap = QPixmap(cover_path) if cover_path and Path(cover_path).is_file() else self._default_playlist_cover(name)
        if pixmap.isNull():
            pixmap = self._default_playlist_cover(name)
        size = self.playlist_cover.size()
        scaled = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        left = max(0, (scaled.width() - size.width()) // 2)
        top = max(0, (scaled.height() - size.height()) // 2)
        self.playlist_cover.setPixmap(scaled.copy(left, top, size.width(), size.height()))

    @staticmethod
    def _default_playlist_cover(name: str) -> QPixmap:
        pixmap = art_pixmap(name, 94)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(255, 255, 255, 225))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(32)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "♪")
        painter.end()
        return pixmap

    def play_playlist(self) -> None:
        if not self.current_playlist_name:
            return
        tracks = self.library.playlist_tracks(self.current_playlist_name)
        if not tracks:
            self.notify("Playlist này chưa có bài hát.")
            return
        self._render_tracks(tracks)
        self._play_index(0)

    def shuffle_playlist(self) -> None:
        if not self.current_playlist_name:
            return
        tracks = self.library.playlist_tracks(self.current_playlist_name)
        if len(tracks) < 2:
            self.notify("Cần ít nhất 2 bài để trộn playlist.")
            return
        self._render_tracks(shuffle_tracks(tracks))
        self._play_index(0)
        self.notify("Đang phát playlist theo thứ tự ngẫu nhiên.")

    def change_playlist_cover(self) -> None:
        if not self.current_playlist_name:
            return
        cover_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh bìa playlist",
            "",
            "Ảnh (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not cover_path:
            return
        if self.library.set_playlist_cover(self.current_playlist_name, cover_path):
            self._set_playlist_cover(self.current_playlist_name)
            self.notify("Đã cập nhật ảnh bìa playlist.")

    def _render_tracks(self, tracks: list[Track]) -> None:
        self.tracks = list(tracks)
        self.current_index = -1
        self.results.clear()
        self.results.verticalScrollBar().setValue(0)
        for index, track in enumerate(self.tracks):
            card = TrackCard(track)
            thumbnail_key = card.thumbnail_key
            if thumbnail_key in self.thumbnail_cache:
                card.set_thumbnail(self.thumbnail_cache[thumbnail_key])
            item = QListWidgetItem()
            item.setData(Qt.UserRole, index)
            item.setSizeHint(card.sizeHint())
            self.results.addItem(item)
            self.results.setItemWidget(item, card)
            fade_in(card, 260, min(index, 10) * 45)
        self.thumbnail_queue_timer.start(0)

    def _queue_visible_thumbnails(self) -> None:
        if self.compact_mode or self.isMinimized():
            return
        viewport = self.results.viewport().rect()
        for row in range(self.results.count()):
            item = self.results.item(row)
            if not self.results.visualItemRect(item).intersects(viewport):
                continue
            index = item.data(Qt.UserRole)
            if not isinstance(index, int) or not 0 <= index < len(self.tracks):
                continue
            track = self.tracks[index]
            if track.thumbnail_url or track.webpage_url:
                self._queue_thumbnail(track)

    def _queue_thumbnail(self, track: Track, refresh: bool = False) -> None:
        thumbnail_key = track.thumbnail_url or track.webpage_url
        if not thumbnail_key or thumbnail_key in self.thumbnail_cache or thumbnail_key in self.thumbnail_inflight:
            return
        self.thumbnail_inflight.add(thumbnail_key)
        worker = Worker(load_track_thumbnail, track, refresh)
        self.workers.append(worker)
        worker.signals.result.connect(
            lambda payload, key=thumbnail_key, item=track: self._thumbnail_loaded(key, item, payload)
        )
        worker.signals.error.connect(
            lambda _message, key=thumbnail_key, item=track: self._thumbnail_failed(key, item)
        )
        worker.signals.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.pool.start(worker)

    def _thumbnail_loaded(self, key: str, track: Track, payload: tuple[str, bytes]) -> None:
        self.thumbnail_inflight.discard(key)
        thumbnail_url, data = payload
        pixmap = QPixmap()
        if not data or not pixmap.loadFromData(data):
            self._thumbnail_failed(key, track)
            return
        self.thumbnail_retries.pop(key, None)
        pixmap = pixmap.scaled(256, 256, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
        while len(self.thumbnail_cache) >= 120:
            self.thumbnail_cache.pop(next(iter(self.thumbnail_cache)))
        self.thumbnail_cache[key] = pixmap
        self.thumbnail_cache[thumbnail_url] = pixmap
        if 0 <= self.current_index < len(self.tracks):
            current = self.tracks[self.current_index]
            if current.webpage_url == track.webpage_url:
                self.nano_cover.setPixmap(
                    pixmap.scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.FastTransformation)
                )
        self.library.update_thumbnail(track.webpage_url, thumbnail_url)
        self.tracks = [
            replace(item, thumbnail_url=thumbnail_url) if item.webpage_url == track.webpage_url else item
            for item in self.tracks
        ]
        for index in range(self.results.count()):
            item = self.results.item(index)
            card = self.results.itemWidget(item)
            if isinstance(card, TrackCard) and card.thumbnail_key == key:
                card.set_thumbnail(pixmap)

    def _thumbnail_failed(self, key: str, track: Track) -> None:
        self.thumbnail_inflight.discard(key)
        attempts = self.thumbnail_retries.get(key, 0)
        if attempts >= 1:
            return
        self.thumbnail_retries[key] = attempts + 1
        QTimer.singleShot(1200, lambda item=track: self._queue_thumbnail(item, refresh=True))

    def _submit(self, fn: Callable[..., Any], callback: Callable[[Any], None], *args: Any) -> None:
        worker = Worker(fn, *args)
        self.workers.append(worker)
        worker.signals.result.connect(callback)
        worker.signals.error.connect(self._show_error)
        worker.signals.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.pool.start(worker)

    def search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self.search_input.setFocus()
            self.notify("Hãy nhập tên bài hát hoặc nghệ sĩ.")
            return
        self.search_generation += 1
        generation = self.search_generation
        self.search_button.setDisabled(True)
        self.search_button.setText("Đang tìm…")
        self.result_count.setText("Đang tìm YouTube + SoundCloud…")
        self._submit(search_everywhere, lambda payload: self._show_results(generation, payload), query)

    def _show_results(self, generation: int, payload: tuple[list[Track], list[str]]) -> None:
        if generation != self.search_generation:
            return
        self.search_button.setDisabled(False)
        self.search_button.setText("Tìm mọi nguồn")
        tracks, errors = payload
        self._hide_playlist_header()
        self._set_reordering_enabled(False)
        self._set_sidebar_active("discover")
        self.breadcrumb.setText("HOME  /  DISCOVER")
        self.page_title.setText("Search music")
        self.search_panel.show()
        self.result_section_title.setText("KẾT QUẢ TỪ MỌI NGUỒN")
        self._render_tracks(tracks)
        self.result_count.setText(f"{len(self.tracks)} kết quả")
        self.notify(f"Đã tìm thấy {len(self.tracks)} kết quả.")
        if errors:
            self.notify("Một vài nguồn chưa phản hồi: " + " | ".join(errors))

    def play_selected(self, item: QListWidgetItem) -> None:
        index = item.data(Qt.UserRole)
        if isinstance(index, int):
            self._play_index(index)

    def _play_index(self, index: int) -> None:
        if not 0 <= index < len(self.tracks):
            return
        self.current_index = index
        self.playback_active = False
        self.timer.stop()
        self._set_play_button(False)
        track = self.tracks[index]
        self.now_playing.setText(f"Đang tải: {track.label}")
        self._submit(resolve_stream, lambda payload: self._start_stream(index, track, payload), track)

    def _start_stream(self, index: int, track: Track, payload: tuple[str, int, dict[str, str]]) -> None:
        if index != self.current_index:
            return
        url, duration, headers = payload
        try:
            self.manual_stop = False
            self.player.play(url, headers)
            self.player.set_volume(self.volume.value())
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.current_duration_ms = duration * 1000
        self.playback_active = True
        self.library.record_recent(track)
        self.now_playing.setText(track.label)
        self._set_play_button(True)
        self._sync_compact_track()
        self._sync_player_polling()

    def toggle_play(self) -> None:
        if self.current_index < 0 and self.tracks:
            self._play_index(0)
            return
        if self.current_index < 0:
            return
        self.player.toggle_pause()
        self.playback_active = self.player.is_playing()
        self._set_play_button(self.playback_active)
        self._sync_compact_track()
        self._sync_player_polling()

    def stop(self) -> None:
        self.manual_stop = True
        self.playback_active = False
        self.timer.stop()
        self.player.stop()
        self._set_play_button(False)
        self.timeline.setValue(0)
        self.elapsed.setText("0:00")
        self.nano_timeline.setValue(0)
        self.nano_elapsed.setText("0:00")
        self._sync_compact_track()

    def previous(self) -> None:
        if self.tracks:
            self._play_index((self.current_index - 1) % len(self.tracks))

    def next_track(self) -> None:
        if self.tracks:
            self._play_index((self.current_index + 1) % len(self.tracks))

    def seek_relative(self, milliseconds: int) -> None:
        if self.current_index >= 0:
            self.player.set_time(self.player.time() + milliseconds)

    def _begin_seek(self) -> None:
        self.dragging_timeline = True

    def _end_seek(self) -> None:
        self.dragging_timeline = False
        slider = self.sender()
        if not isinstance(slider, QSlider):
            slider = self.timeline
        self.player.set_time(slider.value())

    def _refresh_player(self) -> None:
        elapsed = self.player.time()
        length = max(self.player.length(), self.current_duration_ms, 1)
        if not self.dragging_timeline:
            self.timeline.setRange(0, length)
            self.timeline.setValue(min(elapsed, length))
            self.nano_timeline.setRange(0, length)
            self.nano_timeline.setValue(min(elapsed, length))
        self.elapsed.setText(format_time(elapsed / 1000))
        self.total.setText(format_time(length / 1000))
        self.nano_elapsed.setText(format_time(elapsed / 1000))
        self.nano_total.setText(format_time(length / 1000))

    def _on_ended(self) -> None:
        self.playback_active = False
        self._sync_player_polling()
        if self.manual_stop:
            self.manual_stop = False
            return
        if self.player.is_playing():
            return
        self.next_track()

    def _on_player_error(self) -> None:
        self.playback_active = False
        self._sync_player_polling()
        self._set_play_button(False)
        self._sync_compact_track()
        self._show_error("VLC không thể phát luồng này. Hãy thử kết quả khác hoặc cập nhật yt-dlp.")

    def _show_error(self, message: str) -> None:
        self.search_button.setDisabled(False)
        self.search_button.setText("Tìm mọi nguồn")
        self.notify(message)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "connection"):
            return
        compact = self.width() < 860
        self.connection.setVisible(not compact)
        self.sidebar.setFixedWidth(178 if compact else 198)

    def closeEvent(self, event: Any) -> None:
        self.timer.stop()
        self.player.close()
        event.accept()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "timer"):
            self._sync_player_polling()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Pulse Music")
    try:
        window = MusicWindow()
    except RuntimeError as exc:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, "Pulse Music", str(exc))
        raise SystemExit(1)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
