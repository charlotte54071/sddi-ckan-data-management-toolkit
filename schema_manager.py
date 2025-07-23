import json

class SchemaManager:
    '''Manages schema templates and field mappings'''
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        '''Load all schema templates'''
        for schema_type, template_path in self.config['schema_mappings'].items():
            with open(template_path, 'r') as f:
                self.templates[schema_type] = json.load(f)

    def get_template(self, schema_type):
        '''Get template for a specific schema type'''
        return self.templates.get(schema_type)

    def get_field_mapping(self, schema_type):
        '''Get field mappings for a specific schema type'''
        template = self.get_template(schema_type)
        return template['field_mappings'] if template else None

    def get_resource_fields(self, schema_type):
        '''Get resource fields for a specific schema type'''
        template = self.get_template(schema_type)
        return template['resource_fields'] if template else None

    def validate_schema_type(self, schema_type):
        '''Validate if the schema type is supported'''
        return schema_type in self.config['schema_mappings']

    def get_common_fields(self):
        '''Get fields common to all schemas'''
        return self.config['excel_configuration']['common_fields']

    def get_resource_field_names(self):
        '''Get resource field names'''
        return self.config['excel_configuration']['resource_fields']
