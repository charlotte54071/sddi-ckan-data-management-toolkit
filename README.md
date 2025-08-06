# CKAN Catalog Creation Automation

## Table of Contents

- [Overview](#overview)
- [Functionality](#functionality)
- [Code Structure](#code-structure)
  - [`create_cat.py`](#create_cat.py)
  - [`write_cat.py`](#write_cat.py)
  - [`schema_manager.py`](#schema_manager.py)
- [Config](#config)
- [Usage](#usage)
- [Schemas](#schemas)
- [Example](#example)

## Overview
This repository contains scripts for managing metadata of catalog entries between an Excel file and a CKAN instance, supporting multiple SDDI schemas. The main purpose is to automate the process of catalog creation and data retrieval. It includes configuration handling, API communication, Excel manipulation, and data validation.

## Functionality

### `create_cat.py`
Automates the process of reading catalog metadata from an Excel file (`SDDI-Metadata.xlsx`), processing it based on schema type, and uploading it to a CKAN instance via API calls.

### `write_cat.py`
Automates the process of retrieving, processing, and inserting catalog data into the `SDDI-Metadata.xlsx` Excel file.

### `schema_manager.py`
Manages different SDDI schemas and their mappings between Excel columns and CKAN fields.

### `detect_outdated_files.py`
Monitors a specified directory for new or changed files based on creation timestamps, compares them with CKAN catalog entries, and reports files that need updating. Features include per-file tracking, configurable filtering, and optimization for large directories.

**🆕 Enhanced File Type Support:**
- **3D Models**: OBJ, FBX, DAE, 3DS, Blender (.blend), Maya (.ma/.mb), Cinema4D (.c4d), STL, PLY, glTF/GLB, USD, IFC, STEP/STP files
- **2D Geo Files**: Shapefile (.shp), KML/KMZ, GPX, GeoJSON, GML, AutoCAD (.dwg/.dxf), GeoTIFF, NetCDF (.nc), HDF5, LAS/LAZ point clouds

![workflow_import-export_excell_ckan](https://github.com/user-attachments/assets/38118a46-2d31-4d6a-83a2-3616eb7df6fd)

## Functionality
### `create_cat.py`
The script consists of several components and achieves the following:

1. **Reads metadata**: Extracts catalog metadata from a predefined Excel file format.
2. **Validates data**: Ensures required fields are present and valid.
3. **Uploads to CKAN**: Creates or updates datasets on the CKAN instance using API calls.
4. **Handles configuration**: Manages CKAN API keys and instance URLs for reuse.

### `write_cat.py`
1. **CKAN Interaction**: Retrieves catalog metadata via the CKAN API using the `CKANManager` class and handles API responses.
2. **Excel File Handling**: Uses the `ExcelHandler` class to write catalog details (title, description, tags, license, organization, groups, resources) into designated Excel columns.
3. **Configuration and Validation**: Saves CKAN API keys and instance URLs in `config_write.ini` for reuse and validates URLs.
4. **Resource Management**: Supports writing multiple resources (URL, name, description, format) across predefined placeholders.
5. **Error Handling**: Ensures robust handling of API or file operation errors with meaningful feedback.

## Code Structure
### `create_cat.py`
#### JSON Template

The JSON template is based on the `ckan_dataset.yaml` scheming. This template is used to construct the payload for creating datasets in CKAN. Any changes to the CKAN scheming require corresponding updates to this template.

#### CKANManager

Handles interactions with the CKAN instance, enabling API requests for dataset management.

#### ExcelHandler

Processes the Excel file (`SDDI-Metadata.xlsx`) and extracts relevant metadata.

#### MetadataManager

Validates metadata and constructs the data payload for CKAN.


#### ConfigManager

Stores the JSON template and manages configurations for CKAN instance access.


#### Helper Functions

Utility functions to assist the main components.


### `write_cat.py`

Uses as similar structure but without JSON template. 

## Config
All scripts use a `config.ini` file to store configuration parameters. The file will be created automatically on first run with default values.

### Configuration Sections
- **[CKAN]**: CKAN API configuration
  - `api_url`: CKAN instance URL (default: http://localhost:5000)
  - `api_key`: CKAN API key

- **[Monitoring]**: File monitoring configuration for `detect_outdated_files.py`
  - `allowed_extensions`: Comma-separated list of file extensions to monitor (default: .xlsx,.json,.csv)
  - `exclude_dirs`: Comma-separated list of directories to exclude (default: __pycache__,TEST,schema_templates,templates)
  
  **Extended Configuration Examples:**
  ```ini
  # For 3D modeling workflows:
  allowed_extensions = .obj,.fbx,.dae,.3ds,.blend,.stl,.ply,.gltf,.glb,.usd,.ifc,.step
  
  # For GIS and geospatial workflows:
  allowed_extensions = .shp,.kml,.kmz,.gpx,.geojson,.gml,.dwg,.dxf,.tif,.nc,.hdf5,.las,.laz
  
  # For comprehensive monitoring (all supported file types):
  allowed_extensions = *
  ```

1. **Configuration Files**:
   - `config_write.ini` (for `write_cat.py`) and `config.ini` (for `create_cat.py`).
   - Created automatically the first time the script runs.

2. **Setup**:
   - On first run, you will be prompted to enter the CKAN API key and instance URL (e.g., `http://192.168.92.1:5000`).
   - These details are saved in the configuration file for future runs.

3. **Editing Configuration**:
   - To update the API key or instance URL, open the `.ini` file in a text editor and modify the values.

## Usage

### `create_cat.py`

1. Place the `SDDI-Metadata.xlsx` file in the desired directory.
2. Install `openpyxl` library if is not installed on your system:
`pip install openpyxl`
3. Run the script:
`python create_cat.py`
4. provide the path to the Excel file when prompted: 
`.../path/to/SDDI-Metadata.xlsx`
5. Enter the [CKAN API key](https://docs.ckan.org/en/2.11/api/index.html) and instance URL when prompted. (The CKAN API key can be found in your CKAN instance in `user`page.) These will be saved for future use.
6. The script will process the metadata and interact with the CKAN API to create or update datasets.

** Please note that the Excel file **must be closed** when the script is run and that the name of the file **isn't allowed to be changed**.

### `write_cat.py`

1. Ensure the `SDDI-Metadata.xlsx` file exists in the specified directory.
2. Run the script and provide the Excel file path, CKAN catalog name, API key, and CKAN instance URL when prompted.
3. The script will fetch the catalog data from the CKAN instance and write it to the Excel file in a structured format.

### `detect_outdated_files.py`

1. Configure monitoring settings in `config.ini` (optional)
2. Run the script:
   ```bash
   python detect_outdated_files.py
   ```
3. The script will scan the specified directory, compare files with CKAN catalog, and report outdated files grouped by extension.


## Example
### `create_cat.py`
```bash
$ pip install openpyxl
python create_cat.py
Please enter the file path: /path/to/SDDI-Metadata.xlsx
Enter the API key: your-api-key
Enter the instance url (e.g. http://192.168.92.1:5000): http://192.168.92.1:5000
successfully created catalog Catalog1
```
### `write_cat.py`
```bash
$ python write_cat.py
Please enter the Excel file path: /path/to/SDDI-Metadata.xlsx
Enter the API key: your-api-key
Enter the instance url (e.g. http://192.168.92.1:5000): http://192.168.92.1:5000
Enter the CKAN catalog name (identifier): catalog-example
Successfully wrote catalog 'Example Catalog' to .xlsx file.

### `detect_outdated_files.py`
```bash
$ python detect_outdated_files.py
Scanning directory: d:\ckan-docker-CKANofficial\sddi-import-export-excel-tool

Outdated files by extension:
.xlsx:
  - test_data.xlsx (New file, not in CKAN)
.json:
  - updated_metadata.json (Modified 2023-11-15 14:30:00)

Tracking data updated in file_tracking.json

Error processing catalog Catalog2: Data for required fields is not provided: license is missing
