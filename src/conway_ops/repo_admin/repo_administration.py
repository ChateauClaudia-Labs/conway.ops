from pathlib                                                    import Path
import pandas                                                   as _pd
import xlsxwriter

from conway.reports.report_writer                               import ReportWriter

from conway_ops.repo_admin.repo_statics                         import RepoStatics
from conway_ops.repo_admin.repo_inspector_factory               import RepoInspectorFactory
from conway_ops.repo_admin.repo_inspector                       import RepoInspector
from conway_ops.repo_admin.filesystem_repo_inspector            import FileSystem_RepoInspector
from conway_ops.repo_admin.repo_bundle                          import RepoBundle

class RepoAdministration():

    '''
    Class to assist operator to manage the multiple repos that comprise the Vulnerability Management solution

    :param str local_root: Folder or URL of the parent folder for all local GIT repos.

    :param str remote_root: Folder or URL of the parent folder for the remote GIT repos

    :param RepoBundle repo_bundle: Object encapsulating the names of the GIT repos for which joint GIT operations 
        are to be done by this :class:`RepoAdministration` instance.
    '''
    def __init__(self, local_root, remote_root, repo_bundle):
        self.local_root                                 = local_root
        self.remote_root                                = remote_root
        self.repo_bundle                                = repo_bundle

    def create_project(self, project_name, work_branch_name):
        '''
        Creates all the repos required for a project as per standard patterns of the 
        :class:``RepoBundle``.

        :param str project_name: name of the project (i.e., application) for which repos must be created
        :param str work_branch_name: name of the branch in which work will be done, i.e., a branch that exists
            both in the local and the remote and which is how the local pushes work to the remote.
            NB: By default, the master branch only exists in the remote, hence the need for the work_branch_name.

        :return: a :class:``RepoBundle`` with information about all the repos created for project ``project_name``.
        :rtype: RepoBundle
        '''
        bundle                                          = RepoBundle(project_name)
        for repo_info in bundle.bundled_repos():
            remote_url                                  = self.remote_root + "/" + repo_info.name
            local_url                                   = self.local_root + "/" + repo_info.name

            # This creates the master branch
            #
            #   GOTCHA: unlike other methods in this class, we only support file system repos
            #           (not GIT Hub repos)
            #
            inspector                                   = FileSystem_RepoInspector(self.remote_root, repo_info.name)
            remote_repo                                 = inspector.init_repo() 

            # Avoid having an empty remote, so that it has a head and we can create branches.
            # Accomplish that by adding a scaffold README.md and a scaffold .gitignore
            README_FILENAME                             = "README.md"
            with open(remote_url + "/" + README_FILENAME, 'w') as f:
                f.write(repo_info.description + " for application '" + project_name + "'.\n")

            GIT_IGNORE_FILENAME                         = ".gitignore"
            with open(remote_url + "/" + GIT_IGNORE_FILENAME, 'w') as f:
                for line in self._git_ignore_content():
                    f.write(line + "\n")


            remote_repo.index.add([README_FILENAME, GIT_IGNORE_FILENAME])
            remote_repo.index.commit("Initial commit")            

            master_branch                               = remote_repo.active_branch
            work_branch                                 = remote_repo.create_head(work_branch_name)
            work_branch.checkout()
            
            local_repo                                  = remote_repo.clone(local_url)

            # Now come back to master branch on the remote, so that if local tries to do a git push,
            # the push succeeds (i.e., avoid errors of pushing to a remote branch arising from that branch
            # being checked out in the remote, so move remote to a branch to which pushes are not made, i.e., to master).
            #
            master_branch.checkout()

        return bundle
      
    def create_branch(self, branch_name):
        '''
        Creates a new local GIT branch called ``branch_name`` in all the repos, and sets up the
        corresponding remote.

        The contents of the new branch are initialized to be the same as the remote master branch.
        '''
        raise ValueError("Not implemented")
    
    def commit_branch(self, branch_name, commit_message, preview_only=True):
        '''
        Identifies all the changes in the working trees across all local repos, and then either:

        * Returns a string message with what they are, if ``preview_only`` is True

        * Or adds all the changes to the index, commits them, pushes to the remote, and merges them into master in the
          remote.
        '''
        raise ValueError("Not implemented")
    
    def update_release_candidate_branch(self, timestamp):
        '''
        Merges the contents of the master branch into the release candidate branch identified by the given timestamp.

        :param Timestamp timestamp: used to tag the branch being created and/or updated.
        '''
        raise ValueError("Not implemented")
    
    def remove_branch(self, branch_name):
        '''
        '''
        raise ValueError("Not implemented")

    def checkout_branch(self, branch_name, repos_in_scope_l, local=True):
        '''
        For GIT repos in scope, switches them all to the branch given by ``branch_name``, provided that:

        * No repo in scope have no untracked files
        * No repo in scope is bare
        * All repos in scope have branch called ``branch_name``

        :param str branch_name: The name of the branch to which to switch
        :param list[str] repos_in_scope_l: A list of names for GIT repos for which stats are requested. 

        :param bool local: Optional parameter that is True by default. 
            If True, then the repos in scope are local, i.e., the GIT repos under ``self.local_root``. If False,
            then repos in scope are remote, i.e., under ``self.remote_root``.
        :return: A DataFrame with the status information about each repo
        :rtype: :class:`pandas.DataFrame`
        '''
        RS                                              = RepoStatics()
        if local:
            REPOS_ROOT                                  = self.local_root
            repo_environment                            = RS.LOCAL_REPO
        else:
            REPOS_ROOT                                  = self.remote_root
            repo_environment                            = RS.REMOTE_REPO

        # Check that we can move out of current branch safely, i.e., there is no uncommitted work
        stats_df                                        = self.repo_stats(repos_in_scope_l=repos_in_scope_l)
        stats_df                                        = stats_df[stats_df[RS.LOCAL_OR_REMOTE_COL]==repo_environment]
        def _bad_row(row):
            '''
            Returns True if the ``row`` contains information about a repo that has untracked changes or is dirty
            (i.e., working tree has modifications and/or index has uncommitted changes)
            '''
            if row[RS.NB_UNTRACKED_FILES_COL] > 0 or row[RS.NB_MODIFIED_FILES_COL] > 0 or row[RS.NB_DELETED_FILES_COL] > 0:
                return True
            else:
                return False

        bad_df                                          = stats_df[stats_df.apply(lambda row: _bad_row(row), axis=1)]
        if len(bad_df) > 0:
            raise ValueError("Can't switch to branch '" + str(branch_name) + "' because these repos have uncommitted changes: "
                             + ", ".join(list(bad_df[RS.REPO_NAME_COL].unique())))
        
        # Now check that branch exists in all the pertinent repos
        repos_lacking_desired_branch                    = []
        for repo_name in repos_in_scope_l:
            inspector                                   = RepoInspectorFactory.findInspector(REPOS_ROOT, repo_name)
            branches                                    = inspector.branches()
            if not branch_name in branches:
                repos_lacking_desired_branch.append(repo_name)
        if len(repos_lacking_desired_branch) > 0:
            raise ValueError("Can't switch to branch '" + str(branch_name) + "' because that branch doesn't exist in these repos: "
                             + ", ".join(repos_lacking_desired_branch))

        # Now move to the new branch
        for repo_name in repos_in_scope_l:
            inspector                                   = RepoInspectorFactory.findInspector(REPOS_ROOT, repo_name)

            status                                      = inspector.checkout(branch_name)

            print("\n-----------" + repo_name + "-----------\n")
            print("\tStatus:\t\t" + str(status))

    def create_repo_report(self, publications_folder, repos_in_scope_l=None, mask_nondeterministic_data=False):
        '''
        Creates an Excel report with multiple worksheets, as follows:

        * There is a worksheet with general stats for all repos

        * For each repo name, there are two worksheets, containing log information for the local and remote
            repos with those names.

        :param str publications_folder: Root directory for a folder structure under which all reports
            must be saved. The Excel report created by this method will be saved in the subdirectory
            ``/Operator Reports/DevOps/`` under this root ``publications_folder``.
        :param list[str] repos_in_scope_l: A list of names for GIT repos for which stats are requested. If set to None, 
            then it will default to provide stats for the repos ``self.repo_bundle``
        :param bool mask_nondeterministic_data: If True, then any data that is non-deterministic (such as dates or hash 
            codes) is masked. This is False by default. Typical use case for masking is in test cases that need 
            determinism.
        :rtype: None
        '''
        # First, set up common static variables 
        MASKED_MSG                                              = "< MASKED > "

        STATS_DIRECTORY                                         = publications_folder + "/"                 \
                                                                    + RepoStatics.OPERATOR_REPORTS + "/"    \
                                                                    + RepoStatics.DEV_OPS_REPORTS_FOLDER
                                                        
        STATS_FILENAME                                          = RepoStatics.REPORT_REPO_STATS + ".xlsx"
        Path(STATS_DIRECTORY).mkdir(parents=True, exist_ok=True)

        workbook                                                = xlsxwriter.Workbook(STATS_DIRECTORY + "/" + STATS_FILENAME)
        writer                                                  = ReportWriter()

        # Now generate and save the stats worksheet
        stats_df                                                = self.repo_stats(repos_in_scope_l)
        if mask_nondeterministic_data:
            stats_df[RepoStatics.LAST_COMMIT_TIMESTAMP_COL]     = MASKED_MSG
            stats_df[RepoStatics.LAST_COMMIT_HASH_COL]          = MASKED_MSG

        worksheet                                               = workbook.add_worksheet(RepoStatics.REPORT_REPO_STATS_WORKSHEET)
        widths_dict                                             = {RepoStatics.REPO_NAME_COL:               20,
                                                                    RepoStatics.LOCAL_OR_REMOTE_COL:         15,
                                                                    RepoStatics.LAST_COMMIT_COL:             40,
                                                                    RepoStatics.LAST_COMMIT_TIMESTAMP_COL:   30,
                                                                    RepoStatics.LAST_COMMIT_HASH_COL:        45}
        writer.populate_excel_worksheet(stats_df, workbook, worksheet, widths_dict=widths_dict)
        
        # Now generate and save the multiple log worksheets
        all_repos_logs_dict                                     = self.repo_logs(repos_in_scope_l)
        for repo_name in all_repos_logs_dict.keys():
            a_repo_logs_dict                                    = all_repos_logs_dict[repo_name]
            for instance_type in a_repo_logs_dict.keys(): # instance_type refers to local vs remote repos
                log_df                                          = a_repo_logs_dict[instance_type]
                if mask_nondeterministic_data:
                    log_df[RepoStatics.COMMIT_DATE_COL]         = MASKED_MSG
                    log_df[RepoStatics.COMMIT_HASH_COL]         = MASKED_MSG
                    log_df[RepoStatics.COMMIT_AUTHOR_COL]       = MASKED_MSG

                sheet_name                                      = RepoAdministration.worksheet_for_log(repo_name, 
                                                                                                       instance_type)
                worksheet                                       = workbook.add_worksheet(sheet_name)
                widths_dict                                     = {RepoStatics.COMMIT_DATE_COL:             30,
                                                                    RepoStatics.COMMIT_SUMMARY_COL:          35,
                                                                    RepoStatics.COMMIT_FILE_COL:             65,
                                                                    RepoStatics.COMMIT_HASH_COL:             45,
                                                                    RepoStatics.COMMIT_AUTHOR_COL:           40
                }
                writer.populate_excel_worksheet(log_df, workbook, worksheet, widths_dict=widths_dict, freeze_col_nb=3)
                                                        
        workbook.close()

    def worksheet_for_log(repo_name, instance_type):
        '''
        :param str instance_type:  Either ``RepoStatics.LOCAL_REPO`` or ``RepoStatics.REMOTE_REPO``
        :param str repo_name: Name of the repo whose logs are to be persisted in the worksheet whose name is computed
            by this method.
        :return: The worksheets used by the ``create_repo_report`` method to save log information for the repo
            identified by ``repo_name`` for the given ``instance_type``
        :rtype: str
        '''
        sheet_name                                      = repo_name + " (" + instance_type + ")"
        
        # xlsxwriter does not allow worksheet names to exceed 31 characters, so truncate if needed
        # to avoid an excelption when we save
        sheet_name                                      = sheet_name[:31]
        return sheet_name


    def repo_stats(self, repos_in_scope_l=None):
        '''
        :param list[str] repos_in_scope_l: A list of names for GIT repos for which stats are requested. If set to None, 
            then it will default to provide stats for names of ``self.repo_bundle.bundled_repos()``
        :return: A descriptive DataFrame with information about each repo, such as what branch it is in for local and 
            remote, whether it has unchecked or untracked files, and most recent commit.
        :rtype: :class:`pandas.DataFrame`
        '''
        RS                                              = RepoStatics()

        data_l                                          = []

        columns                                         = [RS.REPO_NAME_COL,
                                                           RS.LOCAL_OR_REMOTE_COL,
                                                           RS.CURRENT_BRANCH_COL,
                                                           RS.NB_UNTRACKED_FILES_COL,
                                                           RS.NB_MODIFIED_FILES_COL,
                                                           RS.NB_DELETED_FILES_COL,
                                                           RS.LAST_COMMIT_COL,
                                                           RS.LAST_COMMIT_TIMESTAMP_COL,
                                                           RS.LAST_COMMIT_HASH_COL,
                                                           ]
        if repos_in_scope_l is None:
            repos_in_scope_l                            = [repo_info.name for repo_info in self.repo_bundle.bundled_repos()]
        for repo_name in repos_in_scope_l:
            local_inspector                             = RepoInspectorFactory.findInspector(self.local_root, repo_name)

            repo_name, current_branch, \
                commit_message, commit_ts, commit_hash, \
                untracked_files, modified_files, deleted_files \
                                                        = self._one_repo_stats(local_inspector)
            local_or_remote                             = RS.LOCAL_REPO
            data_l.append([repo_name, local_or_remote, current_branch, 
                           len(untracked_files), len(modified_files), len(deleted_files),
                           commit_message, commit_ts, commit_hash, 
                           ])

            remote_inspector                            = RepoInspectorFactory.findInspector(self.remote_root, repo_name)

            repo_name, current_branch, \
                commit_message, commit_ts, commit_hash, \
                untracked_files, modified_files, deleted_files \
                                                    = self._one_repo_stats(remote_inspector)
            local_or_remote                         = RS.REMOTE_REPO
            data_l.append([repo_name, local_or_remote, current_branch, 
                           len(untracked_files), len(modified_files), len(deleted_files),
                        commit_message, commit_ts, commit_hash, 
                        ])

        result_df                                       = _pd.DataFrame(data = data_l, columns = columns)

        return result_df
    
    def repo_logs(self, repos_in_scope_l=None):
        '''
        :param list[str] repos_in_scope_l: A list of names for GIT repos for which stats are requested. If set to None, then 
            it will default to provide stats for ``self.repo_names``
        :return: Logs for each of the repos named in ``repos_in_scope_l``. For each repo name, two DataFrames are produced, 
            corresponding to the local and remote repos for a given name. These multiple DataFrames are packaged in 
            a 2-level dictionary, where the top level keys are the repo names, the next level keys are the 
            ``RepoStatics.LOCAL_REPO`` and ``RepoStatics.REMOTE_REPO``, and the values are the log DataFrames.
        :rtype: :class:`dict`
        '''
        result_dict                                     = {}
        if repos_in_scope_l is None:
            repos_in_scope_l                            = [repo_info.name for repo_info in self.repo_bundle.bundled_repos()]
        for repo_name in repos_in_scope_l:
            local_inspector                             = RepoInspectorFactory.findInspector(self.local_root, repo_name)
            remote_inspector                            = RepoInspectorFactory.findInspector(self.remote_root,repo_name)

            local_log_df                                = local_inspector.log_to_dataframe()
            remote_log_df                               = remote_inspector.log_to_dataframe()
            result_dict[repo_name]                      = {RepoStatics.LOCAL_REPO:      local_log_df,
                                                           RepoStatics.REMOTE_REPO:     remote_log_df}

        return result_dict

    def _git_ignore_content(self):
        '''
        :return: Contents with which to initialize a new ``.gitignore`` file for a new Git repo.
        :rtype: list[str]
        '''
        lines                                           = []
        lines.append("# Python build")
        lines.append("__pycache__/")
        lines.append("*.egg-info/")
        lines.append("")
        lines.append("")
        lines.append("# Used in documentation")
        lines.append("build/")
        lines.append("*.~docx")
        lines.append("*.~xlsx")
        lines.append("*.~vsdx")
        lines.append("*.~pptx")
        lines.append("")
        lines.append("")
        lines.append("# Used in operator tools")
        lines.append("*.ipynb_checkpoints/")
        lines.append("")
        lines.append("# Used in test scenarios")
        lines.append("ACTUALS@*/")
        lines.append("RUN_NOTES/")
        lines.append("")
        lines.append("")

        return lines

    def _one_repo_stats(self, repo: RepoInspector):
        '''
        '''
        repo_name                                       = repo.repo_name
        current_branch                                  = repo.current_branch()

        commit_info                                     = repo.last_commit()
        commit_hash                                     = commit_info.commit_hash
        commit_message                                  = commit_info.commit_msg
        commit_ts                                       = commit_info.commit_ts.timestamp

        untracked_files                                 = repo.untracked_files()
        modified_files                                  = repo.modified_files()
        deleted_files                                   = repo.deleted_files()

        return repo_name, current_branch, commit_message, commit_ts, commit_hash, \
            untracked_files, modified_files, deleted_files


