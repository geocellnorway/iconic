# -*- coding: utf-8 -*-
# Iconic (QGIS plugin) — SVG-only

import os
import re
import json
import shutil
import zipfile
import datetime
import xml.etree.ElementTree as ET

from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    Qt, QSize, pyqtSignal, QVariant,
    QStandardPaths, QUrl, QEventLoop, QTimer, QObject, QEvent
)
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter
from qgis.PyQt.QtWidgets import (
    QAction,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolBar,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QDoubleSpinBox,
    QMessageBox,
    QFormLayout,
    QDockWidget,
    QCheckBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QAbstractItemView,
)
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import (
    QgsProject,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateTransform,
    QgsProperty,
    QgsMarkerSymbol,
    QgsSvgMarkerSymbolLayer,
    QgsSymbolLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    Qgis,
    QgsNetworkAccessManager,
    QgsMessageLog,
)
from qgis.gui import QgsMapTool, QgsMapCanvas


PLUGIN_MENU = "&Geocell"
PLUGIN_TOOLBAR = "Geocell"
DOCK_TITLE = "Iconic"
REPO_XML_URL = "https://geocell.no/iconpacks/packages.xml"


# ------------------------------------------------------------
# Qt compatibility helpers
# ------------------------------------------------------------
def qt_user_role():
    try:
        return Qt.ItemDataRole.UserRole
    except AttributeError:
        return Qt.UserRole

def qt_align_top():
    try:
        return Qt.AlignmentFlag.AlignTop
    except AttributeError:
        return Qt.AlignTop

def qt_align_hcenter():
    try:
        return Qt.AlignmentFlag.AlignHCenter
    except AttributeError:
        return Qt.AlignHCenter

def qt_left_button():
    try:
        return Qt.MouseButton.LeftButton
    except AttributeError:
        return Qt.LeftButton

def qt_right_button():
    try:
        return Qt.MouseButton.RightButton
    except AttributeError:
        return Qt.RightButton

def qt_key_escape():
    try:
        return Qt.Key.Key_Escape
    except AttributeError:
        return Qt.Key_Escape

def qt_cross_cursor():
    try:
        return Qt.CursorShape.CrossCursor
    except AttributeError:
        return Qt.CrossCursor

def qt_scrollbar_always_off():
    try:
        return Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    except AttributeError:
        return Qt.ScrollBarAlwaysOff

def qt_text_selectable_by_mouse():
    try:
        return Qt.TextInteractionFlag.TextSelectableByMouse
    except AttributeError:
        return Qt.TextSelectableByMouse

def qt_plain_text():
    try:
        return Qt.TextFormat.PlainText
    except AttributeError:
        return Qt.PlainText

def qt_transparent():
    try:
        return Qt.GlobalColor.transparent
    except AttributeError:
        return Qt.transparent

def qt_left_dock_area():
    try:
        return Qt.DockWidgetArea.LeftDockWidgetArea
    except AttributeError:
        return Qt.LeftDockWidgetArea

def qt_right_dock_area():
    try:
        return Qt.DockWidgetArea.RightDockWidgetArea
    except AttributeError:
        return Qt.RightDockWidgetArea

def qt_resize_event_type():
    try:
        return QEvent.Type.Resize
    except AttributeError:
        return QEvent.Resize

def qt_header_resize_to_contents():
    try:
        return QHeaderView.ResizeMode.ResizeToContents
    except AttributeError:
        return QHeaderView.ResizeToContents

def qt_header_stretch():
    try:
        return QHeaderView.ResizeMode.Stretch
    except AttributeError:
        return QHeaderView.Stretch

def qt_single_selection():
    try:
        return QAbstractItemView.SelectionMode.SingleSelection
    except AttributeError:
        return QAbstractItemView.SingleSelection

def qt_select_rows():
    try:
        return QAbstractItemView.SelectionBehavior.SelectRows
    except AttributeError:
        return QTableWidget.SelectRows

def qt_no_edit_triggers():
    try:
        return QAbstractItemView.EditTrigger.NoEditTriggers
    except AttributeError:
        return QTableWidget.NoEditTriggers

def qt_painter_antialiasing():
    try:
        return QPainter.RenderHint.Antialiasing
    except AttributeError:
        return QPainter.Antialiasing

def qt_exec(obj):
    try:
        return obj.exec()
    except AttributeError:
        return obj.exec_()
    
def qt_sizepolicy_expanding():
    try:
        return QSizePolicy.Policy.Expanding
    except AttributeError:
        return QSizePolicy.Expanding

def qt_sizepolicy_minimum():
    try:
        return QSizePolicy.Policy.Minimum
    except AttributeError:
        return QSizePolicy.Minimum
    
def qt_msgbox_yes():
    try:
        return QMessageBox.StandardButton.Yes
    except AttributeError:
        return QMessageBox.Yes


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
def plugin_dir() -> str:
    return os.path.dirname(__file__)

def res_path(*parts) -> str:
    return os.path.join(plugin_dir(), *parts)

def norm_rel(path: str) -> str:
    return (path or "").replace("\\", "/").lstrip("/")

def appdata_dir() -> str:
    try:
        appdata_loc = QStandardPaths.StandardLocation.AppDataLocation
    except AttributeError:
        appdata_loc = QStandardPaths.AppDataLocation

    base = QStandardPaths.writableLocation(appdata_loc)
    p = os.path.join(base, "iconic_plugin")
    os.makedirs(p, exist_ok=True)
    return p.replace("\\", "/")

def packages_root_dir() -> str:
    p = os.path.join(appdata_dir(), "packages")
    os.makedirs(p, exist_ok=True)
    return p.replace("\\", "/")

def installed_manifest_path() -> str:
    return os.path.join(appdata_dir(), "installed_packages.json").replace("\\", "/")


# ------------------------------------------------------------
# Utils
# ------------------------------------------------------------
def _norm_slug(s: str) -> str:
    t = (s or "").strip().lower()
    t = t.replace("ø", "o").replace("æ", "e").replace("å", "a")
    t = re.sub(r"\s+", "_", t)
    t = re.sub(r"[^a-z0-9_]+", "_", t).strip("_")
    return t or "ukjent"

def _norm_theme_folder(theme: str) -> str:
    return _norm_slug(theme)

def normalize_version(v: str) -> str:
    v = (v or "").strip()
    if v.lower().startswith("v"):
        v = v[1:].strip()
    return v

def _version_key(v: str):
    v = normalize_version(v)
    if not v:
        return (0,)
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except Exception:
            parts.append(0)
    return tuple(parts)

def is_newer_version(avail: str, installed: str) -> bool:
    return _version_key(avail) > _version_key(installed)

def _make_request(url: str, cache_bust: bool = True) -> QNetworkRequest:
    u = (url or "").strip()
    if cache_bust:
        sep = "&" if "?" in u else "?"
        u = f"{u}{sep}_ts={int(datetime.datetime.now().timestamp())}"

    req = QNetworkRequest(QUrl(u))
    req.setRawHeader(b"Cache-Control", b"no-cache, no-store, must-revalidate")
    req.setRawHeader(b"Pragma", b"no-cache")
    req.setRawHeader(b"Expires", b"0")
    req.setRawHeader(b"User-Agent", b"QGIS-Iconic-Plugin/3.2-qt6")
    return req


# ------------------------------------------------------------
# Map tool
# ------------------------------------------------------------
class ClickPointTool(QgsMapTool):
    clicked = pyqtSignal(QgsPointXY)
    canceled = pyqtSignal()

    def __init__(self, canvas: QgsMapCanvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(qt_cross_cursor())

    def canvasReleaseEvent(self, e):
        if e.button() == qt_right_button():
            self.canceled.emit()
            return
        if e.button() != qt_left_button():
            return
        pt = self.canvas.getCoordinateTransform().toMapCoordinates(e.pos().x(), e.pos().y())
        self.clicked.emit(pt)

    def keyPressEvent(self, e):
        if e.key() == qt_key_escape():
            self.canceled.emit()
        else:
            super().keyPressEvent(e)


# ------------------------------------------------------------
# Manifest
# ------------------------------------------------------------
class PackageManifest:
    def __init__(self):
        self.path = installed_manifest_path()
        self.data = {"version": 1, "installed": {}}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"version": 1, "installed": {}}
        if "installed" not in self.data:
            self.data["installed"] = {}

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def installed_ids(self):
        return sorted(list((self.data.get("installed") or {}).keys()))

    def installed_meta(self, package_id: str) -> dict:
        return (self.data.get("installed") or {}).get(str(package_id), {})

    def set_installed(self, package_id: str, meta: dict):
        self.data.setdefault("installed", {})
        self.data["installed"][str(package_id)] = meta
        self.save()

    def remove(self, package_id: str):
        self.data.setdefault("installed", {})
        self.data["installed"].pop(str(package_id), None)
        self.save()

    def find_installed_by_theme_norm(self, theme_norm: str) -> dict:
        theme_norm = _norm_theme_folder(theme_norm)
        for _pid, meta in (self.data.get("installed") or {}).items():
            if _norm_theme_folder(meta.get("theme_norm") or meta.get("theme") or "") == theme_norm:
                return meta
        return {}

    def installed_version_for_theme_norm(self, theme_norm: str) -> str:
        meta = self.find_installed_by_theme_norm(theme_norm)
        if not meta:
            return ""
        return normalize_version(meta.get("version") or "")


