import requests
import json
import openpyxl
import os
import configparser
import re
from datetime import datetime
class CKANManager:
    
    '''Interacts with the CKAN instance'''
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }

    def post(self, endpoint, data=None):
        url = f"{self.api_url}{endpoint}"
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)

    def get(self, endpoint, params=None):
        url = f"{self.api_url}{endpoint}"
        response = requests.get(url, params=params, headers=self.headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

class ExcelHandler:
    '''Handles interaction with the Excel file'''
    def __init__(self, path):
        self.path = path
        try:
            self.wb = openpyxl.load_workbook(self.path)
        except Exception as e:
            print(f"Error: {str(e)}")
            return
        
        self.ws = self.wb.worksheets[0]
        self.update_organisations()
        self.update_categories_and_topics()
        self.update_licenses()

    def find_start_row(self, target, ws_index=0):
        for i, row in enumerate(self.wb.worksheets[ws_index].iter_rows(values_only=True), start=1):
            if row[1] == target or row[12] == target:
                return i
        return None

    def extract_data(self, start_row):
        if start_row is None:
            print("Start row not found.")
            return []

        data = []
        for row in self.ws.iter_rows(min_row=start_row, values_only=True):
            if all(cell is None for cell in row):
                break
            data.append(row)
        return data

    def update_organisations(self):
        response = ckan_manager.post('/api/3/action/organization_list?all_fields=True')
        if response['success']:
            start_row = 5
            start_col = 13

            metadata_manager.organisations = response['result']
            for i, org in enumerate(response['result']):
                self.wb.worksheets[1].cell(row=start_row + i, column=start_col).value = org['title']

            self.wb.save(self.path)

    def update_categories_and_topics(self):
        # response = ckan_manager.post('/api/3/action/group_list?all_fields=True')
        # if response['success']:
            # # hard coded structure of the SDDI-Metadata.xlsx options of the second worksheet
            # start_row = 5
            # topics_col = 5
            # categories_col = 3  

            # groups = response['result']
            # metadata_manager.categories = []
            # metadata_manager.topics = []

            # found_hauptkategorien = False

            # # TODO: check if this actually works, seems not possible to distinguish between themen und hauptkategorien based on the group string provided by instance
            # for group in groups:
            #     title = group['title']
            #     if title == 'Hauptkategorien': 
            #         found_hauptkategorien = True
            #         continue

            #     if not found_hauptkategorien:
            #         metadata_manager.topics.append(title)  # add to topics
            #     else:
            #         metadata_manager.categories.append(title)  # add to main categories

            # write all groups in the topic column for now until we can disting.
            start_row = 5
            topics_col = 5
            for i, topic in enumerate(metadata_manager.groups):
                self.wb.worksheets[1].cell(row=start_row + i, column=topics_col).value = topic['title']

            # for i, category in enumerate(metadata_manager.categories):
            #     self.wb.worksheets[1].cell(row=start_row + i, column=categories_col).value = category

            self.wb.save(self.path)

    def update_licenses(self):
        response = ckan_manager.post('/api/3/action/license_list')
        if response['success']:
            start_row = 5
            start_col = 7 

            metadata_manager.licenses = {lic['title']: lic['id'] for lic in response['result']}
            for i, lic in enumerate(response['result']):
                self.wb.worksheets[1].cell(row=start_row + i, column=start_col).value = lic['title']

            self.wb.save(self.path)

class MetadataManager:
    '''Stores metadata and performs mapping'''
    def __init__(self, template_file):
        with open(template_file, 'r') as f:
            self.template = json.load(f)

        self.categories = []
        self.topics = []
        self.access_rights = {
            'Öffentlich': 'public', 
            'Registrierte Benutzer': 'registered', 
            'Mitglieder der selben Organisation': 'same_organization', 
            'Nur ausgewählte Benutzer': 'only_allowed_users'
        }
        self.organisations = {}
        self.groups = ckan_manager.post('/api/3/action/group_list?all_fields=True')['result']
        self.licenses = {lic['title']: lic['id'] for lic in ckan_manager.post('/api/3/action/license_list')['result']}

    def validate_and_construct_package(self, row):
            package_data = self.template

            package_data['title'] = row[1]  # title
            package_data['notes'] = row[2]  # description
            package_data['tags'] = convert_string_to_tags(row[4])  # convert tags from semicolon-separated string to list

            # map license title to ID from CKAN
            if row[5] in self.licenses:
                package_data['license_id'] = self.licenses[row[5]]
            else:
                package_data['license_id'] = 'notspecified'  # fallback if license not found

            package_data['author'] = json.dumps([{
                                    "author": row[6],
                                    "author_email": row[7]
                                    }], ensure_ascii=False)
            package_data['maintainer'] = json.dumps([{
                        "Maintainer Email": row[9],
                        "maintainer": row[8],
                        "phone": row[10]
                        }], ensure_ascii=False)

            # organization mapping
            org_check, org_index = string_in_dicts(row[11], self.organisations)
            if org_check:
                package_data['owner_org'] = self.organisations[org_index]['name']
            else:
                raise Exception('Organization not specified or provided in wrong format')

            # map categories and topics (from groups)
            package_data['groups'] = []
            for group_name in [row[12], row[13], row[14], row[15]]:
                for group in self.groups:
                    if group_name == group['title']:
                        package_data['groups'].append({'id': group['id']})
                        break

            language_mapping = {'Deutsch': 'de', 'Englisch': 'en'}
            package_data['language'] = language_mapping.get(row[16], 'notspecified')

            package_data['version'] = row[17]

            # date fields
            # expected input provided by excel is dd/mm/yyyy
            # expected input by instance e.g 2024-11-13 but as a string!
            # if row[18] is not None:
            #     begin_date = row[18].strftime("%Y-%m-%d")
            #     package_data['begin_collection_date'] = begin_date
            
            # if row[19] is not None:
            #     end_date = row[19].strftime("%Y-%m-%d")
            #     package_data['end_collection_date'] = end_date

            # resources are stored in 6-column intervals
            package_data['resources'] = []
            for i in range(21, len(row), 6):  
                if row[i] is not None:
                    resource = {
                        'url': row[i],
                        'name': row[i + 1],
                        'description': row[i + 2],
                        'format': row[i + 3],
                        'restricted': {
                            'level': self.access_rights.get(row[i + 4], 'notspecified'),
                            'allowed_users': ""
                        }
                    }
                    package_data['resources'].append(resource)

            lower_case = row[1].lower()
            alphanumeric = re.sub(r'[^a-z0-9]', '', lower_case)
            package_data['name'] = alphanumeric

            return package_data

def save_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        api_key = config['DEFAULT'].get('API_KEY')
        instance_url = config['DEFAULT'].get('INSTANCE_URL')
        path = config['DEFAULT'].get('excel_file_path')
    else:
        api_key = input("Enter the API key: ")
        while True:
            instance_url = input("Enter the instance url (e.g. http://192.168.92.1:5000): ")
            if is_valid_url(instance_url):
                break
        path = input("Please enter the Excel file path: ").strip()
        if not os.path.exists(path):
            print("The file path does not exist.")
            exit(0)
        config['DEFAULT'] = {'API_KEY': api_key, 'INSTANCE_URL': instance_url, 'EXCEL_FILE_PATH': path}
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    return api_key, instance_url, path

# helper functions
def contains_value_with_index(dicts, value):
    for index, d in enumerate(dicts):
        if value in d.values():
            return True, index
    return False, -1

def string_in_dicts(string, list_of_dicts):
    for index, dictionary in enumerate(list_of_dicts):
        if string in dictionary.values():
            return True, index
    return False, -1

def is_valid_url(url):
    pattern = re.compile(r"^(http|https)://(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}$")
    if pattern.match(url):
        protocol, rest = url.split("://")
        ip, port = rest.split(":")
        parts = ip.split(".")
        if all(0 <= int(part) <= 255 for part in parts):
            if 0 <= int(port) <= 65535:
                return True
    return False

def convert_string_to_tags(input_string):
    words = [word.strip() for word in input_string.split(';') if word.strip()]
    return [{'name': word} for word in words]

if __name__ == "__main__":
    api_key, api_url, path = save_config()
    ckan_manager = CKANManager(api_url, api_key)
    metadata_manager = MetadataManager('ckan_template.json')
    excel_handler = ExcelHandler(path)

    start_row = excel_handler.find_start_row('Titel')
    cat_data = excel_handler.extract_data(start_row + 1)

    for row in cat_data:
        package_data = metadata_manager.validate_and_construct_package(row)
        response = ckan_manager.post('/api/3/action/package_create', package_data)
        if response['success']:
            print(f"Successfully created catalog {response['result']['title']}")
        else:
            print(f'Catalog {row[1]} could not be created\n\n{response}')
            #print(f"Error processing catalog {row[1]}: {e}")
