import abc

class ScaffoldingStatics(abc.ABC):

    '''
    Represents a static enum collection of static variables that are used in the scaffolding process for a new
    Conway application
    '''
    def __init__(self):
        pass

    PARAMS                                              = "params"
    APP_CODE_PARAM                                      = "app_code"
    APP_NAME_PARAM                                      = "app_name"
    APP_NAME_UPPER_PARAM                                = "app_name_upper"
    APP_ABBREVIATION_UPPER_PARAM                        = "app_abbreviation_upper"
    APP_ABBREVIATION_LOWER_PARAM                        = "app_abbreviation_lower"
    APP_MODULE_PARAM                                    = "app_module"

    AUTHOR_PARAM                                        = "author"
    AUTHOR_EMAIL_PARAM                                  = "author_email"
    PROJECT_DESCRIPTION_PARAM                           = "project_description"
    PROJECT_ROOT_PARAM                                  = "project_root"


  

