import requests
import urllib3
from typing import Optional, Dict, Any, List

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CKANManager:
    """
    Unified CKAN API manager for interacting with CKAN instances.
    Combines functionality for dataset creation, searching, and resource management.
    """
    
    def __init__(self, api_url: str, api_key: str, debug: bool = False):
        """
        Initialize CKAN manager.
        
        Args:
            api_url: CKAN API base URL
            api_key: CKAN API key for authentication
            debug: Enable debug logging
        """
        self.api_url = api_url
        self.api_key = api_key
        self.debug = debug
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        self.connection_available = self.test_connection()
        
        if self.debug:
            print(f"🔍 CKAN Manager initialized - Connection: {self.connection_available}")
    
    def test_connection(self) -> bool:
        """
        Test if CKAN is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/3/action/status_show", 
                timeout=10, 
                verify=False
            )
            if self.debug:
                print(f"🔍 Connection test - Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            if self.debug:
                print(f"❌ Connection test failed: {e}")
            return False
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and return JSON data.
        
        Args:
            response: HTTP response object
            
        Returns:
            JSON response data
            
        Raises:
            Exception: If API request failed
        """
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform GET request to CKAN API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            Exception: If request fails
        """
        if self.debug:
            print(f"🔍 GET request: {endpoint}")
            print(f"   Params: {params}")
            print(f"   Connection: {self.connection_available}")
        
        if not self.connection_available:
            if self.debug:
                print("❌ Connection unavailable, skipping request")
            raise Exception("CKAN service unavailable")
        
        url = f"{self.api_url}{endpoint}"
        if self.debug:
            print(f"   Full URL: {url}")
        
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=self.headers, 
                verify=False, 
                timeout=10
            )
            
            if self.debug:
                print(f"   Response status: {response.status_code}")
            
            result = self._handle_response(response)
            
            if self.debug:
                print(f"   API success: {result.get('success', 'unknown')}")
            
            return result
                
        except requests.exceptions.ConnectionError as e:
            error_msg = "Cannot connect to CKAN server"
            if self.debug:
                print(f"   ❌ {error_msg}: {e}")
            self.connection_available = False
            raise Exception(error_msg)
        except requests.exceptions.Timeout as e:
            error_msg = "Request timeout"
            if self.debug:
                print(f"   ❌ {error_msg}: {e}")
            raise Exception(error_msg)
        except Exception as e:
            if self.debug:
                print(f"   ❌ Other error: {e}")
            raise e
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform POST request to CKAN API.
        
        Args:
            endpoint: API endpoint path
            data: JSON data to send
            
        Returns:
            JSON response data
            
        Raises:
            Exception: If request fails
        """
        if self.debug:
            print(f"🔍 POST request: {endpoint}")
            print(f"   Data: {data}")
        
        if not self.connection_available:
            if self.debug:
                print("❌ Connection unavailable, skipping request")
            raise Exception("CKAN service unavailable")
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = requests.post(
                url, 
                json=data, 
                headers=self.headers, 
                verify=False, 
                timeout=30
            )
            
            if self.debug:
                print(f"   Response status: {response.status_code}")
            
            return self._handle_response(response)
            
        except Exception as e:
            if self.debug:
                print(f"   ❌ POST error: {e}")
            raise e
    
    def search_datasets(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for datasets using package_search API.
        
        Args:
            query: Search query string
            
        Returns:
            Search results or None if failed
        """
        try:
            endpoint = "/api/3/action/package_search"
            params = {'q': query, 'rows': 100}
            
            if self.debug:
                print(f"🔍 Search datasets: '{query}'")
            
            result = self.get(endpoint, params)
            
            # Add detailed search result debugging
            if result and result.get('success') and self.debug:
                search_result = result['result']
                count = search_result.get('count', 0)
                results = search_result.get('results', [])
                
                print(f"   📊 Found {count} datasets")
                
                if count > 0:
                    print(f"   📋 Dataset list:")
                    for dataset in results:
                        name = dataset.get('name', 'N/A')
                        title = dataset.get('title', 'N/A')
                        print(f"      - {name} ({title})")
                else:
                    print(f"   ❌ Search results empty")
            
            return result
        except Exception as e:
            if self.debug:
                print(f"❌ Dataset search error: {e}")
            return None
    
    def get_dataset_by_id(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get dataset by exact ID.
        
        Args:
            dataset_id: Dataset ID to retrieve
            
        Returns:
            Dataset data or None if failed
        """
        try:
            endpoint = "/api/3/action/package_show"
            params = {'id': dataset_id}
            
            if self.debug:
                print(f"🔍 Get dataset: '{dataset_id}'")
            
            return self.get(endpoint, params)
        except Exception as e:
            if self.debug:
                print(f"❌ Get dataset error: {e}")
            return None
    
    def create_dataset(self, dataset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new dataset.
        
        Args:
            dataset_data: Dataset metadata
            
        Returns:
            Created dataset data or None if failed
        """
        try:
            endpoint = "/api/3/action/package_create"
            
            if self.debug:
                print(f"🔍 Create dataset: {dataset_data.get('name', 'N/A')}")
            
            return self.post(endpoint, dataset_data)
        except Exception as e:
            if self.debug:
                print(f"❌ Create dataset error: {e}")
            return None
    
    def update_dataset(self, dataset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing dataset.
        
        Args:
            dataset_data: Updated dataset metadata
            
        Returns:
            Updated dataset data or None if failed
        """
        try:
            endpoint = "/api/3/action/package_update"
            
            if self.debug:
                print(f"🔍 Update dataset: {dataset_data.get('name', 'N/A')}")
            
            return self.post(endpoint, dataset_data)
        except Exception as e:
            if self.debug:
                print(f"❌ Update dataset error: {e}")
            return None
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Delete a dataset.
        
        Args:
            dataset_id: Dataset ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = "/api/3/action/package_delete"
            data = {'id': dataset_id}
            
            if self.debug:
                print(f"🔍 Delete dataset: {dataset_id}")
            
            result = self.post(endpoint, data)
            return result.get('success', False)
        except Exception as e:
            if self.debug:
                print(f"❌ Delete dataset error: {e}")
            return False
    
    def create_resource(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new resource.
        
        Args:
            resource_data: Resource metadata and file data
            
        Returns:
            Created resource data or None if failed
        """
        try:
            endpoint = "/api/3/action/resource_create"
            
            if self.debug:
                print(f"🔍 Create resource: {resource_data.get('name', 'N/A')}")
            
            return self.post(endpoint, resource_data)
        except Exception as e:
            if self.debug:
                print(f"❌ Create resource error: {e}")
            return None
    
    def update_resource(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing resource.
        
        Args:
            resource_data: Updated resource metadata
            
        Returns:
            Updated resource data or None if failed
        """
        try:
            endpoint = "/api/3/action/resource_update"
            
            if self.debug:
                print(f"🔍 Update resource: {resource_data.get('name', 'N/A')}")
            
            return self.post(endpoint, resource_data)
        except Exception as e:
            if self.debug:
                print(f"❌ Update resource error: {e}")
            return None
    
    def delete_resource(self, resource_id: str) -> bool:
        """
        Delete a resource.
        
        Args:
            resource_id: Resource ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = "/api/3/action/resource_delete"
            data = {'id': resource_id}
            
            if self.debug:
                print(f"🔍 Delete resource: {resource_id}")
            
            result = self.post(endpoint, data)
            return result.get('success', False)
        except Exception as e:
            if self.debug:
                print(f"❌ Delete resource error: {e}")
            return False
    
    def get_all_datasets(self) -> Optional[List[str]]:
        """
        Get list of all dataset IDs.
        
        Returns:
            List of dataset IDs or None if failed
        """
        try:
            endpoint = "/api/3/action/package_list"
            
            if self.debug:
                print(f"🔍 Get all datasets")
            
            result = self.get(endpoint)
            if result and result.get('success'):
                return result['result']
            return None
        except Exception as e:
            if self.debug:
                print(f"❌ Get all datasets error: {e}")
            return None
    
    def search_resources(self, query):
        """
        Search for resources using the resource_search API
        """
        try:
            endpoint = "/api/3/action/resource_search"
            # Use POST request as required by the API
            data = {'query': query}
            return self.post(endpoint, data=data)
        except Exception as e:
            if self.debug:
                print(f"❌ Resource search error: {e}")
            return None