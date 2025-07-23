import requests
import time

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJoSXBxOUVGSU5qa0wtYjUzaFdyS0NtY1p6RTRpYVM4ZFF2MVpsTXZ0S2NJIiwiaWF0IjoxNzUzMDI0MzAzfQ.jJA2BYnhY-E5lVCJwU5INZtAEd2ehkK85loj9DSToOs"
base_url = "https://localhost:8443/api/3/action"
headers = {"Authorization": api_key}

def delete_all_datasets():
    try:
        # Get all datasets including private ones
        search_url = f"{base_url}/package_search"
        search_data = {"rows": 1000, "include_private": True}  # Get up to 1000 datasets
        response = requests.post(search_url, headers=headers, json=search_data, verify=False)
        datasets = response.json()['result']['results']
        
        print(f"Found {len(datasets)} datasets to delete")
        
        for dataset in datasets:
            dataset_id = dataset['id']
            dataset_name = dataset['name']
            try:
                # First delete the dataset
                delete_url = f"{base_url}/package_delete"
                delete_data = {"id": dataset_id}
                delete_response = requests.post(delete_url, headers=headers, json=delete_data, verify=False)
                
                # Wait briefly
                time.sleep(1)
                
                # Then purge it completely
                purge_url = f"{base_url}/dataset_purge"
                purge_data = {"id": dataset_id}
                purge_response = requests.post(purge_url, headers=headers, json=purge_data, verify=False)
                
                if delete_response.json().get('success'):
                    print(f"Successfully deleted dataset: {dataset_name}")
                    if purge_response.json().get('success'):
                        print(f"Successfully purged dataset: {dataset_name}")
                    else:
                        print(f"Failed to purge dataset: {dataset_name}")
                else:
                    print(f"Failed to delete dataset: {dataset_name}")
                    
            except Exception as e:
                print(f"Error processing dataset {dataset_name}: {str(e)}")
                
        print("\nDeletion process completed!")
        
    except Exception as e:
        print(f"Error listing datasets: {str(e)}")

if __name__ == "__main__":
    delete_all_datasets()