# ------------------------------------------------------------
# Repo
# ------------------------------------------------------------
class PackageRepository:
    def __init__(self, xml_url: str):
        self.xml_url = xml_url

    def fetch_packages_blocking(self) -> list:
        nam = QgsNetworkAccessManager.instance()
        req = _make_request(self.xml_url, cache_bust=True)
        reply = nam.get(req)

        loop = QEventLoop()
        reply.finished.connect(loop.quit)

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(20000)

        qt_exec(loop)

        if not timer.isActive():
            try:
                reply.abort()
            except Exception:
                pass
            raise RuntimeError("Timeout ved henting av pakkeliste (XML).")

        try:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        except AttributeError:
            try:
                status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            except Exception:
                status = None

        try:
            final_url = reply.url().toString()
        except Exception:
            final_url = self.xml_url

        raw = bytes(reply.readAll())

        if status not in (None, 200):
            try:
                err_name = getattr(reply.error(), "name", str(reply.error()))
            except Exception:
                err_name = "ukjent"

            raise RuntimeError(
                f"Nettverksfeil ved henting av pakkeliste.\n"
                f"URL: {final_url}\n"
                f"HTTP-status: {status}\n"
                f"Qt-feilkode: {err_name}\n"
                f"Feiltekst: {reply.errorString()}"
            )

        if not raw:
            raise RuntimeError(
                f"Pakkelisten ble hentet uten innhold.\n"
                f"URL: {final_url}\n"
                f"HTTP-status: {status}"
            )

        xml_text = raw.decode("utf-8", errors="replace")

        try:
            return self._parse_xml(xml_text)
        except Exception as e:
            preview = xml_text[:500]
            raise RuntimeError(
                f"Kunne ikke tolke pakkelisten som XML.\n"
                f"URL: {final_url}\n"
                f"HTTP-status: {status}\n"
                f"Feil: {e}\n\n"
                f"Start på svar:\n{preview}"
            )

    def _parse_xml(self, xml_text: str) -> list:
        out = []
        root = ET.fromstring(xml_text)

        for p in root.findall(".//package"):
            pid = (p.get("id") or "").strip()
            theme = (p.get("theme") or "").strip()
            version = normalize_version((p.get("version") or "").strip())
            count = (p.get("count") or "").strip()
            bytes_ = (p.get("bytes") or "").strip()

            out.append({
                "id": pid,
                "name": (p.get("name") or "").strip() or pid,
                "theme": theme,
                "theme_norm": _norm_theme_folder(theme),
                "version": version,
                "download_url": (p.get("download_url") or "").strip(),
                "pack_json": (p.get("pack_json") or "").strip(),
                "count": count,
                "bytes": bytes_,
            })

        return [x for x in out if x.get("id") and x.get("download_url") and x.get("theme_norm")]


class PackageUpdateChecker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, repo_url: str, parent=None):
        super().__init__(parent)
        self.repo_url = repo_url
        self.reply = None

    def start(self):
        nam = QgsNetworkAccessManager.instance()
        req = _make_request(self.repo_url, cache_bust=True)
        self.reply = nam.get(req)
        self.reply.finished.connect(self._on_finished)

    def _on_finished(self):
        try:
            if not self.reply:
                self.finished.emit("")
                return

            try:
                status = self.reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            except AttributeError:
                try:
                    status = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
                except Exception:
                    status = None

            if status not in (None, 200):
                self.finished.emit("")
                return

            xml_text = bytes(self.reply.readAll()).decode("utf-8", errors="replace")
            repo = PackageRepository(self.repo_url)
            pkgs = repo._parse_xml(xml_text)

            latest = {}
            for p in pkgs:
                t = p["theme_norm"]
                cur = latest.get(t)
                if not cur or is_newer_version(p.get("version", ""), cur.get("version", "")):
                    latest[t] = p

            man = PackageManifest()
            updates = 0
            new_packs = 0

            for theme_norm, pkg in latest.items():
                inst_v = man.installed_version_for_theme_norm(theme_norm)
                if not inst_v:
                    new_packs += 1
                elif is_newer_version(pkg.get("version", ""), inst_v):
                    updates += 1

            if updates > 0:
                self.finished.emit(f"🔔 {updates} pakke(r) har oppdateringer. Åpne “Ikonpakker” for å oppdatere.")
            elif new_packs > 0:
                self.finished.emit(f"ℹ️ {new_packs} nye pakke(r) er tilgjengelig. Åpne “Ikonpakker” for å installere.")
            else:
                self.finished.emit("")
        except Exception:
            self.finished.emit("")


# ------------------------------------------------------------
# Installer
# ------------------------------------------------------------
_INVALID_WIN = r'<>:"/\\|?*'
_ctrl_re = re.compile(r"[\x00-\x1F\x7F]")

def _sanitize_component(name: str, replacement="_") -> str:
    name = (name or "")
    name = _ctrl_re.sub("", name)
    trans = {ord(ch): replacement for ch in _INVALID_WIN}
    name = name.translate(trans).rstrip(" .")
    if not name:
        name = "_"
    upper = name.upper()
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
    if upper in reserved:
        name = f"_{name}"
    return name

def _sanitize_relpath(zip_name: str) -> str:
    zip_name = (zip_name or "").replace("\\", "/")
    parts = []
    for p in zip_name.split("/"):
        if p in ("", ".", ".."):
            continue
        parts.append(_sanitize_component(p))
    return "/".join(parts) if parts else "_"


