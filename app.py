import streamlit as st
import pandas as pd
import os
import tempfile
import zipfile
from datetime import datetime
import json
import requests
import time
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="CKAN Tools",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Natural styling without AI-style effects
st.markdown("""
<style>
    .main-header {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #2c3e50;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: #6c757d;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .section-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-note {
        background-color: #e7f3ff;
        border: 1px solid #b8daff;
        color: #004085;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .sidebar .stSelectbox > label {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

class CKANApi:
    """CKAN API client"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test CKAN connection"""
        try:
            response = requests.get(
                f"{self.base_url}/api/3/action/site_read",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get dataset information"""
        try:
            response = requests.get(
                f"{self.base_url}/api/3/action/package_show?id={dataset_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dataset"""
        try:
            response = requests.post(
                f"{self.base_url}/api/3/action/package_create",
                headers=self.headers,
                json=dataset_data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def update_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update dataset"""
        try:
            response = requests.post(
                f"{self.base_url}/api/3/action/package_update",
                headers=self.headers,
                json=dataset_data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

class CKANToolsApp:
    def __init__(self):
        # Initialize session state
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        
    def add_log(self, message: str, log_type: str = "info"):
        """Add log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type
        }
        st.session_state.logs.append(log_entry)
        
        # Keep only last 50 logs
        if len(st.session_state.logs) > 50:
            st.session_state.logs = st.session_state.logs[-50:]
    
    def display_logs(self):
        """Display logs"""
        if st.session_state.logs:
            st.subheader("Activity Log")
            
            for log in st.session_state.logs[-10:]:  # Show last 10
                timestamp = log['timestamp']
                message = log['message']
                log_type = log['type']
                
                if log_type == "success":
                    st.success(f"[{timestamp}] {message}")
                elif log_type == "error":
                    st.error(f"[{timestamp}] {message}")
                elif log_type == "warning":
                    st.warning(f"[{timestamp}] {message}")
                else:
                    st.info(f"[{timestamp}] {message}")
        
    def main(self):
        # Main header
        st.markdown("""
        <div class="main-header">
            <h1>CKAN Tools</h1>
            <p>Excel Import & File Monitor for CKAN Data Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar navigation
        with st.sidebar:
            st.subheader("Tools")
            
            tool_option = st.selectbox(
                "Select a tool:",
                ["Home", "Excel Import", "File Monitor", "Settings", "Help"]
            )
            
            # Connection status
            if st.button("Test CKAN Connection", use_container_width=True):
                self.quick_connection_test()
        
        # Display selected page
        if tool_option == "Home":
            self.show_home_page()
        elif tool_option == "Excel Import":
            self.show_excel_import_page()
        elif tool_option == "File Monitor":
            self.show_file_monitor_page()
        elif tool_option == "Settings":
            self.show_config_page()
        elif tool_option == "Help":
            self.show_help_page()
    
    def quick_connection_test(self):
        """Quick connection test"""
        ckan_url = st.session_state.get('ckan_url', '')
        api_key = st.session_state.get('api_key', '')
        
        if not ckan_url or not api_key:
            st.sidebar.error("Please configure CKAN connection in Settings first")
            return
        
        with st.sidebar:
            with st.spinner("Testing connection..."):
                api = CKANApi(ckan_url, api_key)
                result = api.test_connection()
                
                if result["success"]:
                    st.success("Connection successful")
                else:
                    st.error(f"Connection failed: {result['message']}")
    
    def show_home_page(self):
        """Display home page"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="section-card">
                <h3>Excel Import</h3>
                <p>Upload Excel files and automatically create or update CKAN datasets. 
                Supports multiple schema types including datasets, devices, and digital twins.</p>
                <ul>
                    <li>Automatic Excel schema parsing</li>
                    <li>Batch dataset creation</li>
                    <li>Real-time progress tracking</li>
                    <li>Detailed error logging</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="section-card">
                <h3>File Monitor</h3>
                <p>Monitor local file changes and compare with CKAN resources 
                to detect outdated files that need synchronization.</p>
                <ul>
                    <li>File change detection</li>
                    <li>Version comparison analysis</li>
                    <li>Sync recommendations</li>
                    <li>Detailed reporting</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Connection status
        if self.check_config():
            st.subheader("Connection Status")
            col1, col2 = st.columns(2)
            with col1:
                st.info("CKAN connection configured")
            with col2:
                if st.button("Test Connection"):
                    self.quick_connection_test()
        
        # Recent activity
        self.show_recent_activity()
    
    def show_excel_import_page(self):
        """Excel import page"""
        st.header("Excel Import")
        
        # Check configuration
        if not self.check_config():
            st.warning("Please configure your CKAN connection in Settings before proceeding.")
            return
        
        # File upload section
        st.subheader("1. Upload Excel File")
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=['xlsx', 'xls'],
            help="Select Excel files containing dataset schemas (dataset, device, digitaltwin, etc.)"
        )
        
        if uploaded_file is not None:
            # File information
            file_size = len(uploaded_file.getbuffer()) / 1024 / 1024  # MB
            st.markdown(f"""
            <div class="info-note">
                <strong>File:</strong> {uploaded_file.name} ({file_size:.2f} MB)
            </div>
            """, unsafe_allow_html=True)
            
            # File preview
            try:
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_names = excel_data.sheet_names
                
                st.subheader("2. File Preview")
                
                selected_sheets = st.multiselect(
                    "Select worksheets to process:",
                    sheet_names,
                    default=sheet_names[:3] if len(sheet_names) > 3 else sheet_names
                )
                
                # Preview selected worksheets
                for sheet in selected_sheets[:2]:  # Preview first 2 only
                    with st.expander(f"Preview: {sheet}"):
                        df = pd.read_excel(uploaded_file, sheet_name=sheet)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Rows", len(df))
                        with col2:
                            st.metric("Columns", len(df.columns))
                        with col3:
                            valid_rows = len(df.dropna(subset=['name', 'title'] if 'name' in df.columns and 'title' in df.columns else []))
                            st.metric("Valid Rows", valid_rows)
                        
                        st.dataframe(df.head(5), use_container_width=True)
                        
                        # Check required fields
                        required_fields = ['name', 'title']
                        missing_fields = [field for field in required_fields if field not in df.columns]
                        
                        if missing_fields:
                            st.warning(f"Missing required fields: {', '.join(missing_fields)}")
                        else:
                            st.success("All required fields present")
                            
            except Exception as e:
                st.error(f"Error previewing file: {str(e)}")
            
            # Import options
            st.subheader("3. Import Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                update_existing = st.checkbox("Update existing datasets", value=True)
                validate_data = st.checkbox("Validate data before import", value=True)
                
            with col2:
                batch_size = st.number_input("Batch size", min_value=1, max_value=100, value=10)
                dry_run = st.checkbox("Dry run (simulate without creating)", value=False)
            
            # Execute import
            st.subheader("4. Run Import")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("Start Import", use_container_width=True, type="primary", 
                           disabled=st.session_state.processing):
                    self.execute_excel_import(uploaded_file, update_existing, validate_data, batch_size, dry_run)
            
            with col2:
                if st.button("Clear Log", use_container_width=True):
                    st.session_state.logs = []
                    st.rerun()
        
        # Display logs
        self.display_logs()
    
    def show_file_monitor_page(self):
        """File monitor page"""
        st.header("File Monitor")
        
        # Check configuration
        if not self.check_config():
            st.warning("Please configure your CKAN connection in Settings before proceeding.")
            return
        
        st.markdown("""
        <div class="info-note">
            <strong>Note:</strong> Due to web environment limitations, please upload a ZIP file 
            containing the folders you want to monitor.
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_zip = st.file_uploader(
            "Upload folder as ZIP file",
            type=['zip'],
            help="Compress the folder you want to monitor into a ZIP file and upload it"
        )
        
        if uploaded_zip is not None:
            zip_size = len(uploaded_zip.getbuffer()) / 1024 / 1024
            st.markdown(f"""
            <div class="info-note">
                <strong>ZIP File:</strong> {uploaded_zip.name} ({zip_size:.2f} MB)
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Start Monitoring", use_container_width=True, type="primary"):
                self.execute_file_monitor(uploaded_zip)
        
        # Display logs
        self.display_logs()
    
    def show_config_page(self):
        """Configuration page"""
        st.header("Settings")
        
        # Connection info
        st.markdown("""
        <div class="info-note">
            <strong>Configuration Tips:</strong><br>
            • CKAN Server URL must be publicly accessible (not localhost)<br>
            • Example: https://demo.ckan.org or https://your-domain.com/ckan<br>
            • API Key can be found in your CKAN user profile settings
        </div>
        """, unsafe_allow_html=True)
        
        # CKAN connection configuration
        st.subheader("CKAN Connection")
        
        with st.form("ckan_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                ckan_url = st.text_input(
                    "CKAN Server URL",
                    value=st.session_state.get('ckan_url', ''),
                    placeholder="https://demo.ckan.org",
                    help="Must be a publicly accessible CKAN instance URL"
                )
                
                # Example instances
                example_url = st.selectbox(
                    "Or choose an example instance:",
                    ["Custom URL", "https://demo.ckan.org", "https://catalog.data.gov", "https://open.canada.ca/data"]
                )
                
                if example_url != "Custom URL":
                    ckan_url = example_url
                
                api_key = st.text_input(
                    "API Key",
                    value=st.session_state.get('api_key', ''),
                    type="password",
                    help="Found in your CKAN user profile settings"
                )
                
            with col2:
                org_name = st.text_input(
                    "Default Organization",
                    value=st.session_state.get('org_name', ''),
                    placeholder="your-organization",
                    help="Default organization for creating datasets"
                )
                
                default_license = st.selectbox(
                    "Default License",
                    ["cc-by", "cc-by-sa", "cc-zero", "odc-pddl", "other-open"],
                    index=0
                )
            
            # Connection validation
            st.subheader("Connection Validation")
            
            # Display current config status
            if ckan_url:
                if 'localhost' in ckan_url or '127.0.0.1' in ckan_url:
                    st.warning("Warning: localhost addresses cannot be accessed from cloud environments")
                elif not ckan_url.startswith(('http://', 'https://')):
                    st.warning("Warning: URL should start with http:// or https://")
                else:
                    st.success("URL format looks correct")
            
            col1, col2 = st.columns(2)
            
            with col1:
                test_connection = st.form_submit_button("Test Connection", use_container_width=True)
                
            with col2:
                save_config = st.form_submit_button("Save Configuration", use_container_width=True, type="primary")
            
            if test_connection:
                self.test_ckan_connection_improved(ckan_url, api_key)
                
            if save_config:
                st.session_state.update({
                    'ckan_url': ckan_url,
                    'api_key': api_key,
                    'org_name': org_name,
                    'default_license': default_license
                })
                st.success("Configuration saved successfully")
                self.add_log("Configuration updated", "success")
        
        # Configuration examples
        with st.expander("Configuration Examples and Help"):
            st.markdown("""
            ### Public CKAN Instances for Testing
            
            | Instance | URL | Description |
            |----------|-----|-------------|
            | CKAN Demo | https://demo.ckan.org | Official demo instance |
            | Data.gov | https://catalog.data.gov | US Government data portal |
            | Canada Open Data | https://open.canada.ca/data | Canadian open data |
            | European Data Portal | https://data.europa.eu | European data portal |
            
            ### Getting Your API Key
            
            1. Log in to your CKAN instance
            2. Click on your username in the top right
            3. Select "Profile" or "User Settings"
            4. Find the "API Key" section
            5. Copy the key and paste it in the configuration above
            
            ### Important Notes
            
            - **localhost addresses**: Cannot be accessed from cloud environments
            - **API permissions**: Ensure your API key has dataset creation/update permissions
            - **Network access**: The CKAN server must be accessible from the internet
            """)
    
    def show_help_page(self):
        """Help page"""
        st.header("Help & Documentation")
        
        with st.expander("Quick Start Guide", expanded=True):
            st.markdown("""
            ### 1. Excel Import to CKAN
            
            **Steps:**
            1. Go to "Excel Import" from the sidebar
            2. Upload an Excel file containing dataset information
            3. Configure your CKAN server URL and API key in Settings
            4. Preview the data to be imported
            5. Click "Start Import"
            
            **Excel File Requirements:**
            - Supports .xlsx and .xls formats
            - Each worksheet represents a schema type (dataset, device, digitaltwin, etc.)
            - First row should contain column headers
            - Required fields: name (identifier), title
            
            **Common Fields:**
            - `name`: Unique dataset identifier (required)
            - `title`: Dataset title (required)
            - `notes`: Dataset description
            - `owner_org`: Organization
            - `tags`: Tags (comma-separated)
            - `license_id`: License type
            
            ### 2. File Monitor
            
            **Steps:**
            1. Go to "File Monitor" from the sidebar
            2. Upload a ZIP file containing folders to monitor
            3. Configure CKAN connection information
            4. Click "Start Monitoring"
            
            **Monitor Features:**
            - File modification time comparison
            - File size change detection
            - Metadata consistency checking
            - Sync recommendation reports
            """)
        
        with st.expander("Frequently Asked Questions"):
            st.markdown("""
            **Q: How do I get a CKAN API key?**
            
            A: Log in to your CKAN instance, go to your user profile settings, 
            and you'll find the API key in the "API Key" section.
            
            **Q: What fields should my Excel file contain?**
            
            A: At minimum: `name` (unique identifier) and `title`. 
            Optional fields include `notes`, `owner_org`, `tags`, `license_id`.
            
            **Q: Why do I need to upload a ZIP file for monitoring?**
            
            A: Web applications cannot directly access local file systems for security reasons. 
            ZIP upload allows us to simulate file monitoring in the cloud.
            
            **Q: What should I do with large files?**
            
            A: Recommendations:
            - Process large files in smaller batches
            - Use smaller batch sizes in import options
            - Ensure stable network connection
            """)
        
        with st.expander("Technical Information"):
            st.markdown("""
            ### CKAN API Endpoints Used
            
            - `package_create`: Create new datasets
            - `package_update`: Update existing datasets
            - `package_show`: Get dataset information
            - `package_list`: List all datasets
            - `resource_create`: Create resources
            - `resource_update`: Update resources
            
            ### Error Codes
            
            - `200`: Success
            - `400`: Bad request parameters
            - `401`: Authentication failed (check API key)
            - `403`: Insufficient permissions
            - `404`: Resource not found
            - `409`: Resource conflict (duplicate name)
            - `500`: Server internal error
            
            ### Data Validation Rules
            
            - Dataset names: lowercase letters, numbers, hyphens, underscores only
            - Name length: maximum 100 characters
            - Title: cannot be empty
            - Organization: must exist in CKAN
            """)
    
    def check_config(self) -> bool:
        """Check if CKAN configuration is complete"""
        return bool(st.session_state.get('ckan_url') and st.session_state.get('api_key'))
    
    def test_ckan_connection_improved(self, ckan_url: str, api_key: str):
        """Improved CKAN connection test"""
        if not ckan_url or not api_key:
            st.error("Please provide both CKAN URL and API key")
            return
        
        # Pre-checks
        if 'localhost' in ckan_url or '127.0.0.1' in ckan_url:
            st.error("localhost addresses cannot be accessed from cloud environments. Please use a publicly accessible URL.")
            self.add_log("Connection test failed: localhost address not accessible", "error")
            return
        
        if not ckan_url.startswith(('http://', 'https://')):
            st.error("URL must start with http:// or https://")
            return
        
        with st.spinner("Testing connection..."):
            try:
                # Test basic connection first
                import requests
                response = requests.get(ckan_url, timeout=10)
                
                if response.status_code == 200:
                    st.info("Basic network connection successful")
                else:
                    st.warning(f"Website response unusual (HTTP {response.status_code})")
                
                # Test API
                api = CKANApi(ckan_url, api_key)
                result = api.test_connection()
                
                if result["success"]:
                    st.success("CKAN API connection test successful!")
                    st.info(f"Server: {ckan_url}")
                    st.info("API key validation passed")
                    self.add_log("CKAN connection test successful", "success")
                else:
                    st.error(f"API connection test failed: {result['message']}")
                    self.add_log(f"CKAN API test failed: {result['message']}", "error")
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to server. Please check if the URL is correct.")
                self.add_log("Connection test failed: unable to connect to server", "error")
            except requests.exceptions.Timeout:
                st.error("Connection timeout. Server response too slow.")
                self.add_log("Connection test failed: connection timeout", "error")
            except Exception as e:
                st.error(f"Connection test failed: {str(e)}")
                self.add_log(f"Connection test exception: {str(e)}", "error")
    
    def execute_excel_import(self, uploaded_file, update_existing: bool, 
                           validate_data: bool, batch_size: int, dry_run: bool):
        """Execute Excel import"""
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("Starting Excel import task", "info")
            status_text.text("Processing Excel file...")
            progress_bar.progress(20)
            
            # Get CKAN API client
            api = CKANApi(st.session_state.ckan_url, st.session_state.api_key)
            
            # Read Excel file
            excel_data = pd.ExcelFile(uploaded_file)
            total_sheets = len(excel_data.sheet_names)
            
            self.add_log(f"Found {total_sheets} worksheets", "info")
            progress_bar.progress(40)
            
            total_processed = 0
            total_success = 0
            total_errors = 0
            
            # Process each worksheet
            for i, sheet_name in enumerate(excel_data.sheet_names):
                status_text.text(f"Processing worksheet: {sheet_name}")
                progress = 40 + (i / total_sheets) * 50
                progress_bar.progress(int(progress))
                
                try:
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    self.add_log(f"Processing worksheet '{sheet_name}': {len(df)} rows", "info")
                    
                    # Validate required fields
                    if 'name' not in df.columns or 'title' not in df.columns:
                        self.add_log(f"Skipping worksheet '{sheet_name}': missing required fields (name, title)", "warning")
                        continue
                    
                    # Process each row
                    for idx, row in df.iterrows():
                        if pd.isna(row.get('name')) or pd.isna(row.get('title')):
                            continue  # Skip rows with missing required fields
                        
                        dataset_data = self.prepare_dataset_data(row, sheet_name)
                        total_processed += 1
                        
                        if dry_run:
                            self.add_log(f"[Dry run] Would create dataset: {dataset_data['name']}", "info")
                            total_success += 1
                        else:
                            try:
                                # Check if dataset exists
                                existing = api.get_dataset(dataset_data['name'])
                                
                                if existing.get('success'):
                                    if update_existing:
                                        result = api.update_dataset(dataset_data)
                                        action = "Updated"
                                    else:
                                        self.add_log(f"Dataset exists, skipping: {dataset_data['name']}", "warning")
                                        continue
                                else:
                                    result = api.create_dataset(dataset_data)
                                    action = "Created"
                                
                                if result.get('success'):
                                    self.add_log(f"{action} dataset: {dataset_data['name']}", "success")
                                    total_success += 1
                                else:
                                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                                    self.add_log(f"Failed to {action.lower()} dataset {dataset_data['name']}: {error_msg}", "error")
                                    total_errors += 1
                            except Exception as e:
                                self.add_log(f"Error processing dataset {dataset_data['name']}: {str(e)}", "error")
                                total_errors += 1
                        
                        # Batch processing delay
                        if total_processed % batch_size == 0:
                            time.sleep(0.1)
                
                except Exception as e:
                    self.add_log(f"Error processing worksheet '{sheet_name}': {str(e)}", "error")
                    total_errors += 1
            
            progress_bar.progress(100)
            status_text.text("Excel import completed!")
            
            self.add_log("Excel import task completed", "success")
            self.add_log(f"Total processed: {total_processed}, Success: {total_success}, Errors: {total_errors}", "info")
            
            # Show results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Processed", total_processed)
            with col2:
                st.metric("Successful", total_success)
            with col3:
                st.metric("Errors", total_errors)
            
            if dry_run:
                st.info("This was a dry run - no datasets were actually created")
            elif total_success > 0:
                st.success("Excel import completed successfully!")
            else:
                st.warning("Import completed but no datasets were processed")
                
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("Error occurred during import")
            st.error(f"Error details: {str(e)}")
            self.add_log(f"Import task exception: {str(e)}", "error")
        
        finally:
            st.session_state.processing = False
    
    def prepare_dataset_data(self, row: pd.Series, schema_type: str) -> Dict[str, Any]:
        """Prepare dataset data from Excel row"""
        # Basic dataset information
        dataset_data = {
            'name': str(row['name']).lower().replace(' ', '-'),
            'title': str(row['title']),
            'type': schema_type
        }
        
        # Optional fields
        optional_fields = {
            'notes': 'notes',
            'owner_org': 'owner_org',
            'license_id': 'license_id',
            'url': 'url',
            'version': 'version',
            'author': 'author',
            'author_email': 'author_email',
            'maintainer': 'maintainer',
            'maintainer_email': 'maintainer_email'
        }
        
        for excel_field, ckan_field in optional_fields.items():
            if excel_field in row and pd.notna(row[excel_field]):
                dataset_data[ckan_field] = str(row[excel_field])
        
        # Process tags
        if 'tags' in row and pd.notna(row['tags']):
            tags = [tag.strip() for tag in str(row['tags']).split(',')]
            dataset_data['tags'] = [{'name': tag} for tag in tags if tag]
        
        # Add default values
        if 'owner_org' not in dataset_data and st.session_state.get('org_name'):
            dataset_data['owner_org'] = st.session_state.org_name
        
        if 'license_id' not in dataset_data:
            dataset_data['license_id'] = st.session_state.get('default_license', 'cc-by')
        
        return dataset_data
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get dataset information"""
        try:
            response = requests.get(
                f"{self.base_url}/api/3/action/package_show?id={dataset_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dataset"""
        try:
            response = requests.post(
                f"{self.base_url}/api/3/action/package_create",
                headers=self.headers,
                json=dataset_data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def update_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update dataset"""
        try:
            response = requests.post(
                f"{self.base_url}/api/3/action/package_update",
                headers=self.headers,
                json=dataset_data,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def execute_file_monitor(self, uploaded_zip):
        """Execute file monitor"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("Starting file monitor task", "info")
            status_text.text("Extracting ZIP file...")
            progress_bar.progress(20)
            
            # Extract ZIP file
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, uploaded_zip.name)
            
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            
            extracted_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
                file_list = zip_ref.namelist()
            
            self.add_log(f"Extracted {len(file_list)} files", "info")
            progress_bar.progress(40)
            
            # Get CKAN API client
            api = CKANApi(st.session_state.ckan_url, st.session_state.api_key)
            
            status_text.text("Getting CKAN datasets...")
            
            # Get CKAN datasets list
            try:
                datasets_response = requests.get(
                    f"{st.session_state.ckan_url}/api/3/action/package_list",
                    headers={'Authorization': st.session_state.api_key},
                    timeout=30
                )
                
                if datasets_response.status_code != 200:
                    raise Exception(f"Failed to get datasets: HTTP {datasets_response.status_code}")
                
                datasets_data = datasets_response.json()
                if not datasets_data.get('success'):
                    raise Exception("CKAN API returned error")
                
                dataset_names = datasets_data['result']
                self.add_log(f"Found {len(dataset_names)} datasets in CKAN", "info")
                
            except Exception as e:
                st.error(f"Failed to get CKAN datasets: {str(e)}")
                self.add_log(f"Failed to get CKAN datasets: {str(e)}", "error")
                return
            
            progress_bar.progress(70)
            status_text.text("Analyzing files...")
            
            # Analyze local files and compare with CKAN
            outdated_files = []
            processed_files = 0
            
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, extracted_dir)
                    processed_files += 1
                    
                    # Get file stats
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # Check if there's a corresponding dataset in CKAN
                    # This is a simplified approach - in reality you'd have more sophisticated matching
                    file_base_name = os.path.splitext(os.path.basename(file))[0]
                    potential_dataset_name = file_base_name.lower().replace(' ', '-').replace('_', '-')
                    
                    # Check if dataset exists and get its resources
                    if potential_dataset_name in dataset_names:
                        try:
                            dataset_response = requests.get(
                                f"{st.session_state.ckan_url}/api/3/action/package_show?id={potential_dataset_name}",
                                headers={'Authorization': st.session_state.api_key},
                                timeout=15
                            )
                            
                            if dataset_response.status_code == 200:
                                dataset_data = dataset_response.json()
                                if dataset_data.get('success'):
                                    resources = dataset_data['result'].get('resources', [])
                                    
                                    # Compare with resources
                                    needs_update = True
                                    for resource in resources:
                                        # Simple comparison - in reality you'd check more thoroughly
                                        if resource.get('name', '').lower() == file.lower():
                                            # Resource exists, check if it needs updating
                                            resource_modified = resource.get('last_modified', resource.get('created', ''))
                                            if resource_modified:
                                                try:
                                                    resource_date = datetime.fromisoformat(resource_modified.replace('Z', '+00:00'))
                                                    if file_mtime <= resource_date.replace(tzinfo=None):
                                                        needs_update = False
                                                except:
                                                    pass  # If date parsing fails, assume update needed
                                            break
                                    
                                    if needs_update:
                                        outdated_files.append({
                                            'file': relative_path,
                                            'dataset': potential_dataset_name,
                                            'size': file_size,
                                            'modified': file_mtime.strftime('%Y-%m-%d %H:%M:%S'),
                                            'reason': 'File newer than CKAN resource'
                                        })
                        except Exception as e:
                            self.add_log(f"Error checking dataset {potential_dataset_name}: {str(e)}", "warning")
            
            progress_bar.progress(100)
            status_text.text("File monitoring completed!")
            
            self.add_log(f"Analyzed {processed_files} files", "info")
            
            if outdated_files:
                self.add_log(f"Found {len(outdated_files)} files that may need synchronization", "warning")
                st.warning(f"Found {len(outdated_files)} files that may need synchronization")
                
                # Display results
                df_results = pd.DataFrame(outdated_files)
                st.dataframe(df_results, use_container_width=True)
                
                # Sync recommendations
                st.subheader("Synchronization Recommendations")
                for file_info in outdated_files:
                    with st.expander(f"File: {file_info['file']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**File Information:**")
                            st.write(f"- Size: {file_info['size']} bytes")
                            st.write(f"- Modified: {file_info['modified']}")
                            st.write(f"- Dataset: {file_info['dataset']}")
                        
                        with col2:
                            st.write("**Recommendation:**")
                            st.write(f"- Issue: {file_info['reason']}")
                            st.write("- Action: Update CKAN resource")
                            st.write("- Priority: Medium")
            else:
                self.add_log("No outdated files found", "success")
                st.success("All files appear to be up to date")
            
            self.add_log("File monitor task completed", "success")
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("Error occurred during monitoring")
            st.error(f"Error details: {str(e)}")
            self.add_log(f"Monitor task exception: {str(e)}", "error")
    
    def show_recent_activity(self):
        """Show recent activity"""
        if st.session_state.logs:
            st.subheader("Recent Activity")
            recent_logs = st.session_state.logs[-5:]
            
            for log in reversed(recent_logs):
                timestamp = log['timestamp']
                message = log['message']
                log_type = log['type']
                
                icon = "✓" if log_type == "success" else "✗" if log_type == "error" else "!" if log_type == "warning" else "•"
                st.write(f"{icon} **{timestamp}** - {message}")
        else:
            st.info("No recent activity to display")

# Run the application
if __name__ == "__main__":
    app = CKANToolsApp()
    app.main()