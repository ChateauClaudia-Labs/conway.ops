import os                                                               as _os
{% macro CLASS() -%}
    {{ params.app_abbreviation_upper }}_Logger
{%- endmacro %}
{% macro MODULE() -%}
    {{ params.app_abbreviation_lower }}_logger
{%- endmacro %}

from conway.application.application                                     import Application
from {{ params.app_module }}.observability.{{ MODULE() }} import {{ CLASS() }}

class {{ params.app_name }}Application(Application):

    def __init__(self):

        APP_NAME                                        = "{{ params.app_name }}"

        logger                                          = {{ CLASS() }}(activation_level={{ CLASS() }}.LEVEL_INFO)

        super().__init__(logger)
          
        # __file__ is something like 
        #
        #   'C:\Alex\Code\{{ params.app_code }}\{{ params.app_code}}.svc\src\{{ params.app_module }}\application\{{ params.app_module}}_application.py'
        #
        #
        # So to get the project folder ("{{ params.app_code }}") we need to go 4 directories up
        #
        directory                                       = _os.path.dirname(__file__)

        for idx in range(4):
            directory                                   = _os.path.dirname(directory)
        project_directory                               = directory   
        config_path                                     = project_directory + "/config"     
          
        super().__init__(app_name=APP_NAME, config_path=config_path, logger=logger)