class PackageInstaller:
    def __init__(self, manifest: PackageManifest):
        self.manifest = manifest

    def package_dir(self, package_id: str) -> str:
        p = os.path.join(packages_root_dir(), _sanitize_component(package_id))
        os.makedirs(p, exist_ok=True)
        return p.replace("\\", "/")

    def uninstall(self, package_id: str):
        pdir = self.package_dir(package_id)
        try:
            shutil.rmtree(pdir, ignore_errors=True)
        except Exception:
            pass
        self.manifest.remove(package_id)

    def install_from_repo(self, pkg: dict):
        package_id = pkg["id"]
        theme_norm = _norm_theme_folder(pkg.get("theme") or "")
        if not theme_norm:
            raise RuntimeError("Pakke mangler theme.")

        existing = self.manifest.find_installed_by_theme_norm(theme_norm)
        if existing and existing.get("id") and existing.get("id") != package_id:
            try:
                self.uninstall(existing["id"])
            except Exception:
                pass

        pdir = self.package_dir(package_id)

        # Rydd gammel installasjon av samme package_id før reinstall / oppdatering
        try:
            shutil.rmtree(pdir, ignore_errors=True)
        except Exception:
            pass
        os.makedirs(pdir, exist_ok=True)

        zip_path = os.path.join(pdir, "package.zip").replace("\\", "/")

        self._download_file(pkg["download_url"], zip_path, cache_bust=True)
        self._extract_svgs(zip_path, pdir, theme_norm)

        if pkg.get("pack_json"):
            json_path = os.path.join(pdir, "resources", "svg", theme_norm, f"{theme_norm}.json").replace("\\", "/")
            self._download_file(pkg["pack_json"], json_path, cache_bust=True)

        meta = {
            "id": package_id,
            "name": pkg.get("name") or package_id,
            "theme": pkg.get("theme") or theme_norm,
            "theme_norm": theme_norm,
            "version": normalize_version(pkg.get("version") or ""),
            "download_url": pkg.get("download_url"),
            "pack_json": pkg.get("pack_json", ""),
            "installed_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "package_dir": pdir,
        }
        self.manifest.set_installed(package_id, meta)

    def _download_file(self, url: str, out_path: str, cache_bust: bool = True):
        nam = QgsNetworkAccessManager.instance()
        req = _make_request(url, cache_bust=cache_bust)
        reply = nam.get(req)

        loop = QEventLoop()
        reply.finished.connect(loop.quit)

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(60000)

        qt_exec(loop)

        if not timer.isActive():
            try:
                reply.abort()
            except Exception:
                pass
            raise RuntimeError(f"Timeout ved nedlasting: {url}")

        try:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        except AttributeError:
            try:
                status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            except Exception:
                status = None

        data = bytes(reply.readAll())

        if status not in (None, 200):
            try:
                err_name = getattr(reply.error(), "name", str(reply.error()))
            except Exception:
                err_name = "ukjent"

            raise RuntimeError(
                f"Nedlasting feilet.\n"
                f"URL: {url}\n"
                f"HTTP-status: {status}\n"
                f"Qt-feilkode: {err_name}\n"
                f"Feiltekst: {reply.errorString()}"
            )

        if not data:
            raise RuntimeError(f"Nedlasting ga tomt innhold: {url}")

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)

    def _extract_svgs(self, zip_path: str, package_dir: str, theme_norm: str):
        theme_norm = _norm_theme_folder(theme_norm)
        out_root = os.path.join(package_dir, "resources", "svg", theme_norm).replace("\\", "/")
        os.makedirs(out_root, exist_ok=True)

        def strip_known_prefixes(rel: str) -> str:
            rel = (rel or "").replace("\\", "/").lstrip("/")
            prefix1 = f"resources/svg/{theme_norm}/"
            if rel.lower().startswith(prefix1.lower()):
                return rel[len(prefix1):]

            prefix2 = f"{theme_norm}/"
            if rel.lower().startswith(prefix2.lower()):
                return rel[len(prefix2):]

            if rel.lower().startswith("resources/svg/"):
                parts = rel.split("/")
                if len(parts) >= 3:
                    return "/".join(parts[3:]) if len(parts) > 3 else ""
            return rel

        with zipfile.ZipFile(zip_path, "r") as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                name = info.filename or ""
                if not name.lower().endswith(".svg"):
                    continue

                rel_sanitized = _sanitize_relpath(name)
                inner = strip_known_prefixes(rel_sanitized).lstrip("/")
                if not inner:
                    continue

                out_file = os.path.join(out_root, *inner.split("/")).replace("\\", "/")
                os.makedirs(os.path.dirname(out_file), exist_ok=True)

                # Overskriv direkte, ikke lag _2, _3 osv.
                with z.open(info, "r") as src, open(out_file, "wb") as dst:
                    dst.write(src.read())


# ------------------------------------------------------------
# Package manager dialog
# ------------------------------------------------------------
class PackageManagerDialog(QDialog):
    packagesChanged = pyqtSignal()

    def __init__(self, parent, repo_url: str, im):
        super().__init__(parent)
        self.setWindowTitle("Ikonpakker")
        self.resize(900, 460)

        self.im = im
        self.manifest = PackageManifest()
        self.installer = PackageInstaller(self.manifest)
        self.repo = PackageRepository(repo_url)
        self._packages = []

        v = QVBoxLayout(self)

        top1 = QHBoxLayout()
        self.btn_refresh = QPushButton("Oppdater pakkeliste")
        self.btn_install = QPushButton("Installer / oppdater valgt")
        self.btn_uninstall = QPushButton("Avinstaller valgt")
        top1.addWidget(self.btn_refresh)
        top1.addStretch(1)
        top1.addWidget(self.btn_install)
        top1.addWidget(self.btn_uninstall)
        v.addLayout(top1)

        top2 = QHBoxLayout()
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Søk (pakkenavn / theme)…")
        self.chk_only_updates = QCheckBox("Kun oppdateringer")
        top2.addWidget(QLabel("Søk:"))
        top2.addWidget(self.txt_filter, 1)
        top2.addSpacing(10)
        top2.addWidget(self.chk_only_updates)
        v.addLayout(top2)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels([
            "Installert", "Pakke", "Antall ikoner",
            "Pakkestørrelse", "Installert", "Tilgjengelig"
        ])

        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0, qt_header_resize_to_contents())
        hh.setSectionResizeMode(1, qt_header_stretch())
        hh.setSectionResizeMode(2, qt_header_resize_to_contents())
        hh.setSectionResizeMode(3, qt_header_resize_to_contents())
        hh.setSectionResizeMode(4, qt_header_resize_to_contents())
        hh.setSectionResizeMode(5, qt_header_resize_to_contents())

        self.tbl.setSelectionBehavior(qt_select_rows())
        self.tbl.setEditTriggers(qt_no_edit_triggers())
        v.addWidget(self.tbl, 1)

        self.lbl = QLabel("")
        v.addWidget(self.lbl)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_install.clicked.connect(self.install_selected)
        self.btn_uninstall.clicked.connect(self.uninstall_selected)
        self.txt_filter.textChanged.connect(self._render_table)
        self.chk_only_updates.toggled.connect(self._render_table)

        self.refresh()

    def refresh(self):
        try:
            self._packages = self.repo.fetch_packages_blocking()
        except Exception as e:
            QMessageBox.warning(self, "Kunne ikke hente pakkeliste", str(e))
            self._packages = []
        self._render_table()

    def _fmt_v(self, v: str) -> str:
        v = normalize_version(v or "")
        return f"v{v}" if v else "-"

    def _fmt_size(self, s) -> str:
        try:
            b = int(str(s).strip())
        except Exception:
            return "-"
        if b < 0:
            return "-"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        v = float(b)
        while v >= 1024.0 and i < len(units) - 1:
            v /= 1024.0
            i += 1
        if i == 0:
            return f"{int(v)} {units[i]}"
        return f"{v:.1f} {units[i]}"

    def _render_table(self):
        self.tbl.setRowCount(0)

        by_theme = {}
        for pkg in self._packages:
            t = pkg.get("theme_norm") or ""
            if not t:
                continue
            cur = by_theme.get(t)
            if not cur or is_newer_version(pkg.get("version", ""), cur.get("version", "")):
                by_theme[t] = pkg

        q = (self.txt_filter.text() or "").strip().lower()
        only_updates = bool(self.chk_only_updates.isChecked())

        themes = sorted(by_theme.keys())
        installed_count = len(self.manifest.installed_ids())
        updates_count = 0
        shown = 0

        for t in themes:
            pkg = by_theme[t]
            name = (pkg.get("name") or t).strip()
            theme_label = (pkg.get("theme") or t).strip()
            avail_v = (pkg.get("version") or "").strip()

            installed_meta = self.manifest.find_installed_by_theme_norm(t)
            installed_v = (installed_meta.get("version") or "").strip() if installed_meta else ""
            installed_yes = "Ja" if installed_meta else "Nei"

            num = str(pkg.get("count") or "").strip() or "-"
            size_txt = self._fmt_size(pkg.get("bytes"))

            has_update = bool(installed_meta and is_newer_version(avail_v, installed_v))
            if has_update:
                updates_count += 1

            if q:
                hay = f"{name} {theme_label} {avail_v} {installed_v}".lower()
                if q not in hay:
                    continue

            if only_updates and not has_update:
                continue

            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(installed_yes))
            self.tbl.setItem(r, 1, QTableWidgetItem(name))
            self.tbl.setItem(r, 2, QTableWidgetItem(num))
            self.tbl.setItem(r, 3, QTableWidgetItem(size_txt))
            self.tbl.setItem(r, 4, QTableWidgetItem(self._fmt_v(installed_v)))
            self.tbl.setItem(r, 5, QTableWidgetItem(self._fmt_v(avail_v)))
            self.tbl.item(r, 0).setData(qt_user_role(), pkg)
            shown += 1

        self.lbl.setText(
            f"Pakker på server: {len(themes)}  •  Vist: {shown}  •  Installert: {installed_count}  •  Oppdateringer: {updates_count}"
        )

    def _selected_pkg(self):
        row = self.tbl.currentRow()
        if row < 0:
            return None
        it = self.tbl.item(row, 0)
        if not it:
            return None
        return it.data(qt_user_role())

    def install_selected(self):
        pkg = self._selected_pkg()
        if not pkg:
            QMessageBox.information(self, "Velg pakke", "Velg en pakke i listen.")
            return
        try:
            self.installer.install_from_repo(pkg)
        except Exception as e:
            QMessageBox.warning(self, "Installering feilet", str(e))
            return

        self.im.reload_svg_only()
        self.refresh()
        self.packagesChanged.emit()
        QMessageBox.information(self, "Ferdig", "Pakken er installert/oppdatert.")

    def uninstall_selected(self):
        pkg = self._selected_pkg()
        if not pkg:
            QMessageBox.information(self, "Velg pakke", "Velg en pakke i listen.")
            return

        theme_norm = _norm_theme_folder(pkg.get("theme_norm") or "")
        installed_meta = self.manifest.find_installed_by_theme_norm(theme_norm)
        if not installed_meta:
            QMessageBox.information(self, "Ikke installert", "Denne pakken er ikke installert.")
            return

        pid = installed_meta.get("id")
        if QMessageBox.question(
            self,
            "Avinstaller",
            f"Vil du avinstallere '{installed_meta.get('name', theme_norm)}'?"
        ) != qt_msgbox_yes():
            return

        try:
            self.installer.uninstall(pid)
        except Exception as e:
            QMessageBox.warning(self, "Avinstallering feilet", str(e))
            return

        self.im.reload_svg_only()
        self.refresh()
        self.packagesChanged.emit()
        QMessageBox.information(self, "Ferdig", "Pakken er avinstallert.")


