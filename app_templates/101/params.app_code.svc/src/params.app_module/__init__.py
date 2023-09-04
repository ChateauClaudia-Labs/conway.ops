from {{ params.app_module}}.application.{{ params.app_module }}_application import {{ params.app_name }}Application

# Start the global singleton that represents the application
{{ params.app_name }}Application()