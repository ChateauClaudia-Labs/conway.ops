{% macro SCENARIOS() -%}
    {{ params.app_abbreviation_upper }}_SCENARIOS_REPO
{%- endmacro %}

import os                                               as _os

from conway.observability.logger                        import Logger

class {{ params.app_abbreviation_upper }}_Logger(Logger):

    '''
    Utility to control what messages get logged by the ``{{ params.app_module }}`` module
    '''
    def __init__(self, activation_level):

        super().__init(activation_level)

    def log(self, message, log_level, stack_level_increase, show_caller=True):
        '''
        '''
        super().log(message, log_level, stack_level_increase, show_caller)

    def unclutter(self, message):
        '''
        Helper method that derived classes can use to shorten long message. For example, to replace
        long root paths by a string for an environment variable
        '''
        msg1                                            = super().unclutter(message)
        {{ SCENARIOS() }}                               = "{{ params.app_name_upper }}_SCENARIOS_REPO"
        if {{ SCENARIOS() }} in _os.environ.keys():
            VAR                                         = _os.environ[{{ SCENARIOS() }}]
            msg2                                        = msg1.replace(VAR, f"${{ SCENARIOS()}}")

            # Try a variation i ncase VAR is "/c/..." but msg2 starts with "C:/..."
            VAR2                                        = VAR.replace("/c/", "C:/")
            msg3                                        = msg2.replace(VAR2, f"${{ SCENARIOS()}}")
            result                                      = msg3
        else:
            result                                      = msg1

        return result