# ------------------------------------------------------------
# Icon manager (SVG-only)
# ------------------------------------------------------------
class IconManager:
    def __init__(self):
        self._loaded = False
        self.svg_icons = []
        self._pix_cache = {}

    def ensure_loaded(self):
        if self._loaded:
            return
        self.reload_svg_only()
        self._loaded = True

    def reload_svg_only(self):
        self._pix_cache = {k: v for k, v in self._pix_cache.items() if k and k[0] != "svg"}
        self.svg_icons = []
        self._load_user_installed_packs()

    def _load_user_installed_packs(self):
        man = PackageManifest()
        for pid in man.installed_ids():
            meta = man.installed_meta(pid) or {}
            pdir = (meta.get("package_dir") or os.path.join(packages_root_dir(), pid)).replace("\\", "/")
            theme_norm = meta.get("theme_norm") or _norm_theme_folder(meta.get("theme") or "")
            if not theme_norm:
                continue

            json_abs = os.path.join(pdir, "resources", "svg", theme_norm, f"{theme_norm}.json").replace("\\", "/")
            if os.path.exists(json_abs):
                self._load_svg_pack_abs(
                    json_abs=json_abs,
                    package_root=pdir,
                    theme_norm=theme_norm,
                    pack_id=meta.get("id") or pid,
                    pack_name=meta.get("name") or theme_norm,
                )

    def _load_svg_pack_abs(self, json_abs: str, package_root: str, theme_norm: str, pack_id: str, pack_name: str):
        def _resolve_user_svg_path(symbol_rel: str, theme_norm_local: str) -> str:
            p = norm_rel(symbol_rel)
            if not p:
                return ""
            if p.lower().startswith("resources/"):
                return p
            return f"resources/svg/{theme_norm_local}/{p}"

        def _abs(p_rel: str) -> str:
            return os.path.join(package_root, p_rel).replace("\\", "/")

        try:
            with open(json_abs, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and isinstance(data.get("items"), list):
                data = data["items"]

            if not isinstance(data, list):
                return

            for item in data:
                if not isinstance(item, dict):
                    continue

                name = str(item.get("name") or "(uten navn)")
                description = str(item.get("description") or "").strip()
                category = str(item.get("category") or "").strip()
                default_variant = str(item.get("default_variant") or "positive")
                default_color = str(item.get("default_color") or "")
                variants_raw = item.get("variants")

                if not isinstance(variants_raw, dict) or not variants_raw:
                    symbol_rel = _resolve_user_svg_path(item.get("symbol") or "", theme_norm)
                    if not symbol_rel:
                        continue
                    symbol_abs = _abs(symbol_rel)
                    if not os.path.exists(symbol_abs):
                        QgsMessageLog.logMessage(f"[Iconic] Mangler SVG: {symbol_abs} (name={name})", "Iconic", Qgis.Warning)
                        continue

                    self.svg_icons.append({
                        "name": name,
                        "description": description,
                        "category": category,
                        "variants": None,
                        "default_variant": "",
                        "default_color": "",
                        "symbol_rel": symbol_rel,
                        "symbol_abs": symbol_abs,
                        "package_root": package_root,
                        "theme_norm": theme_norm,
                        "pack_id": pack_id,
                        "pack_name": pack_name,
                    })
                    continue

                variants_norm = {}
                for vname, vval in variants_raw.items():
                    vname = str(vname)
                    if isinstance(vval, str):
                        p = _resolve_user_svg_path(vval, theme_norm)
                        if p:
                            variants_norm[vname] = p
                    elif isinstance(vval, dict):
                        cmap = {}
                        for cname, cpath in vval.items():
                            if isinstance(cpath, str):
                                p = _resolve_user_svg_path(cpath, theme_norm)
                                if p:
                                    cmap[str(cname)] = p
                        if cmap:
                            variants_norm[vname] = cmap

                if not variants_norm:
                    continue

                if default_variant not in variants_norm:
                    default_variant = next(iter(variants_norm.keys()))

                chosen = variants_norm[default_variant]
                symbol_rel = ""
                if isinstance(chosen, str):
                    symbol_rel = chosen
                elif isinstance(chosen, dict):
                    if default_color and default_color in chosen:
                        symbol_rel = chosen[default_color]
                    else:
                        symbol_rel = chosen[next(iter(chosen.keys()))]

                if not symbol_rel:
                    continue

                symbol_abs = _abs(symbol_rel)
                if not os.path.exists(symbol_abs):
                    QgsMessageLog.logMessage(f"[Iconic] Mangler SVG: {symbol_abs} (name={name})", "Iconic", Qgis.Warning)
                    continue

                self.svg_icons.append({
                    "name": name,
                    "description": description,
                    "category": category,
                    "variants": variants_norm,
                    "default_variant": default_variant,
                    "default_color": default_color,
                    "symbol_rel": symbol_rel,
                    "symbol_abs": symbol_abs,
                    "package_root": package_root,
                    "theme_norm": theme_norm,
                    "pack_id": pack_id,
                    "pack_name": pack_name,
                })

        except Exception as e:
            QgsMessageLog.logMessage(f"[Iconic] Feil ved lasting av {json_abs}: {e}", "Iconic", Qgis.Warning)

    def render_svg_pixmap(self, svg_abs: str, px: int) -> QPixmap:
        key = ("svg", svg_abs, px)
        if key in self._pix_cache:
            return self._pix_cache[key]

        s = int(px)
        svg_abs = (svg_abs or "").replace("\\", "/")
        base = QIcon(svg_abs).pixmap(s, s)

        pix = QPixmap(s, s)
        pix.fill(qt_transparent())

        p = QPainter(pix)
        p.setRenderHint(qt_painter_antialiasing(), True)
        p.drawPixmap(0, 0, base)
        p.end()

        self._pix_cache[key] = pix
        return pix


# ------------------------------------------------------------
# Fields (SVG-only)
# ------------------------------------------------------------
REQUIRED_FIELDS_SVG = [
    ("icon_source", QVariant.String),
    ("svg_name", QVariant.String),
    ("svg_path", QVariant.String),
    ("svg_size", QVariant.Double),
    ("svg_variant", QVariant.String),
    ("svg_category", QVariant.String),
    ("svg_pack", QVariant.String),
]

def ensure_layer_fields(layer: QgsVectorLayer, fields):
    pr = layer.dataProvider()
    existing = {f.name(): f for f in layer.fields()}
    to_add = []
    for name, qvariant in fields:
        if name not in existing:
            to_add.append(QgsField(name, qvariant))
    if to_add:
        pr.addAttributes(to_add)
        layer.updateFields()


# ------------------------------------------------------------
# Property keys
# ------------------------------------------------------------
def _prop_size():
    try:
        return QgsSymbolLayer.Property.Size
    except Exception:
        return getattr(QgsSymbolLayer, "PropertySize", None)


# ------------------------------------------------------------
# Renderer
# ------------------------------------------------------------
def _make_symbol_for_svg(svg_abs_path: str) -> QgsMarkerSymbol:
    key_size = _prop_size()
    if key_size is None:
        raise RuntimeError("Fant ikke QgsSymbolLayer-property key for Size.")

    sym = QgsMarkerSymbol()
    sym.deleteSymbolLayer(0)

    svg_layer = QgsSvgMarkerSymbolLayer.create({"name": svg_abs_path})
    svg_layer.setDataDefinedProperty(key_size, QgsProperty.fromField("svg_size"))

    sym.appendSymbolLayer(svg_layer)
    return sym

def apply_renderer_svg_categorized(layer: QgsVectorLayer, rebuild_from_layer: bool = True):
    ensure_layer_fields(layer, REQUIRED_FIELDS_SVG)

    field = "svg_path"
    categories = []

    if rebuild_from_layer:
        idx_path = layer.fields().indexOf("svg_path")
        idx_name = layer.fields().indexOf("svg_name")
        idx_src = layer.fields().indexOf("icon_source")

        seen = {}
        for f in layer.getFeatures():
            try:
                src = str(f[idx_src] or "").strip()
                if src != "svg":
                    continue
                p = str(f[idx_path] or "").strip()
                if not p:
                    continue
                nm = str(f[idx_name] or "").strip() or os.path.basename(p)
                if p not in seen:
                    seen[p] = nm
            except Exception:
                continue

        for p, nm in sorted(seen.items(), key=lambda kv: (kv[1].lower(), kv[0].lower())):
            sym = _make_symbol_for_svg(p)
            categories.append(QgsRendererCategory(p, sym, nm))

    renderer = QgsCategorizedSymbolRenderer(field, categories)

    try:
        renderer.setDefaultSymbol(QgsMarkerSymbol.createSimple({"name": "circle"}))
        renderer.setDefaultSymbolLabel("Ukjent / ikke matchet")
    except Exception:
        pass

    layer.setRenderer(renderer)
    layer.triggerRepaint()

def ensure_svg_category_in_renderer(layer: QgsVectorLayer, svg_path: str, label: str):
    svg_path = (svg_path or "").strip()
    if not svg_path:
        return

    r = layer.renderer()
    if not isinstance(r, QgsCategorizedSymbolRenderer):
        apply_renderer_svg_categorized(layer, rebuild_from_layer=True)
        r = layer.renderer()

    if not isinstance(r, QgsCategorizedSymbolRenderer):
        return

    if (r.classAttribute() or "") != "svg_path":
        apply_renderer_svg_categorized(layer, rebuild_from_layer=True)
        return

    for c in r.categories():
        if str(c.value()) == svg_path:
            return

    sym = _make_symbol_for_svg(svg_path)
    cat = QgsRendererCategory(svg_path, sym, label or os.path.basename(svg_path))
    r.addCategory(cat)

    layer.triggerRepaint()
    try:
        layer.emitStyleChanged()
    except Exception:
        pass


# ------------------------------------------------------------
# Populate fields
# ------------------------------------------------------------
def populate_svg_fields_for_existing_features(layer: QgsVectorLayer, payload: dict,
                                             only_if_empty: bool = True,
                                             commit: bool = False,
                                             overwrite_existing: bool = False) -> int:
    ensure_layer_fields(layer, REQUIRED_FIELDS_SVG)

    name = payload["name"]
    svg_abs = (payload.get("svg_abs") or "").replace("\\", "/")
    size = float(payload["size_mm"])
    variant = str(payload.get("svg_variant") or "").strip()
    category = str(payload.get("category") or "").strip()
    pack = str(payload.get("pack") or "").strip()

    if not layer.isEditable():
        if not layer.startEditing():
            raise RuntimeError("Kunne ikke starte redigering på laget (skrivebeskyttet?)")

    flds = layer.fields()
    idx_src = flds.indexOf("icon_source")
    idx_name = flds.indexOf("svg_name")
    idx_path = flds.indexOf("svg_path")
    idx_size = flds.indexOf("svg_size")
    idx_var = flds.indexOf("svg_variant")
    idx_cat = flds.indexOf("svg_category")
    idx_pack = flds.indexOf("svg_pack")

    layer.beginEditCommand("Iconic: style eksisterende")

    changed = 0
    try:
        for f in layer.getFeatures():
            cur_src = str(f[idx_src] or "").strip()
            cur_path = str(f[idx_path] or "").strip()

            if not overwrite_existing and only_if_empty:
                if cur_src == "svg" and cur_path:
                    continue

            fid = f.id()
            layer.changeAttributeValue(fid, idx_src, "svg")
            layer.changeAttributeValue(fid, idx_name, name)
            layer.changeAttributeValue(fid, idx_path, svg_abs)
            layer.changeAttributeValue(fid, idx_size, size)
            layer.changeAttributeValue(fid, idx_var, variant)
            layer.changeAttributeValue(fid, idx_cat, category)
            layer.changeAttributeValue(fid, idx_pack, pack)
            changed += 1

        layer.endEditCommand()
    except Exception:
        layer.destroyEditCommand()
        raise

    ensure_svg_category_in_renderer(layer, svg_abs, name)
    layer.triggerRepaint()

    if commit:
        layer.commitChanges()

    return changed


# ------------------------------------------------------------
# Add feature
# ------------------------------------------------------------
def add_point_feature_svg(layer: QgsVectorLayer, map_point: QgsPointXY, payload: dict, map_crs):
    ensure_layer_fields(layer, REQUIRED_FIELDS_SVG)

    if not layer.isEditable():
        if not layer.startEditing():
            raise RuntimeError("Kunne ikke starte redigering (skrivebeskyttet / låst?)")

    layer_crs = layer.crs()
    if layer_crs != map_crs:
        tr = QgsCoordinateTransform(map_crs, layer_crs, QgsProject.instance())
        pt_layer = tr.transform(map_point)
    else:
        pt_layer = map_point

    svg_abs = (payload.get("svg_abs") or "").replace("\\", "/")
    if not svg_abs or not os.path.exists(svg_abs):
        raise RuntimeError(f"SVG finnes ikke: {svg_abs}")

    variant = str(payload.get("svg_variant") or "").strip()
    category = str(payload.get("category") or "").strip()
    pack = str(payload.get("pack") or "").strip()

    feat = QgsFeature(layer.fields())
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pt_layer)))

    feat["icon_source"] = "svg"
    feat["svg_name"] = payload["name"]
    feat["svg_path"] = svg_abs
    feat["svg_size"] = float(payload["size_mm"])
    feat["svg_variant"] = variant
    feat["svg_category"] = category
    feat["svg_pack"] = pack

    if not layer.addFeature(feat):
        raise RuntimeError("Kunne ikke legge til feature i laget.")

    ensure_svg_category_in_renderer(layer, svg_abs, payload["name"])
    layer.updateExtents()
    layer.triggerRepaint()
    return feat


