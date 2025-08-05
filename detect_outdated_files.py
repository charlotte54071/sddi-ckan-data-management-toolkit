#!/usr/bin/env python3
"""
A tool to monitor local files and sync them with CKAN datasets.
Compares file timestamps with CKAN resource timestamps for accurate synchronization.
"""

import os
import configparser
import json
from datetime import datetime, timezone
from collections import defaultdict
import re
import pytz
from ckan_manager import CKANManager

# Import the unified CKAN manager

# === TIMEZONE CONFIGURATION ===
BERLIN_TZ = pytz.timezone('Europe/Berlin')
UTC_TZ = pytz.UTC

def convert_utc_to_berlin(utc_datetime):
    """Convert UTC datetime to Berlin time"""
    if utc_datetime is None:
        return None
    
    # If datetime is naive (no timezone), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = UTC_TZ.localize(utc_datetime)
    
    # Convert to Berlin time
    berlin_time = utc_datetime.astimezone(BERLIN_TZ)
    return berlin_time

def parse_ckan_timestamp(timestamp_str, debug=False):
    """Parse CKAN timestamp (UTC) and convert to Berlin time"""
    if not timestamp_str or timestamp_str == 'N/A':
        return None
    
    try:
        # Parse UTC timestamp from CKAN
        utc_datetime = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Convert to Berlin time
        berlin_datetime = convert_utc_to_berlin(utc_datetime)
        
        if debug:
            print(f"      🕐 timestamp transformation:")
            print(f"         CKAN UTC: {utc_datetime}")
            print(f"         Berlin time: {berlin_datetime}")
        
        return berlin_datetime
    except Exception as e:
        if debug:
            print(f"         ❌ timestamp parse fail: {e}")
        return None

# === SETUP ===
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file not found at {config_path}")
config.read(config_path)

def load_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    api_key = config.get('DEFAULT', 'api_key', fallback=None)
    instance_url = config.get('DEFAULT', 'instance_url', fallback=None)
    path = config.get('DEFAULT', 'excel_file_path', fallback=None)
    schema_config = config.get('DEFAULT', 'schema_config', fallback=None)
    return api_key, instance_url, path, schema_config

# === CONFIGURATION ===
MONITOR_DIR = r'D:\ckan-docker-CKANofficial\sddi-import-export-excel-tool\TEST'
ALLOWED_EXTENSIONS = tuple(config.get('Monitoring', 'allowed_extensions', fallback='*').lower().split(','))
EXCLUDE_DIRS = tuple(config.get('Monitoring', 'exclude_dirs', fallback='__pycache__,schema_templates,templates').split(','))
EXCLUDED_EXTENSIONS = tuple(config.get('Monitoring', 'excluded_extensions', fallback='.tmp,.log,.cache,.pyc,.pyo,.bak,.swp,.DS_Store').lower().split(','))
TRACKING_FILE = 'file_tracking.json'

# CKAN Configuration
if 'CKAN' in config:
    CKAN_API_URL = config.get('CKAN', 'api_url', fallback='http://localhost:5000')
    CKAN_API_KEY = config.get('CKAN', 'api_key', fallback='')
else:
    CKAN_API_URL = 'http://localhost:5000'
    CKAN_API_KEY = ''

if not CKAN_API_URL or CKAN_API_URL.lower() == 'none':
    CKAN_API_URL = 'http://localhost:5000'
elif not CKAN_API_URL.startswith(('http://', 'https://')):
    CKAN_API_URL = f'http://{CKAN_API_URL}'

# CKAN Manager is now imported from ckan_manager.py

