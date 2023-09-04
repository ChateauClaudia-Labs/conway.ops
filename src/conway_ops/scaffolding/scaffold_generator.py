from jinja2                                                 import Environment, FileSystemLoader
from pathlib                                                import Path

from conway_ops.scaffolding.scaffolding_statics             import ScaffoldingStatics

class ScaffoldGenerator():

    '''
    Class used to scaffold new projects adhering to the Conway design patterns. It creates a project structure containing
    all the mandatory repos for a Conway application, and generates Python code and other necessary files to populate
    the project folders with sample implementation of services, tests and documentation.

    This class allows for different types of projects to be generated. For example, maybe some projects need scaffolding
    for a CLI, a UI or a web server, whereas other projects don't. To support this, code generation is dependent on the notion 
    of a :class:``ScaffoldSpec``. Code generating is normally driven from templates, and different templates are used
    depending on the concrete instance of a :class:``ScaffoldSpec`` that is passed to the constructor of this class.
    '''
    def __init__(self, project_root, spec):
        self.project_root                                   = project_root
        self.spec                                           = spec

    def generate(self, subproject):
        '''
        Generates sample code for a particular repo, as per the templates specified in ``self.spec``.

        :param str subproject:  the subfolder of a project that correspond to the particular repo, config or other area 
            for which this method will generate scaffolding code. It is needed because
            a project usually consists of multiple repos (as sub-folders of the root project folder), as well as a (runtime) config
            folder external from all repos, and scaffolding generation is done one repo at a time.
        '''
        generated_files_l                                   = []
        if subproject == "config": # Special case
            subproject_templates                            = f"{self.spec.templates_root}/config"
        else: # we are generating code for a repo, folder structure is templated
            subproject_templates                            = f"{self.spec.templates_root}/{ScaffoldingStatics.PARAMS}.{ScaffoldingStatics.APP_CODE_PARAM}.{subproject}"
        environment                                         = Environment(loader=FileSystemLoader(subproject_templates))
        for template_relative_path in environment.list_templates():
            template                                        = environment.get_template(template_relative_path)
            
            content = template.render(
                self.spec.variables_dict
            )
            destination_filename                            = f"{self.project_root}/{template_relative_path}"
            destination_filename                            = self._eval_templated_path(destination_filename, self.spec.variables_dict)
            destination_path                                = Path(destination_filename).parent.as_posix()
            Path(destination_path).mkdir(parents=True, exist_ok=True)
            with open(destination_filename, mode="w", encoding="utf-8") as generated_file:
                generated_file.write(content)
                generated_files_l.append(destination_filename)

        return generated_files_l
    

    def _eval_templated_folder(self, folder, variables_dict):
        '''
        Helper method to modify folder names that are using template variables.
        It is a building block for ``self._eval_templated_path``, whereby the latter breaks a path into 
        the component folders and uses this method to evaluate each folder separately.

        For example, if ``variables_dict["params"]["app_code"] == "cash"``, then if ``folder == "params.app_code.svc"``
        the method will return ``cash.svc``

        :param str folder: a posibly templated folder or filename. Example: ``"params.app_name"``
        :param dict variables_dict: dictionary defining the template variables, possibly nested across subdictionaries.
        :return: a modified folder where templated strings are replaced by their values.
        :rtype: str
        '''
        tokens = folder.split(".")
        if len(tokens) == 0 or not tokens[0] in variables_dict.keys(): # Hit bottom - nothing templated in the path
            return folder
        
        # If we get here, then we had a match, so the path includes templates
        val                                                 = variables_dict[tokens[0]]
        tail_folder                                         = ".".join(tokens[1:])
        
        if type(val)==dict: # we need to recurse
            return self._eval_templated_folder(tail_folder, val)
        else:
            #if len(tail_folder) > 0: # There was more text than the template variables, so need to not lose the "."
            #    tail_folder                                 = f".{tail_folder}"
            return f"{str(val)}{tail_folder}"
        
    def _eval_templated_path(self, path, variables_dict):
        '''
        Helper methd to evaluate template variables in a templated path and return the resulting path.

        For example, if 
        
        .. code-block::
        
            path == "params.app_code.svc/src/params.app_name/__init__.py"
            
        then this mehod will return

        .. code-block::
        
            "cash.svc/src/CashManagement/__init__.py"
            
        provided that 

        * ``variables_dict["params"]["app_code"] == "cash"``
        * and ``variables_dict["params"]["app_name"] == "CashManagement"``

        :param str path: a posibly templated folder or filename. Example: ``"params.app_code.svc/src/params.app_name/__init__.py"``
        :param dict variables_dict: dictionary defining the template variables, possibly nested across subdictionaries.
        :return: a modified path where templated strings are replaced by their values.
        :rtype: str
        '''
        evaluated_parts                                     = []
        for templated_folder in Path(path).parts:
            folder                                          =  self._eval_templated_folder(templated_folder, variables_dict)
            evaluated_parts.append(folder)
        return "/".join(evaluated_parts)