# ------------------------------------------------------------
# Dock UI
# ------------------------------------------------------------
class IconicDock(QWidget):
    startPlacingRequested = pyqtSignal(dict)
    stopPlacingRequested = pyqtSignal()
    applyStyleRequested = pyqtSignal(dict)
    refreshLayersRequested = pyqtSignal()
    updateCheckRequested = pyqtSignal()

    def __init__(self, iface, im: IconManager):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.im = im
        self._selected_item = None
        self._reflow_pending = False

        self._build_ui()
        self.populate_layers()
        self.refresh_items()

        self.lst_svg.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.lst_svg.viewport() and event.type() == qt_resize_event_type():
            self._schedule_reflow()
        return super().eventFilter(obj, event)

    def set_update_banner(self, text: str):
        text = (text or "").strip()
        if not text:
            self.lbl_updates.setVisible(False)
            self.lbl_updates.setText("")
            return
        self.lbl_updates.setText(text)
        self.lbl_updates.setVisible(True)

    def _setup_icon_list(self, lst: QListWidget):
        lst.setIconSize(QSize(28, 28))
        lst.setUniformItemSizes(False)
        lst.setWordWrap(True)
        lst.setSelectionMode(qt_single_selection())
        lst.setHorizontalScrollBarPolicy(qt_scrollbar_always_off())

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.cmb_layer = QComboBox()
        self.btn_refresh_layers = QPushButton("Oppdater lagliste")
        form.addRow("Punktlag:", self.cmb_layer)
        form.addRow("", self.btn_refresh_layers)
        layout.addLayout(form)

        self.lbl_updates = QLabel("")
        self.lbl_updates.setWordWrap(True)
        self.lbl_updates.setVisible(False)
        self.lbl_updates.setStyleSheet(
            "QLabel { padding: 6px; color: #000000;background-color: #E7F5FE; border: 1px solid #B9CFE4; border-radius: 4px; }"
        )
        layout.addWidget(self.lbl_updates)

        row_pack = QHBoxLayout()
        self.cmb_pack = QComboBox()
        self.cmb_pack.addItem("Alle pakker", "")
        self.btn_packages = QPushButton("Ikonpakker")
        row_pack.addWidget(QLabel("Ikonpakke:"))
        row_pack.addWidget(self.cmb_pack, 1)
        row_pack.addWidget(self.btn_packages)
        layout.addLayout(row_pack)

        row_cat = QHBoxLayout()
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("Alle kategorier", "")
        row_cat.addWidget(QLabel("Kategori:"))
        row_cat.addWidget(self.cmb_category, 1)
        layout.addLayout(row_cat)

        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Søk (navn / beskrivelse)…")
        search_row.addWidget(QLabel("Søk:"))
        search_row.addWidget(self.txt_search, 1)
        layout.addLayout(search_row)

        self.lst_svg = QListWidget()
        self._setup_icon_list(self.lst_svg)
        layout.addWidget(self.lst_svg, 1)

        self.grp_variant = QGroupBox("Valgt ikon – variant")
        v_l = QVBoxLayout(self.grp_variant)
        v_form = QFormLayout()
        self.cmb_variant = QComboBox()
        self.lbl_variant_na = QLabel("Ikke tilgjengelig")
        v_form.addRow("Variant:", self.cmb_variant)
        v_form.addRow("", self.lbl_variant_na)
        v_l.addLayout(v_form)
        layout.addWidget(self.grp_variant)
        self.grp_variant.setVisible(False)

        size_form = QFormLayout()
        self.spn_svg_size = QDoubleSpinBox()
        self.spn_svg_size.setRange(0.5, 80.0)
        self.spn_svg_size.setDecimals(1)
        self.spn_svg_size.setValue(6.0)
        self.spn_svg_size.setSuffix(" mm")
        size_form.addRow("Størrelse:", self.spn_svg_size)
        layout.addLayout(size_form)

        grp_mode = QGroupBox("Arbeidsmåte")
        mode_l = QVBoxLayout(grp_mode)
        self.rb_place = QRadioButton("Plassér nye punkter ved klikk i kartet")
        self.rb_style = QRadioButton("Style eksisterende lag")
        self.rb_place.setChecked(True)
        mode_l.addWidget(self.rb_place)
        mode_l.addWidget(self.rb_style)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_place)
        self.mode_group.addButton(self.rb_style)
        layout.addWidget(grp_mode)

        grp_style = QGroupBox("Stil-innstillinger")
        style_l = QVBoxLayout(grp_style)
        self.chk_data_driven = QCheckBox("Data-driven (per feature) via felt")
        self.chk_data_driven.setChecked(True)
        style_l.addWidget(self.chk_data_driven)
        self.chk_overwrite_existing = QCheckBox("Overskriv eksisterende ikoner i laget")
        self.chk_overwrite_existing.setChecked(False)
        style_l.addWidget(self.chk_overwrite_existing)
        layout.addWidget(grp_style)

        grp_place = QGroupBox("Plassering")
        place_l = QVBoxLayout(grp_place)
        self.chk_open_form = QCheckBox("Åpne attributtskjema etter plassering")
        self.chk_open_form.setChecked(True)
        place_l.addWidget(self.chk_open_form)
        layout.addWidget(grp_place)

        bottom = QHBoxLayout()
        self.lbl_selected = QLabel("Valgt: (ingen)")
        self.lbl_selected.setTextInteractionFlags(qt_text_selectable_by_mouse())

        self.btn_primary = QPushButton("Plasser i kartet")
        self.btn_stop = QPushButton("Stopp")
        self.btn_stop.setEnabled(False)

        bottom.addWidget(self.lbl_selected, 1)
        bottom.addWidget(self.btn_primary)
        bottom.addWidget(self.btn_stop)
        layout.addLayout(bottom)

        self.btn_refresh_layers.clicked.connect(self.refreshLayersRequested.emit)
        self.btn_primary.clicked.connect(self.on_primary_action)
        self.btn_stop.clicked.connect(self.on_stop)

        self.btn_packages.clicked.connect(self.open_package_manager)
        self.cmb_pack.currentIndexChanged.connect(lambda: (self._maybe_auto_stop(), self._clear_selection_and_label(), self.refresh_items()))
        self.cmb_category.currentIndexChanged.connect(lambda: (self._maybe_auto_stop(), self._clear_selection_and_label(), self.refresh_items()))
        self.txt_search.textChanged.connect(lambda: (self._maybe_auto_stop(), self._clear_selection_and_label(), self.refresh_items()))
        self.spn_svg_size.valueChanged.connect(lambda: self._maybe_auto_stop())

        self.lst_svg.currentItemChanged.connect(self.on_item_selected)
        self.cmb_variant.currentIndexChanged.connect(lambda: (self._maybe_auto_stop(), self._update_selected_label()))

    def _maybe_auto_stop(self):
        if self.btn_stop.isEnabled():
            self.stopPlacingRequested.emit()
            self.placing_stopped_by_plugin()

    def _clear_selection_and_label(self):
        self._selected_item = None
        self.lbl_selected.setText("Valgt: (ingen)")
        self._set_variant_controls(False, [])

    def open_package_manager(self):
        dlg = PackageManagerDialog(self.iface.mainWindow(), REPO_XML_URL, self.im)
        try:
            dlg.packagesChanged.connect(self.updateCheckRequested.emit)
        except Exception:
            pass

        qt_exec(dlg)

        self._maybe_auto_stop()
        self._clear_selection_and_label()
        self.refresh_items()

    def populate_layers(self):
        self.cmb_layer.clear()
        self._layer_map = []

        layers = []
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer) and lyr.isValid():
                if QgsWkbTypes.geometryType(lyr.wkbType()) == QgsWkbTypes.PointGeometry:
                    layers.append(lyr)
        layers.sort(key=lambda l: l.name().lower())

        for lyr in layers:
            self.cmb_layer.addItem(lyr.name())
            self._layer_map.append(lyr)

    def current_layer(self):
        idx = self.cmb_layer.currentIndex()
        if idx < 0 or idx >= len(self._layer_map):
            return None
        return self._layer_map[idx]

    def _rebuild_pack_dropdown(self):
        cur = str(self.cmb_pack.currentData(qt_user_role()) or "")

        packs = {}
        for ic in (self.im.svg_icons or []):
            t = str(ic.get("theme_norm") or "").strip()
            if not t:
                continue
            packs[t] = str(ic.get("pack_name") or t)

        self.cmb_pack.blockSignals(True)
        self.cmb_pack.clear()
        self.cmb_pack.addItem("Alle pakker", "")
        for t in sorted(packs.keys()):
            self.cmb_pack.addItem(packs[t], t)
        idx = self.cmb_pack.findData(cur, qt_user_role())
        self.cmb_pack.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_pack.blockSignals(False)

    def _rebuild_category_dropdown(self, visible_icons: list):
        cur = str(self.cmb_category.currentData(qt_user_role()) or "")
        cats = set()
        for ic in visible_icons:
            c = str(ic.get("category") or "").strip()
            if c:
                cats.add(c)

        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("Alle kategorier", "")
        for c in sorted(cats, key=lambda x: x.lower()):
            self.cmb_category.addItem(c, c)
        idx = self.cmb_category.findData(cur, qt_user_role())
        self.cmb_category.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_category.blockSignals(False)

    def refresh_items(self):
        self.im.ensure_loaded()
        self._rebuild_pack_dropdown()

        q = (self.txt_search.text() or "").strip().lower()
        pack_filter = str(self.cmb_pack.currentData(qt_user_role()) or "").strip()
        cat_filter = str(self.cmb_category.currentData(qt_user_role()) or "").strip()

        pre = []
        for d in (self.im.svg_icons or []):
            if pack_filter and str(d.get("theme_norm") or "").strip() != pack_filter:
                continue
            if q:
                hay = f"{d.get('name','')} {d.get('description','')}".lower()
                if q not in hay:
                    continue
            pre.append(d)

        self._rebuild_category_dropdown(pre)

        icons = []
        for d in pre:
            if cat_filter and str(d.get("category") or "").strip() != cat_filter:
                continue
            icons.append(d)

        self.lst_svg.blockSignals(True)
        self.lst_svg.clear()

        px = 28
        for d in icons:
            pix = self.im.render_svg_pixmap(d["symbol_abs"], px)
            self._add_svg_list_row(d, pix)

        self.lst_svg.blockSignals(False)

        if self.lst_svg.count() > 0 and self.lst_svg.currentRow() < 0:
            self.lst_svg.setCurrentRow(0)

        self._schedule_reflow()

    def _schedule_reflow(self):
        if self._reflow_pending:
            return
        self._reflow_pending = True
        QTimer.singleShot(0, self._reflow_list)

    def _reflow_list(self):
        self._reflow_pending = False
        vw = self.lst_svg.viewport().width()
        if vw <= 0:
            return

        icon_w = self.lst_svg.iconSize().width()
        margins_lr = 12
        spacing = 10
        text_w = max(80, vw - (icon_w + margins_lr + spacing + 8))

        for i in range(self.lst_svg.count()):
            it = self.lst_svg.item(i)
            w = self.lst_svg.itemWidget(it)
            if not w:
                continue

            name_lbl = w.property("name_lbl")
            desc_lbl = w.property("desc_lbl")

            try:
                if isinstance(name_lbl, QLabel):
                    name_lbl.setFixedWidth(text_w)
                if isinstance(desc_lbl, QLabel):
                    desc_lbl.setFixedWidth(text_w)
            except Exception:
                pass

            w.setFixedWidth(vw)
            w.adjustSize()
            it.setSizeHint(QSize(vw, w.sizeHint().height()))

    def _add_svg_list_row(self, d: dict, pix: QPixmap):
        name = str(d.get("name") or "")
        desc = str(d.get("description") or "").strip()

        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(6, 4, 6, 4)
        row_l.setSpacing(10)

        lbl_icon = QLabel()
        lbl_icon.setPixmap(pix)
        lbl_icon.setFixedSize(self.lst_svg.iconSize())
        lbl_icon.setAlignment(qt_align_top() | qt_align_hcenter())
        row_l.addWidget(lbl_icon, 0, qt_align_top())

        txt = QWidget()
        txt_l = QVBoxLayout(txt)
        txt_l.setContentsMargins(0, 0, 0, 0)
        txt_l.setSpacing(0)
        txt.setSizePolicy(qt_sizepolicy_expanding(), qt_sizepolicy_minimum())

        lbl_name = QLabel(name)
        lbl_name.setTextFormat(qt_plain_text())
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("font-weight:600; margin:0; padding:0;")
        lbl_name.setContentsMargins(0, 0, 0, 0)
        lbl_name.setSizePolicy(qt_sizepolicy_expanding(), qt_sizepolicy_minimum())
        txt_l.addWidget(lbl_name)

        lbl_desc = None
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setTextFormat(qt_plain_text())
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color:#666; margin:0; padding:0;")
            lbl_desc.setContentsMargins(0, 0, 0, 0)
            lbl_desc.setSizePolicy(qt_sizepolicy_expanding(), qt_sizepolicy_minimum())
            txt_l.addWidget(lbl_desc)

        row_l.addWidget(txt, 1, qt_align_top())
        row_l.setAlignment(qt_align_top())

        row.setProperty("name_lbl", lbl_name)
        row.setProperty("desc_lbl", lbl_desc)

        it = QListWidgetItem()
        it.setData(qt_user_role(), {"source": "svg", "icon": d})
        self.lst_svg.addItem(it)
        self.lst_svg.setItemWidget(it, row)

    def _variant_keys_for_icon(self, svg_icon: dict) -> list:
        variants = svg_icon.get("variants")
        if not isinstance(variants, dict) or not variants:
            return []
        return sorted([str(k) for k in variants.keys()], key=lambda x: x.lower())

    def _resolve_svg_rel(self, svg_icon: dict, variant: str) -> str:
        variants = svg_icon.get("variants")
        if not isinstance(variants, dict) or not variants:
            return svg_icon.get("symbol_rel") or ""

        v = variants.get(variant)
        if isinstance(v, str):
            return v
        if isinstance(v, dict) and v:
            return v[next(iter(v.keys()))]
        return svg_icon.get("symbol_rel") or ""

    def _resolve_svg_abs(self, svg_icon: dict, svg_rel: str) -> str:
        svg_rel = norm_rel(svg_rel)
        return os.path.join(svg_icon["package_root"], svg_rel).replace("\\", "/")

    def _set_variant_controls(self, visible: bool, keys: list, current: str = ""):
        self.grp_variant.setVisible(bool(visible))
        if not visible:
            self.cmb_variant.blockSignals(True)
            self.cmb_variant.clear()
            self.cmb_variant.blockSignals(False)
            return

        if not keys:
            self.cmb_variant.setEnabled(False)
            self.lbl_variant_na.setVisible(True)
            self.lbl_variant_na.setText("Ikke tilgjengelig")
            self.cmb_variant.setVisible(False)
            return

        self.lbl_variant_na.setVisible(False)
        self.cmb_variant.setVisible(True)
        self.cmb_variant.setEnabled(True)
        self.cmb_variant.blockSignals(True)
        self.cmb_variant.clear()
        self.cmb_variant.addItems(keys)
        if current and current in keys:
            self.cmb_variant.setCurrentText(current)
        else:
            self.cmb_variant.setCurrentIndex(0)
        self.cmb_variant.blockSignals(False)

    def _update_selected_label(self):
        if not self._selected_item:
            self.lbl_selected.setText("Valgt: (ingen)")
            return
        ic = self._selected_item["icon"]
        parts = [f"Valgt: {ic.get('name','')} (SVG)"]

        if isinstance(ic.get("variants"), dict) and ic.get("variants"):
            v = str(self.cmb_variant.currentText() or "").strip()
            if v:
                parts.append(f"variant={v}")

        self.lbl_selected.setText(" — ".join(parts))

    def on_item_selected(self, item, _prev):
        if item and self.btn_stop.isEnabled():
            self._maybe_auto_stop()

        if not item:
            self._clear_selection_and_label()
            return

        d = item.data(qt_user_role())
        self._selected_item = d
        ic = d["icon"]

        vkeys = self._variant_keys_for_icon(ic)
        if vkeys:
            default_variant = str(ic.get("default_variant") or vkeys[0])
            self._set_variant_controls(True, vkeys, default_variant)
        else:
            self._set_variant_controls(False, [], "")

        self._update_selected_label()

    def current_payload(self):
        lyr = self.current_layer()
        if not lyr:
            return None, "Velg et punktlag først."
        if not self._selected_item:
            return None, "Velg et ikon først."

        ic = self._selected_item["icon"]

        variant = ""
        if isinstance(ic.get("variants"), dict) and ic.get("variants"):
            variant = str(self.cmb_variant.currentText() or "").strip()
            if not variant:
                variant = str(ic.get("default_variant") or "positive")

        svg_rel = self._resolve_svg_rel(ic, variant)
        svg_abs = self._resolve_svg_abs(ic, svg_rel)

        payload = {
            "source": "svg",
            "layer_id": lyr.id(),
            "name": ic.get("name") or "",
            "category": str(ic.get("category") or "").strip(),
            "pack": str(ic.get("theme_norm") or "").strip(),
            "svg_rel": svg_rel,
            "svg_abs": svg_abs,
            "svg_variant": variant,
            "size_mm": float(self.spn_svg_size.value()),
            "data_driven": bool(self.chk_data_driven.isChecked()),
            "open_form": bool(self.chk_open_form.isChecked()),
            "overwrite_existing": bool(self.chk_overwrite_existing.isChecked()),
        }
        return payload, ""

    def on_primary_action(self):
        payload, err = self.current_payload()
        if not payload:
            QMessageBox.warning(self, "Mangler valg", err)
            return

        if self.rb_place.isChecked():
            self.btn_primary.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.startPlacingRequested.emit(payload)
        else:
            self.applyStyleRequested.emit(payload)

    def on_stop(self):
        self.btn_primary.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.stopPlacingRequested.emit()

    def placing_stopped_by_plugin(self):
        self.btn_primary.setEnabled(True)
        self.btn_stop.setEnabled(False)