def debug_search_results(ckan_manager, search_terms=None, file_path=None, verbose=True):
    """
    General debug function for searching CKAN datasets
    
    Args:
        ckan_manager: CKAN manager instance
        search_terms: List of custom search terms, or None to auto-generate from file_path
        file_path: File path to generate search terms from (if search_terms is None)
        verbose: Whether to show detailed output
    """
    print(f"\n🔍 === General Search Debug ===")
    
    # Auto-generate search terms if not provided
    if search_terms is None:
        if file_path:
            search_terms = generate_search_terms_from_file(file_path)
            print(f"📁 Auto-generated search terms from: {file_path}")
        else:
            print("❌ Error: Either search_terms or file_path must be provided")
            return
    
    if not search_terms:
        print("❌ No search terms to process")
        return
    
    print(f"🔍 Searching with {len(search_terms)} terms: {search_terms}")
    
    for term in search_terms:
        print(f"\n📝 Search term: '{term}'")
        try:
            result = ckan_manager.search_datasets(term)
            
            if result and result.get('success'):
                search_result = result['result']
                count = search_result.get('count', 0)
                results = search_result.get('results', [])
                
                print(f"   📊 Results found: {count}")
                
                if count > 0:
                    print(f"   📋 Datasets:")
                    for i, dataset in enumerate(results):
                        name = dataset.get('name', 'N/A')
                        title = dataset.get('title', 'N/A')
                        resources = dataset.get('resources', [])
                        print(f"      {i+1}. {name} - {title} ({len(resources)} resources)")
                        
                        if verbose:
                            # Check dataset name and title matches
                            name_match = term.lower() in name.lower()
                            title_match = term.lower() in title.lower()
                            print(f"         Name match: {'✅' if name_match else '❌'}")
                            print(f"         Title match: {'✅' if title_match else '❌'}")
                            
                            # Check resources
                            for j, resource in enumerate(resources):
                                res_name = resource.get('name', 'N/A')
                                res_url = resource.get('url', 'N/A')
                                res_created = resource.get('created', 'N/A')
                                res_modified = resource.get('last_modified', 'N/A')
                                print(f"         Resource {j+1}: {res_name}")
                                print(f"           URL: {res_url}")
                                print(f"           Created: {res_created}")
                                print(f"           Modified: {res_modified}")
                                
                                # Check resource matches
                                res_name_match = term.lower() in res_name.lower()
                                res_url_match = term.lower() in res_url.lower()
                                print(f"           Resource name match: {'✅' if res_name_match else '❌'}")
                                print(f"           Resource URL match: {'✅' if res_url_match else '❌'}")
                else:
                    print(f"   ❌ No matching datasets found")
            else:
                print(f"   ❌ API call failed: {result}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def generate_search_terms_from_file(file_path):
    """
    Generate search terms from a file path for general searching
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of search terms
    """
    if not file_path:
        return []
    
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    search_terms = []
    
    # 1. Original filename (with and without extension)
    search_terms.append(filename)
    search_terms.append(name_without_ext)
    
    # 2. Lowercase versions
    search_terms.append(filename.lower())
    search_terms.append(name_without_ext.lower())
    
    # 3. CKAN standardized version (alphanumeric only)
    ckan_standardized = re.sub(r'[^a-z0-9]', '', name_without_ext.lower())
    if ckan_standardized:
        search_terms.append(ckan_standardized)
    
    # 4. Replace underscores/hyphens with spaces
    spaced_version = re.sub(r'[_-]', ' ', name_without_ext)
    if spaced_version != name_without_ext:
        search_terms.append(spaced_version)
    
    # 5. Individual words (if filename contains separators)
    words = re.split(r'[_\-\s]+', name_without_ext)
    for word in words:
        if len(word) > 2:  # Only add meaningful words
            search_terms.append(word)
            search_terms.append(word.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in search_terms:
        if term and term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    return unique_terms

def generate_possible_dataset_ids(file_path):
    """
    Generate possible CKAN dataset IDs from file path
    Based on CKAN's actual standardization logic: title.lower() + keep only alphanumeric characters
    """
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    possible_ids = []
    
    # 1. 🥇 Use CKAN's actual standardization logic (most important)
    ckan_standardized = re.sub(r'[^a-z0-9]', '', name_without_ext.lower())
    if ckan_standardized:
        possible_ids.append(ckan_standardized)
    
    # 2. 🥈 CKAN standardization based on full filename
    full_name_standardized = re.sub(r'[^a-z0-9]', '', filename.lower())
    if full_name_standardized and full_name_standardized != ckan_standardized:
        possible_ids.append(full_name_standardized)
    
    # 3. 🥉 Original filename variants (as fallback)
    if name_without_ext and name_without_ext.lower() != name_without_ext:
        possible_ids.append(name_without_ext)
    
    # 4. 🔧 Simple lowercase variant
    simple_lowercase = name_without_ext.lower()
    if simple_lowercase and simple_lowercase not in possible_ids:
        possible_ids.append(simple_lowercase)
    
    # 5. 🔄 Hyphenated version (may be used in some cases)
    dash_version = re.sub(r'[^a-z0-9]+', '-', name_without_ext.lower()).strip('-')
    if dash_version and dash_version not in possible_ids:
        possible_ids.append(dash_version)
    
    # Remove empty strings and duplicates while preserving order
    seen = set()
    unique_ids = []
    for id in possible_ids:
        if id and id not in seen:
            seen.add(id)
            unique_ids.append(id)
    
    return unique_ids

def find_matching_resource(resources, filename, debug=False):
    """
    Find matching resource in resources list
    Returns (matching_resource, timestamp) or (None, None)
    """
    if not resources:
        return None, None
    
    name_without_ext = os.path.splitext(filename)[0]
    
    # Matching strategies sorted by priority
    matching_strategies = []
    
    for resource in resources:
        resource_name = resource.get('name', '')
        resource_url = resource.get('url', '')
        resource_format = resource.get('format', '').lower()
        file_extension = os.path.splitext(filename)[1].lower().lstrip('.')
        
        match_score = 0
        match_reasons = []
        
        # 1. 🥇 Resource name exactly matches filename
        if resource_name.lower() == filename.lower():
            match_score += 100
            match_reasons.append("Exact filename match")
        
        # 2. 🥈 Resource name matches filename (without extension)
        elif resource_name.lower() == name_without_ext.lower():
            match_score += 90
            match_reasons.append("Filename match (no extension)")
        
        # 3. 🥉 URL contains complete filename
        elif filename.lower() in resource_url.lower():
            match_score += 80
            match_reasons.append("URL contains filename")
        
        # 4. 🔧 URL contains filename (without extension)
        elif name_without_ext.lower() in resource_url.lower():
            match_score += 70
            match_reasons.append("URL contains filename base")
        
        # 5. 🔄 Format match + partial name match
        elif (resource_format == file_extension and 
              any(word in resource_name.lower() for word in name_without_ext.lower().split('_') if len(word) > 2)):
            match_score += 60
            match_reasons.append("Format match + partial name match")
        
        # 6. 🎯 If only one resource, it might be the one
        elif len(resources) == 1:
            match_score += 50
            match_reasons.append("Only resource")
        
        if match_score > 0:
            # Get resource timestamp
            resource_time_str = resource.get('last_modified') or resource.get('created')
            resource_timestamp = None
            
            if resource_time_str:
                resource_timestamp = parse_ckan_timestamp(resource_time_str, debug)
            
            matching_strategies.append((
                match_score, 
                resource, 
                resource_timestamp, 
                match_reasons
            ))
            
            if debug:
                print(f"         Resource match: {resource_name}")
                print(f"           Match score: {match_score}")
                print(f"           Match reasons: {', '.join(match_reasons)}")
                print(f"           Timestamp: {resource_timestamp}")
    
    # Sort by match score, select best match
    if matching_strategies:
        matching_strategies.sort(key=lambda x: x[0], reverse=True)
        best_match_score, best_resource, best_timestamp, best_reasons = matching_strategies[0]
        
        if debug:
            print(f"         🏆 Best match: {best_resource.get('name')} (score: {best_match_score})")
            print(f"           Reasons: {', '.join(best_reasons)}")
        
        return best_resource, best_timestamp
    
    return None, None

def check_ckan_dataset_with_resource_timestamp(ckan_manager, file_path, debug=False):
    """
    Fixed version: Check Resource-level timestamps instead of Dataset-level
    """
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    expected_ckan_name = re.sub(r'[^a-z0-9]', '', name_without_ext.lower())
    
    if not ckan_manager.connection_available:
        return None, "CKAN service unavailable"
    
    if debug:
        print(f"🔍 Smart file lookup: {filename}")
        print(f"   Expected ID based on CKAN standardization logic: {expected_ckan_name}")
    
    # Strategy 1: Try possible dataset IDs by priority
    possible_ids = generate_possible_dataset_ids(file_path)
    
    if debug:
        print(f"   Try order: {possible_ids}")
    
    for i, dataset_id in enumerate(possible_ids):
        if debug:
            if i == 0:
                priority = "🥇 Highest"
            elif i == 1:
                priority = "🥈 High"
            elif i < 4:
                priority = "🥉 Medium"
            else:
                priority = "🔧 Low"
            print(f"   Try ID [{priority} priority]: {dataset_id}")
        
        result = ckan_manager.get_dataset_by_id(dataset_id)
        if result and result.get('success'):
            dataset = result['result']
            
            # 🎯 Key fix: Check Resource-level timestamps
            resources = dataset.get('resources', [])
            
            if debug:
                print(f"      ✅ Found dataset: {dataset_id}")
                print(f"         Dataset title: {dataset.get('title', 'N/A')}")
                print(f"         Dataset created: {dataset.get('metadata_created', 'N/A')}")
                print(f"         Dataset modified: {dataset.get('metadata_modified', 'N/A')}")
                print(f"         Resources count: {len(resources)}")
            
            # Find matching Resource
            matching_resource, resource_timestamp = find_matching_resource(resources, filename, debug)
            
            if matching_resource and resource_timestamp:
                if debug:
                    print(f"   ✅ Successfully found matching Resource")
                    print(f"      Resource name: {matching_resource.get('name', 'N/A')}")
                    print(f"      Resource time: {resource_timestamp}")
                    print(f"      🎯 Using Resource timestamp for comparison!")
                return resource_timestamp, f"Found dataset resource: {dataset_id}"
            
            # If found Dataset but no matching Resource
            elif resources:
                # Use latest Resource timestamp
                latest_resource_time = None
                for resource in resources:
                    resource_time_str = resource.get('last_modified') or resource.get('created')
                    if resource_time_str:
                        resource_time = parse_ckan_timestamp(resource_time_str, debug)
                        if resource_time and (not latest_resource_time or resource_time > latest_resource_time):
                            latest_resource_time = resource_time
                
                if latest_resource_time:
                    if debug:
                        print(f"   ⚠️  Found dataset but no exact matching Resource, using latest Resource timestamp")
                        print(f"      Latest Resource time: {latest_resource_time}")
                    return latest_resource_time, f"Found dataset (using latest resource): {dataset_id}"
                else:
                    # If Resources have no valid timestamps, use Dataset timestamp
                    dataset_time_str = dataset.get('metadata_modified') or dataset.get('metadata_created')
                    if dataset_time_str:
                        dataset_time = parse_ckan_timestamp(dataset_time_str, debug)
                        if dataset_time:
                            if debug:
                                print(f"   ⚠️  Resource has no valid timestamp, using Dataset timestamp")
                                print(f"      Dataset time: {dataset_time}")
                            return dataset_time, f"Found dataset (using dataset time): {dataset_id}"
            
            # If dataset exists but has no Resources
            else:
                if debug:
                    print(f"   ⚠️  Dataset exists but has no Resources")
                dataset_time_str = dataset.get('metadata_modified') or dataset.get('metadata_created')
                if dataset_time_str:
                    dataset_time = parse_ckan_timestamp(dataset_time_str, debug)
                    if dataset_time:
                        return dataset_time, f"Found empty dataset: {dataset_id}"
                    
        elif debug:
            print(f"      ❌ Not found: {dataset_id}")
    
    # Strategy 2: Search strategy (also check Resources)
    if debug:
        print(f"   🔍 Search strategy: Search by filename")
    
    # Extended search queries, including more possible variants
    search_queries = [
        name_without_ext, 
        expected_ckan_name,
        filename,  # Complete filename with extension
        name_without_ext.replace('_', ' '),  # Replace underscores with spaces
        name_without_ext.replace('_', '-'),  # Replace underscores with hyphens
    ]
    
    # For CV/resume files, add more search terms
    if any(keyword in name_without_ext.lower() for keyword in ['cv', 'resume', 'curriculum']):
        search_queries.extend(['cv', 'resume', 'curriculum vitae'])
    
    # Remove duplicates and filter empty strings
    search_queries = list(set([q for q in search_queries if q]))
    
    for query in search_queries:
        if debug:
            print(f"   Search query: '{query}'")
        
        search_result = ckan_manager.search_datasets(query)
        if search_result and search_result.get('success'):
            search_data = search_result['result']
            count = search_data.get('count', 0)
            datasets = search_data.get('results', [])
            
            if debug:
                print(f"      Search results count: {count}")
            
            if count > 0 and datasets:
                # Strict match validation
                valid_matches = []
                
                for dataset in datasets:
                    dataset_name = dataset.get('name', '')
                    dataset_title = dataset.get('title', '')
                    
                    # Strict match conditions
                    if dataset_name == expected_ckan_name:
                        valid_matches.append(('perfect', dataset))
                        if debug:
                            print(f"      🎯 Perfect match: {dataset_name}")
                    elif dataset_name.lower() == name_without_ext.lower():
                        valid_matches.append(('name', dataset))
                        if debug:
                            print(f"      ✅ Name match: {dataset_name}")
                    elif (name_without_ext.lower() in dataset_title.lower() and 
                          len(name_without_ext) > 3):
                        title_words = set(dataset_title.lower().split())
                        filename_words = set(name_without_ext.lower().replace('_', ' ').split())
                        
                        if filename_words and len(filename_words & title_words) / len(filename_words) >= 0.5:
                            valid_matches.append(('title', dataset))
                            if debug:
                                print(f"      🔍 Title match: {dataset_title}")
                
                # Sort by match quality
                if valid_matches:
                    valid_matches.sort(key=lambda x: {'perfect': 0, 'name': 1, 'title': 2}[x[0]])
                    best_match_type, best_dataset = valid_matches[0]
                    
                    # Check this dataset's Resources
                    resources = best_dataset.get('resources', [])
                    matching_resource, resource_timestamp = find_matching_resource(resources, filename, debug)
                    
                    if matching_resource and resource_timestamp:
                        dataset_id = best_dataset.get('name')
                        if debug:
                            print(f"   ✅ Found matching Resource through search: {dataset_id}")
                        return resource_timestamp, f"Found resource through search: {dataset_id}"
                    elif resources:
                        # Use latest Resource timestamp
                        latest_resource_time = None
                        for resource in resources:
                            resource_time_str = resource.get('last_modified') or resource.get('created')
                            if resource_time_str:
                                resource_time = parse_ckan_timestamp(resource_time_str, debug)
                                if resource_time and (not latest_resource_time or resource_time > latest_resource_time):
                                    latest_resource_time = resource_time
                        
                        if latest_resource_time:
                            dataset_id = best_dataset.get('name')
                            if debug:
                                print(f"   ✅ Found dataset through search, using latest Resource: {dataset_id}")
                            return latest_resource_time, f"Found through search (latest resource): {dataset_id}"
    
    if debug:
        print(f"   ❌ All strategies failed to find matching dataset or resource")
    
    return None, f"Not found (expected ID: {expected_ckan_name})"

def is_file_allowed(filename):
    filename_lower = filename.lower()
    if '*' in ALLOWED_EXTENSIONS:
        if EXCLUDED_EXTENSIONS and any(filename_lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS if ext):
            return False
        return True
    return filename_lower.endswith(ALLOWED_EXTENSIONS)

def get_file_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    categories = {
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'Spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
        'Data': ['.json', '.xml', '.yaml', '.yml', '.sql'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff', '.webp'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'Scripts': ['.py', '.js', '.sh', '.bat', '.ps1', '.r'],
        'Config': ['.ini', '.conf', '.cfg', '.properties', '.env'],
        'Media': ['.mp4', '.avi', '.mov', '.mp3', '.wav', '.flac']
    }
    
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    
    return 'Other' if ext else 'No Extension'

def scan_directory(directory, debug=False):
    file_info = {}
    total_files_scanned = 0
    excluded_files = 0
    
    if debug:
        print(f"🔍 Scanning directory: {directory}")
        print(f"   Allowed extensions: {ALLOWED_EXTENSIONS}")
        print(f"   Excluded extensions: {EXCLUDED_EXTENSIONS}")
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        root_normalized = os.path.normpath(root)
        directory_normalized = os.path.normpath(directory)
        
        if root_normalized != directory_normalized:
            if any(exclude in root for exclude in EXCLUDE_DIRS if exclude):
                if debug:
                    print(f"   ⏭️  Skip excluded directory: {root}")
                continue
        
        for fname in files:
            total_files_scanned += 1
            if debug:
                print(f"   📄 Checking file: {fname}")
            
            if not is_file_allowed(fname):
                excluded_files += 1
                if debug:
                    print(f"      ❌ Excluded by filter")
                continue
            
            try:
                path = os.path.join(root, fname)
                stat = os.stat(path)
                # Convert local file timestamps to Berlin timezone
                created_time = BERLIN_TZ.localize(datetime.fromtimestamp(stat.st_ctime))
                normalized_path = os.path.normpath(path)
                
                file_info[normalized_path] = {
                    'path': normalized_path,
                    'created': created_time,
                    'size': stat.st_size,
                    'category': get_file_category(fname)
                }
                
                if debug:
                    print(f"      ✅ Added (size: {stat.st_size} bytes)")
            except (OSError, IOError) as e:
                if debug:
                    print(f"      ❌ Cannot access: {e}")
                continue
    
    print(f"📊 Scan complete: {total_files_scanned} files, {excluded_files} excluded, {len(file_info)} included")
    return file_info

def load_file_tracking():
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                data = json.load(f)
                tracking_data = {}
                for k, v in data.items():
                    dt = datetime.fromisoformat(v)
                    # If datetime is naive, assume it's Berlin time
                    if dt.tzinfo is None:
                        dt = BERLIN_TZ.localize(dt)
                    tracking_data[k] = dt
                return tracking_data
        except:
            return {}
    return {}

def save_file_tracking(tracking_data):
    data = {k: v.isoformat() for k, v in tracking_data.items()}
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def display_results(outdated_files):
    if not outdated_files:
        print("\n✅ All files are already in CKAN and up to date!")
        return
    
    print(f"\n📤 Files that need synchronization ({len(outdated_files)} files):")
    
    files_by_category = defaultdict(lambda: defaultdict(list))
    files_by_reason = defaultdict(list)
    total_size = 0
    
    for file_info in outdated_files:
        path = file_info['path']
        category = file_info['category']  
        ext = os.path.splitext(path)[1].lower() or 'no extension'
        size = file_info.get('size', 0)
        reason = file_info.get('reason', 'Needs sync')
        
        files_by_category[category][ext].append({
            'path': path,
            'size': size,
            'reason': reason
        })
        files_by_reason[reason].append(file_info)
        total_size += size
    
    # Display summary by reason first
    print(f"\n📊 Sync reason statistics:")
    for reason, files in files_by_reason.items():
        print(f"   {reason}: {len(files)} files")
    
    # Display detailed results by category
    for category in sorted(files_by_category.keys()):
        print(f"\n=== {category.upper()} ===")
        extensions = files_by_category[category]
        
        for ext in sorted(extensions.keys()):
            file_list = extensions[ext]
            category_size = sum(f['size'] for f in file_list)
            print(f"\n{ext.upper()} files ({len(file_list)} files, {format_file_size(category_size)}):")
            
            for file_data in sorted(file_list, key=lambda x: x['path']):
                filename = os.path.basename(file_data['path'])
                size_str = format_file_size(file_data['size'])
                reason = file_data['reason']
                reason_icon = "🆕" if reason == "Missing in CKAN" else "📝"
                print(f"  {reason_icon} {filename} ({size_str}) - {reason}")
    
    print(f"\n📊 Total: {len(outdated_files)} files, {format_file_size(total_size)}")
    
    # Add helpful tips
    print(f"\n💡 Explanation:")
    print(f"   🆕 = File does not exist in CKAN, needs to create new dataset")
    print(f"   📝 = Local file is newer than CKAN version, needs to update dataset")
    print(f"   🎯 = Now using Resource timestamps for accurate comparison!")

def debug_tracking_file():
    """Debug tracking file content"""
    print(f"\n🔍 === Debug tracking file ===")
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                data = json.load(f)
            print(f"Tracking file content:")
            for path, timestamp in data.items():
                print(f"   {os.path.basename(path)}: {timestamp}")
        except Exception as e:
            print(f"Failed to read tracking file: {e}")
    else:
        print(f"Tracking file does not exist: {TRACKING_FILE}")

def main():
    """Main function"""
    print("🔍 Starting outdated file detection...")
    
    # Load configuration
    api_key, api_url, path, schema_config = load_config()
    
    # Initialize CKAN manager
    ckan_manager = CKANManager(api_url, api_key)
    
    # Scan local files
    local_files = scan_directory(MONITOR_DIR)
    print(f"📁 Found {len(local_files)} local files")
    
    # Get CKAN datasets
    print("🌐 Getting CKAN datasets...")
    datasets = ckan_manager.get_all_datasets()
    print(f"📊 Found {len(datasets)} CKAN datasets")
    
    # Compare files
    print("⚖️ Comparing files...")
    outdated_files = []
    
    for file_path, info in local_files.items():
        filename = os.path.basename(file_path)
        print(f"\n📄 Processing file: {filename}")
        
        ckan_time, status = check_ckan_dataset_with_resource_timestamp(ckan_manager, file_path, False)
        
        if ckan_time:
            local_time = info['created']
            if local_time > ckan_time:
                outdated_files.append({
                    'file': filename,
                    'local_time': local_time,
                    'ckan_time': ckan_time,
                    'dataset_name': status,
                    'resource_name': filename
                })
        else:
            outdated_files.append({
                'file': filename,
                'local_time': info['created'],
                'ckan_time': None,
                'dataset_name': 'Not found',
                'resource_name': filename
            })
    
    # Output results
    print(f"\n📋 Detection complete! Found {len(outdated_files)} potentially outdated files:")
    for file_info in outdated_files:
        print(f"  📄 {file_info['file']}")
        print(f"     Local time: {file_info['local_time']}")
        print(f"     CKAN time: {file_info['ckan_time']}")
        print(f"     Dataset: {file_info['dataset_name']}")
        print(f"     Resource: {file_info['resource_name']}")
        print()

def main_resource_timestamp_version():
    """Main program for resource timestamp version"""
    print("=== 🎯 CKAN Smart File Monitoring Tool (Resource Timestamp Version) ===")
    print(f"📂 Monitor directory: {MONITOR_DIR}")
    print(f"🎯 New feature: Use Resource timestamps for precise comparison!")
    print(f"🌍 Timezone handling: CKAN UTC → Berlin time (automatic conversion)")
    print(f"   Current Berlin time: {datetime.now(BERLIN_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    debug_mode = input("Enable debug mode? (y/N): ").lower().startswith('y')
    force_check = input("Force check all files (ignore tracking status)? (y/N): ").lower().startswith('y')
    
    api_key, api_url, path, schema_config = load_config()
    ckan_manager = CKANManager(api_url, api_key, debug=debug_mode)
    
    print(f"🌐 CKAN server: {api_url}")
    print(f"🔐 API key: {'Set' if api_key else 'Not set'}")
    print(f"🔗 Connection status: {'✅ Normal' if ckan_manager.connection_available else '❌ Failed'}")
    
    if debug_mode:
        debug_search_results(ckan_manager)
        debug_tracking_file()
    
    # Scan files
    local_files = scan_directory(MONITOR_DIR, debug_mode)
    
    if force_check:
        print(f"🔄 Force check mode: Will check all {len(local_files)} files")
        files_to_check = local_files
    else:
        # Normal tracking logic
        tracking_data = load_file_tracking()
        files_to_check = {}
        
        for file_path, info in local_files.items():
            current_created = info['created']
            last_seen_created = tracking_data.get(file_path)
            
            # Check if file has changed or doesn't exist in CKAN
            is_changed = not last_seen_created or current_created > last_seen_created
            ckan_time, _ = check_ckan_dataset_with_resource_timestamp(ckan_manager, file_path, False)
            
            if is_changed or not ckan_time:
                files_to_check[file_path] = info
    
    print(f"📊 Will check {len(files_to_check)} files' CKAN status")
    
    # Check file status
    outdated_files = []
    for file_path, info in files_to_check.items():
        filename = os.path.basename(file_path)
        print(f"\n📄 Processing file: {filename}")
        
        ckan_time, status = check_ckan_dataset_with_resource_timestamp(ckan_manager, file_path, debug_mode)
        print(f"   CKAN status: {status}")
        
        if ckan_time:
            local_time = info['created']
            time_diff = (local_time - ckan_time).total_seconds()
            
            if debug_mode:
                print(f"   🕐 Time comparison:")
                print(f"      Local file: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      CKAN resource: {ckan_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      Time difference: {time_diff:.0f} seconds")
            
            if local_time > ckan_time:
                print(f"   📤 Local file is newer (Local: {local_time.strftime('%Y-%m-%d %H:%M')}, CKAN: {ckan_time.strftime('%Y-%m-%d %H:%M')})")
                outdated_files.append({**info, 'reason': 'Local is newer', 'time_diff': time_diff})
            else:
                print(f"   ✅ File is up to date (Local: {local_time.strftime('%Y-%m-%d %H:%M')}, CKAN: {ckan_time.strftime('%Y-%m-%d %H:%M')})")
        else:
            print(f"   📤 Not found in CKAN, needs upload")
            outdated_files.append({**info, 'reason': 'Missing in CKAN'})
    
    print(f"\n📊 Found {len(outdated_files)} files that need synchronization")
    
    # Display results
    display_results(outdated_files)
    
    # If not force check mode, update tracking file
    if not force_check:
        tracking_data = load_file_tracking()
        # Update tracking data
        for file_path, info in local_files.items():
            tracking_data[file_path] = info['created']
        
        # Clean up non-existent files
        existing_paths = set(local_files.keys())
        tracking_data = {k: v for k, v in tracking_data.items() if k in existing_paths}
        
        save_file_tracking(tracking_data)
        print(f"\n💾 Updated tracking file")
    
    print(f"\n⏱️  Scan completed at: {datetime.now()}")
    print("=== 🎯 Monitoring complete ===")

if __name__ == "__main__":
    main_resource_timestamp_version()