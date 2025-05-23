# CKAN Catalog Creation Automation

## Table of Contents

- [Overview](#overview)
- [Functionality](#functionality)
- [Code Structure](#code-structure)
  - [`create_cat.py`](#`create_cat.py`)
  - [`write_cat.py`](#`write_cat.py`)
- [Config](#config)
- [Usage](#usage)
- [Example](#example)

## Overview
This repository contains scripts implementation for managing metadata of the catalog entries between an Excel file and a CKAN instance. The main purpose is to automate the process of catalog creation / data retrieval. It includes configuration handling, API communication, Excel manipulation, and data validation. It contains two scripts, `create_cat.py` and `write_cat.py`. 

`create_cat.py` automates the process of reading catalog metadata from an Excel file (`SDDI-Metadata.xlsx`), processing it, and uploading it to a CKAN instance via API calls. The script is designed to streamline the integration of metadata into a CKAN server by following a structured workflow.

The `write_cat.py` script automates the process of retrieving, processing, and inserting catalog data into the `SDDI-Metadata.xlsx` Excel file.

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
Both scripts use configuration files to store the CKAN API key and instance URL for easier reuse:

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


Error processing catalog Catalog2: Data for required fields is not provided: license is missing