# ------------------------------------------------------------
# Plugin main
# ------------------------------------------------------------
class IconicPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.toolbar = None
        self._toolbar_created = False

        self.im = IconManager()

        self.dock = None
        self.dock_widget = None

        self._map_tool = None
        self._prev_map_tool = None
        self._placing_payload = None

        self._update_banner_text = ""
        self._update_checker = None

    def _on_update_check_finished(self, text: str):
        self._update_banner_text = text or ""
        if self.dock:
            self.dock.set_update_banner(self._update_banner_text)

    def _run_update_check(self):
        self._update_checker = PackageUpdateChecker(REPO_XML_URL, self.iface.mainWindow())
        self._update_checker.finished.connect(self._on_update_check_finished)
        self._update_checker.start()

    def initGui(self):
        icon_path = res_path("icon_iconic.svg")
        icon = QIcon(QPixmap(icon_path))

        self.action = QAction(icon, "Iconic", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.toggled.connect(self._toggle_dock)

        self.iface.addPluginToMenu(PLUGIN_MENU, self.action)

        self.toolbar = self.iface.mainWindow().findChild(QToolBar, PLUGIN_TOOLBAR)
        if self.toolbar is None:
            self.toolbar = QToolBar(PLUGIN_TOOLBAR, self.iface.mainWindow())
            self.toolbar.setObjectName(PLUGIN_TOOLBAR)
            self.iface.mainWindow().addToolBar(self.toolbar)
            self._toolbar_created = True

        # Rydd gammel action med samme tekst hvis den henger igjen
        try:
            for act in list(self.toolbar.actions()):
                if act.text() == "Iconic":
                    self.toolbar.removeAction(act)
                    try:
                        act.deleteLater()
                    except Exception:
                        pass
        except Exception:
            pass

        self.toolbar.addAction(self.action)
        self._run_update_check()

    def unload(self):
        self._stop_placing_tool()

        try:
            dock_widget = self.dock_widget
        except Exception:
            dock_widget = None

        if dock_widget is not None and not sip.isdeleted(dock_widget):
            try:
                dock_widget.visibilityChanged.disconnect(self._dock_visibility_changed)
            except Exception:
                pass
            try:
                self.iface.removeDockWidget(dock_widget)
            except Exception:
                pass
            try:
                dock_widget.setWidget(None)
            except Exception:
                pass
            try:
                dock_widget.deleteLater()
            except Exception:
                pass

        self.dock_widget = None
        self.dock = None

        try:
            action = self.action
        except Exception:
            action = None

        try:
            toolbar = self.toolbar
        except Exception:
            toolbar = None

        if action is not None:
            try:
                if not sip.isdeleted(action):
                    try:
                        action.toggled.disconnect(self._toggle_dock)
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                self.iface.removePluginMenu(PLUGIN_MENU, action)
            except Exception:
                pass

            try:
                if toolbar is not None and not sip.isdeleted(toolbar) and not sip.isdeleted(action):
                    toolbar.removeAction(action)
            except Exception:
                pass

            try:
                if not sip.isdeleted(action):
                    action.deleteLater()
            except Exception:
                pass

        if toolbar is not None:
            try:
                toolbar_deleted = sip.isdeleted(toolbar)
            except Exception:
                toolbar_deleted = True

            if not toolbar_deleted:
                try:
                    is_empty = len(toolbar.actions()) == 0
                except Exception:
                    is_empty = True

                if self._toolbar_created or is_empty:
                    try:
                        self.iface.mainWindow().removeToolBar(toolbar)
                    except Exception:
                        pass
                    try:
                        toolbar.deleteLater()
                    except Exception:
                        pass

        self.action = None
        self.toolbar = None

    def _toggle_dock(self, checked: bool):
        if checked:
            self._show_dock()
        else:
            self._hide_dock()

    def _show_dock(self):
        try:
            self.im.ensure_loaded()
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Iconic – kunne ikke laste SVG", str(e))
            self.action.blockSignals(True)
            self.action.setChecked(False)
            self.action.blockSignals(False)
            return

        if not self.dock_widget:
            self.dock_widget = QDockWidget(DOCK_TITLE, self.iface.mainWindow())
            self.dock_widget.setObjectName("IconicDockWidget")
            self.dock_widget.setAllowedAreas(qt_left_dock_area() | qt_right_dock_area())

            self.dock = IconicDock(self.iface, self.im)
            self.dock.set_update_banner(self._update_banner_text)

            self.dock.startPlacingRequested.connect(self._start_placing_tool)
            self.dock.stopPlacingRequested.connect(self._stop_placing_tool)
            self.dock.applyStyleRequested.connect(self._apply_style)
            self.dock.refreshLayersRequested.connect(self._refresh_layers)
            self.dock.updateCheckRequested.connect(self._run_update_check)

            self.dock_widget.setWidget(self.dock)
            self.dock_widget.visibilityChanged.connect(self._dock_visibility_changed)
            self.iface.addDockWidget(qt_right_dock_area(), self.dock_widget)

        self._refresh_layers()
        self.dock_widget.show()
        self.dock_widget.raise_()

    def _hide_dock(self):
        if self.dock_widget:
            self.dock_widget.hide()
        self._stop_placing_tool()

    def _dock_visibility_changed(self, visible: bool):
        if self.action:
            self.action.blockSignals(True)
            self.action.setChecked(visible)
            self.action.blockSignals(False)
        if not visible:
            self._stop_placing_tool()

    def _refresh_layers(self):
        if self.dock:
            self.dock.populate_layers()

    def _apply_style(self, payload: dict):
        layer = QgsProject.instance().mapLayer(payload["layer_id"])
        if not layer or not layer.isValid():
            QMessageBox.warning(self.iface.mainWindow(), "Ugyldig lag", "Fant ikke valgt lag.")
            return

        try:
            if payload.get("data_driven", True):
                apply_renderer_svg_categorized(layer, rebuild_from_layer=True)

                overwrite = bool(payload.get("overwrite_existing", False))

                filled = populate_svg_fields_for_existing_features(
                    layer,
                    payload,
                    only_if_empty=not overwrite,
                    commit=False,
                    overwrite_existing=overwrite
                )

                self.iface.messageBar().pushMessage(
                    "Iconic",
                    f"Initierte {filled} SVG-features. Renderer: kategorier per svg_path.",
                    level=Qgis.Success,
                    duration=5
                )
        except Exception as e:
            QMessageBox.warning(self.iface.mainWindow(), "Kunne ikke sette stil", str(e))

    def _start_placing_tool(self, payload: dict):
        layer = QgsProject.instance().mapLayer(payload["layer_id"])
        if not layer or not layer.isValid():
            QMessageBox.warning(self.iface.mainWindow(), "Ugyldig lag", "Fant ikke valgt lag.")
            if self.dock:
                self.dock.placing_stopped_by_plugin()
            return

        try:
            apply_renderer_svg_categorized(layer, rebuild_from_layer=True)
        except Exception:
            pass

        self._placing_payload = payload
        canvas = self.iface.mapCanvas()

        self._prev_map_tool = canvas.mapTool()
        self._map_tool = ClickPointTool(canvas)
        self._map_tool.clicked.connect(self._on_canvas_clicked)
        self._map_tool.canceled.connect(self._stop_placing_tool)
        canvas.setMapTool(self._map_tool)

        self.iface.messageBar().pushMessage(
            "Iconic",
            "Klikk i kartet for å plassere. Høyreklikk eller ESC for å stoppe.",
            level=Qgis.Info,
            duration=5,
        )

    def _stop_placing_tool(self):
        canvas = self.iface.mapCanvas()
        if self._map_tool and canvas.mapTool() == self._map_tool:
            if self._prev_map_tool:
                canvas.setMapTool(self._prev_map_tool)
            else:
                canvas.unsetMapTool(self._map_tool)

        self._map_tool = None
        self._prev_map_tool = None
        self._placing_payload = None

        if self.dock:
            self.dock.placing_stopped_by_plugin()

    def _on_canvas_clicked(self, map_point: QgsPointXY):
        payload = self._placing_payload
        if not payload:
            return

        layer = QgsProject.instance().mapLayer(payload["layer_id"])
        if not layer or not layer.isValid():
            QMessageBox.warning(self.iface.mainWindow(), "Ugyldig lag", "Laget finnes ikke lenger.")
            self._stop_placing_tool()
            return

        try:
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        except Exception:
            pass

        try:
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            feat = add_point_feature_svg(layer, map_point, payload, map_crs)

            if payload.get("open_form", True):
                self.iface.openFeatureForm(layer, feat)

        except Exception as e:
            QMessageBox.warning(self.iface.mainWindow(), "Kunne ikke plassere", str(e))