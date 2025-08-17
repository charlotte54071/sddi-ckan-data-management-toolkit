#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CKAN Resource-First File Monitor
--------------------------------
- 仅通过资源名定位 CKAN 资源并做时间戳比较（资源级 last_modified/created）
- 首选 resource_search(POST)；若接口 500 或未命中，兜底 package_search+fq=res_name:"<文件名>"
- 自动将 CKAN UTC 时间转为 Europe/Berlin，比对本地文件创建时间（Berlin 时区）
- 结果按类别/扩展名分组展示
"""

import os
import re
import math
import json
import argparse
import configparser
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pytz
import requests


# ============== 基本配置 ==============
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")

cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH)

# 监控目录（可在 config.ini 里 [Monitoring] monitor_dir=... 设置）
MONITOR_DIR = cfg.get("Monitoring", "monitor_dir", fallback=r"D:\ckan-docker-CKANofficial\sddi-import-export-excel-tool\TEST")

ALLOWED_EXTENSIONS = tuple(cfg.get("Monitoring", "allowed_extensions", fallback="*").lower().split(","))
EXCLUDE_DIRS = tuple(cfg.get("Monitoring", "exclude_dirs", fallback="__pycache__,schema_templates,templates").split(","))
EXCLUDED_EXTENSIONS = tuple(
    cfg.get("Monitoring", "excluded_extensions", fallback=".tmp,.log,.cache,.pyc,.pyo,.bak,.swp,.DS_Store").lower().split(",")
)

TRACKING_FILE = "file_tracking.json"
BERLIN_TZ = pytz.timezone("Europe/Berlin")
UTC_TZ = pytz.UTC


# ============== 工具函数 ==============
def load_config(file: str = "config.ini") -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    c = configparser.ConfigParser()
    c.read(file)
    api_key = c.get("DEFAULT", "api_key", fallback=None)
    instance_url = c.get("DEFAULT", "instance_url", fallback=None)
    path = c.get("DEFAULT", "excel_file_path", fallback=None)
    schema_config = c.get("DEFAULT", "schema_config", fallback=None)
    return api_key, instance_url, path, schema_config


def convert_utc_to_berlin(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = UTC_TZ.localize(dt)
    return dt.astimezone(BERLIN_TZ)


def parse_ckan_timestamp(ts: str, debug: bool = False) -> Optional[datetime]:
    """将 CKAN 的 UTC 时间字符串（可能带 Z）转换为 Europe/Berlin 的 aware datetime。"""
    if not ts or ts == "N/A":
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return convert_utc_to_berlin(dt)
    except Exception as e:
        if debug:
            print(f"         ❌ timestamp parse fail: {e}")
        return None


def format_size(n: int) -> str:
    if n == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(n, 1024)))
    return f"{round(n / (1024 ** i), 2)} {units[i]}"


# ============== HTTP 封装（带 Authorization；verify=False 兼容自签证书） ==============
def _ckan_http_get(api_url: str, api_key: str, action: str, params: dict, debug: bool):
    endpoint = urljoin(api_url.rstrip("/") + "/", f"api/3/action/{action}")
    headers = {"Authorization": api_key} if api_key else {}
    try:
        r = requests.get(endpoint, headers=headers, params=params, timeout=15, verify=False)
        if debug:
            print(f"      HTTP {r.status_code} GET {endpoint} params={params}")
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict) or "success" not in data:
            return False, f"Bad response shape from {action}"
        if not data.get("success"):
            return False, data.get("error") or f"{action} returned success=false"
        return True, data.get("result")
    except Exception as e:
        return False, f"{action} request error: {e}"


def _ckan_http_post(api_url: str, api_key: str, action: str, payload: dict, debug: bool):
    endpoint = urljoin(api_url.rstrip("/") + "/", f"api/3/action/{action}")
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=15, verify=False)
        if debug:
            print(f"      HTTP {r.status_code} POST {endpoint} payload={payload}")
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict) or "success" not in data:
            return False, f"Bad response shape from {action}"
        if not data.get("success"):
            return False, data.get("error") or f"{action} returned success=false"
        return True, data.get("result")
    except Exception as e:
        return False, f"{action} request error: {e}"


# ============== 资源匹配（打分选择最优） ==============
def find_matching_resource(resources: List[dict], filename: str, debug: bool = False) -> Tuple[Optional[dict], Optional[datetime]]:
    if not resources:
        return None, None

    base = os.path.splitext(filename)[0]
    file_ext = os.path.splitext(filename)[1].lower().lstrip(".")

    ranked = []
    for res in resources:
        rname = (res.get("name") or "")
        rurl = (res.get("url") or "")
        rfmt = (res.get("format") or "").lower()

        score, reasons = 0, []

        if rname.lower() == filename.lower():
            score += 100; reasons.append("Exact filename match")
        elif rname.lower() == base.lower():
            score += 90; reasons.append("Filename base match")
        elif filename.lower() in rurl.lower():
            score += 80; reasons.append("URL contains filename")
        elif base.lower() in rurl.lower():
            score += 70; reasons.append("URL contains base")
        elif rfmt == file_ext and any(w for w in base.lower().split("_") if w and w in rname.lower()):
            score += 60; reasons.append("Format + partial name")
        elif len(resources) == 1:
            score += 50; reasons.append("Only resource")

        if score > 0:
            t = res.get("last_modified") or res.get("created")
            ts = parse_ckan_timestamp(t, debug)
            ranked.append((score, res, ts, reasons))
            if debug:
                print(f"         Resource match: {rname}")
                print(f"           Match score: {score}")
                print(f"           Match reasons: {', '.join(reasons)}")
                print(f"           Timestamp: {ts}")

    if not ranked:
        return None, None

    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_res, best_ts, why = ranked[0]
    if debug:
        print(f"         🏆 Best match: {best_res.get('name')} (score {best_score}) — {', '.join(why)}")
    return best_res, best_ts


# ============== 用包索引过滤“资源名”等字段（兜底路径） ==============
def _package_search_by_resource_name(api_url: str, api_key: str, filename: str, debug: bool):
    """
    用 package_search + fq=res_name:"<filename>" 精确找包含该资源名的数据集，
    返回 [(dataset_name, resource_dict), ...]
    """
    payload = {
        "q": "*:*",
        "fq": f'res_name:"{filename}"',
        "include_private": True,  # 带授权时可检索私有
        "rows": 100,
    }
    ok, res = _ckan_http_post(api_url, api_key, "package_search", payload, debug)
    if debug:
        print(f"   package_search fq=res_name:\"{filename}\" -> ok={ok}, count={res.get('count', 0) if isinstance(res, dict) else 'n/a'}")
    if not ok or not res or res.get("count", 0) == 0:
        return []

    hits = []
    for ds in res.get("results", []) or []:
        dname = ds.get("name")
        for r in ds.get("resources", []) or []:
            if (r.get("name") or "").lower() == filename.lower():
                hits.append((dname, r))
    return hits


# ============== 只按资源名查找（首选 resource_search，失败则兜底 package_search） ==============
def check_ckan_by_resource_only(file_path: str, api_url: str, api_key: str, debug: bool = False) -> Tuple[Optional[datetime], str]:
    """
    仅通过资源名定位资源并返回资源级时间戳（Berlin 时区）。
    优先 resource_search(POST)；若 500/空，则 fallback package_search+fq=res_name:"<文件名>"
    """
    filename = os.path.basename(file_path)

    if debug:
        print(f"🔎 Resource-first lookup for: {filename} (no package_show)")

    # --- A) 首选：resource_search (POST) ---
    queries = list({
        f'name:"{filename}"',
        f"name:{filename}",
    })
    pool = {}
    for q in queries:
        ok, res = _ckan_http_post(api_url, api_key, "resource_search", {"query": q, "limit": 100}, debug)
        if debug:
            print(f"   resource_search '{q}' -> ok={ok}")
        # 某些实例会 500，这里直接跳到 B
        if ok and res and res.get("results"):
            for r in res["results"]:
                rid = r.get("id")
                if rid and rid not in pool:
                    pool[rid] = r

    if pool:
        best_res, best_ts = find_matching_resource(list(pool.values()), filename, debug=debug)
        if best_res and not best_ts:
            ok2, full_r = _ckan_http_post(api_url, api_key, "resource_show", {"id": best_res.get("id")}, debug)
            if ok2 and full_r:
                t = full_r.get("last_modified") or full_r.get("created")
                best_ts = parse_ckan_timestamp(t, debug)
        if best_res and best_ts:
            return best_ts, f"Found by resource_search (resource_id={best_res.get('id')})"
        elif best_res:
            return None, f"Resource found but no timestamp (resource_id={best_res.get('id')})"

    # --- B) 兜底：package_search + fq=res_name:"<filename>" ---
    hits = _package_search_by_resource_name(api_url, api_key, filename, debug)
    if hits:
        ds_name, res = hits[0]  # 简单取第一个，如需更严格可再评分
        t = res.get("last_modified") or res.get("created")
        ts = parse_ckan_timestamp(t, debug)
        if ts:
            return ts, f'Found by package_search fq=res_name:"{filename}" in dataset {ds_name}'
        # 没时间戳就补一次 resource_show
        ok3, full_r = _ckan_http_post(api_url, api_key, "resource_show", {"id": res.get("id")}, debug)
        if ok3 and full_r:
            t2 = full_r.get("last_modified") or full_r.get("created")
            ts2 = parse_ckan_timestamp(t2, debug)
            if ts2:
                return ts2, f'Found by package_search+resource_show for "{filename}" in dataset {ds_name}'
        return None, f"Resource found in dataset {ds_name} but no timestamp"

    # 全部失败
    expected_id = re.sub(r"[^a-z0-9]", "", os.path.splitext(filename)[0].lower())
    return None, f"Not found by resource_search nor by fq=res_name (expected ID: {expected_id})"


# ============== 本地文件扫描 ==============
def is_file_allowed(filename: str) -> bool:
    low = filename.lower()
    if "*" in ALLOWED_EXTENSIONS:
        if EXCLUDED_EXTENSIONS and any(low.endswith(ext) for ext in EXCLUDED_EXTENSIONS if ext):
            return False
        return True
    return low.endswith(ALLOWED_EXTENSIONS)


def get_file_category(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    categories = {
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        "Spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
        "Data": [".json", ".xml", ".yaml", ".yml", ".sql"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Scripts": [".py", ".js", ".sh", ".bat", ".ps1", ".r"],
        "Config": [".ini", ".conf", ".cfg", ".properties", ".env"],
        "Media": [".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac"],
        "3D Models": [".stl", ".obj", ".fbx", ".gltf", ".glb", ".ifc", ".step", ".stp", ".iges", ".igs"],
        "2D Geo Files": [
            ".shp", ".kml", ".kmz", ".gpx", ".geojson", ".gml",
            ".dwg", ".dxf", ".gpkg", ".tif", ".tiff", ".ecw", ".jp2", ".img",
            ".asc", ".las", ".laz",
        ],
    }
    for cat, exts in categories.items():
        if ext in exts:
            return cat
    return "Other" if ext else "No Extension"


def scan_directory(directory: str, debug: bool = False) -> Dict[str, dict]:
    file_info: Dict[str, dict] = {}
    total_files, excluded_files = 0, 0

    if debug:
        print(f"🔍 Scanning directory: {directory}")
        print(f"   Allowed extensions: {ALLOWED_EXTENSIONS}")
        print(f"   Excluded extensions: {EXCLUDED_EXTENSIONS}")

    for root, dirs, files in os.walk(directory):
        root_norm = os.path.normpath(root)
        dir_norm = os.path.normpath(directory)
        if root_norm != dir_norm and any(ex in root for ex in EXCLUDE_DIRS if ex):
            if debug:
                print(f"   ⏭️  Skip excluded directory: {root}")
            continue

        for fname in files:
            total_files += 1
            if not is_file_allowed(fname):
                excluded_files += 1
                continue
            try:
                path = os.path.join(root, fname)
                st = os.stat(path)
                created = BERLIN_TZ.localize(datetime.fromtimestamp(st.st_ctime))
                file_info[os.path.normpath(path)] = {
                    "path": os.path.normpath(path),
                    "created": created,
                    "size": st.st_size,
                    "category": get_file_category(fname),
                }
            except (OSError, IOError):
                continue

    print(f"📊 Scan complete: {total_files} files, {excluded_files} excluded, {len(file_info)} included")
    return file_info


# ============== 结果展示 ==============
def display_results(outdated: List[dict]) -> None:
    if not outdated:
        print("\n✅ All files are already in CKAN and up to date!")
        return

    print(f"\n📤 Files that need synchronization ({len(outdated)} files):")

    files_by_reason = defaultdict(list)
    files_by_category = defaultdict(lambda: defaultdict(list))
    total_size = 0

    for f in outdated:
        reason = f.get("reason", "Needs sync")
        files_by_reason[reason].append(f)

        category = f.get("category", "Other")
        ext = os.path.splitext(f["path"])[1].lower() or "no extension"
        files_by_category[category][ext].append(f)

        total_size += f.get("size", 0)

    print("\n📊 Sync reason statistics:")
    for reason, files in files_by_reason.items():
        print(f"   {reason}: {len(files)} files")

    for category in sorted(files_by_category.keys()):
        print(f"\n=== {category.upper()} ===")
        by_ext = files_by_category[category]
        for ext in sorted(by_ext.keys()):
            group = by_ext[ext]
            group_size = sum(item.get("size", 0) for item in group)
            print(f"\n{ext.upper()} files ({len(group)} files, {format_size(group_size)}):")
            for item in sorted(group, key=lambda x: x["path"]):
                fname = os.path.basename(item["path"])
                size_str = format_size(item.get("size", 0))
                reason = item.get("reason", "Needs sync")
                icon = "🆕" if reason == "Missing in CKAN" else "📝"
                print(f"  {icon} {fname} ({size_str}) - {reason}")

    print(f"\n📊 Total: {len(outdated)} files, {format_size(total_size)}")
    print("\n💡 Legend:")
    print("   🆕 = File not in CKAN (create dataset/resource)")
    print("   📝 = Local file is newer than CKAN (update resource)")
    print("   🎯 = Resource-level timestamp comparison")


# ============== 主流程 ==============
def main():
    parser = argparse.ArgumentParser(description="CKAN Resource-First File Monitor")
    parser.add_argument("--debug", action="store_true", help="enable verbose debug logs")
    args = parser.parse_args()
    debug = args.debug

    print("=== 🎯 CKAN Resource-First File Monitoring ===")
    print(f"📂 Monitor directory: {MONITOR_DIR}")
    print(f"🌍 Berlin time now: {datetime.now(BERLIN_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    api_key, api_url, _, _ = load_config()
    print(f"🌐 CKAN server: {api_url}")
    print(f"🔐 API key: {'Set' if api_key else 'Not set'}")

    # 简单健康检查
    ok, res = _ckan_http_get(api_url, api_key, "status_show", {}, debug)
    print(f"🔗 Connection: {'✅ OK' if ok else '❌ ' + str(res)}")

    local_files = scan_directory(MONITOR_DIR, debug=debug)

    outdated: List[dict] = []
    for path, info in local_files.items():
        fname = os.path.basename(path)
        print(f"\n📄 Processing file: {fname}")
        ckan_time, status = check_ckan_by_resource_only(path, api_url, api_key, debug=debug)
        print(f"   CKAN status: {status}")

        if ckan_time:
            local_time = info["created"]
            if local_time > ckan_time:
                print(f"   📤 Local is newer (local {local_time.strftime('%Y-%m-%d %H:%M')}, CKAN {ckan_time.strftime('%Y-%m-%d %H:%M')})")
                outdated.append({**info, "reason": "Local is newer"})
            else:
                print("   ✅ Up to date")
        else:
            print("   📤 Not found in CKAN → needs create")
            outdated.append({**info, "reason": "Missing in CKAN"})

    print(f"\n📊 Found {len(outdated)} files that need synchronization")
    display_results(outdated)

    print(f"\n⏱️  Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=== ✅ Monitoring complete ===")


if __name__ == "__main__":
    main()
