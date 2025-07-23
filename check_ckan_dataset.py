import requests

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJoSXBxOUVGSU5qa0wtYjUzaFdyS0NtY1p6RTRpYVM4ZFF2MVpsTXZ0S2NJIiwiaWF0IjoxNzUzMDI0MzAzfQ.jJA2BYnhY-E5lVCJwU5INZtAEd2ehkK85loj9DSToOs"
url = "https://localhost:8443/api/3/action/package_show"

headers = {"Authorization": api_key}

# Check Example Dataset 2 specifically
dataset_id = "exampledataset2"

try:
    data = {"id": dataset_id}
    response = requests.get(url, headers=headers, json=data, verify=False)
    result = response.json()
    
    if result.get('success'):
        dataset = result['result']
        print(f"\n{dataset_id}:")
        print(f"  Title: {dataset.get('title', 'N/A')}")
        print(f"  role: {dataset.get('maintainer', 'N/A')}")
        print(f"  Private: {dataset.get('private', 'N/A')}")
        print(f"  State: {dataset.get('state', 'N/A')}")
        print(f"  Owner Org: {dataset.get('owner_org', 'N/A')}")
        print(f"  Created: {dataset.get('metadata_created', 'N/A')}")
    else:
        print(f"\n{dataset_id}: Not found or error")
        print(f"Response: {result}")
        
except Exception as e:
    print(f"\n{dataset_id}: Error - {e}") 