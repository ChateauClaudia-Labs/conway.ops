import git
import datetime as _dt

from conway.util.timestamp                                  import Timestamp

class RepoInspector():

    '''
    Utility class that is able to execute GIT commands for both local and remote repos.

    It was introduced as an alternative to GitPython's ``git.Repo`` class, since the latter only works
    for repos stored in the local file system, not for remote repos identified by a URL.

    :param str parent_url: A string identifying the location under which the repo of interest lives as
        a "subfolder" or "sub resource". May be a path to the local file system or the URL to a remote server.
    :param str repo_name: A string identifying the name of the repo of interest, as a "subfolder"
        or "sub resource" under the ``parent_url``.

    '''
    def __init__(self, parent_url, repo_name):

        self.parent_url                     = parent_url
        self.repo_name                      = repo_name
        self.executor                       = git.cmd.Git(parent_url + "/" + repo_name)


    def execute(self, command):
        '''
        Executes the git command.

        :param str command: A string representing the full GIT CLI command to run. Example: "git status"
        '''
        result                              = self.executor.execute(command)
        return result


    def current_branch(self):
        '''
        :return: The name of the current branch
        :rtype: str
        '''
        result                              = self.executor.execute(command = "git rev-parse --abbrev-ref HEAD")
        return result
    
    def modified_files(self):
        '''
        :return: List of files that have been modified but not yet staged. In the boundary case where a file
            has an unstaged deletion, that does not count as "modified" as per the semantics of this method.
        :rtype: list
        '''
        raw                                 = self.executor.execute(command = "git ls-files -m")

        # raw is something like
        #
        #       'src/vulnerability_management/projector/vm_database_projector.py\nsrc/vulnerability_management/util/static_globals.py'
        #
        # so need to split string by new lines
        #
        files_l                             = [x for x in raw.split("\n") if len(x) > 0]

        # Under git semantics, the modified files obtained by doing "git ls-files -m" includes unstaged deletions.
        # So to get the "real" list of modified files, exclude deletes
        #
        deleted_files_l                     = self.deleted_files()
        result                              = [f for f in files_l if not f in deleted_files_l]

        return result
    
    def deleted_files(self):
        '''
        :return: List of files with an unstaged deletion
        :rtype: list
        '''
        raw                                 = self.executor.execute(command = "git ls-files -d")
        # raw is something like
        #
        #       'src/vulnerability_management/projector/vm_database_projector.py\nsrc/vulnerability_management/util/static_globals.py'
        #
        # so need to split string by new lines
        #
        result                              = [x for x in raw.split("\n") if len(x) > 0]

        return result

    def untracked_files(self):
        '''
        :return: List of files that are not tracked
        :rtype: list
        '''
        raw                                 = self.executor.execute(command = "git ls-files -o --exclude-standard")
        # raw is something like
        #
        #       'src/vulnerability_management/projector/vm_database_projector.py\nsrc/vulnerability_management/util/static_globals.py'
        #
        # so need to split string by new lines
        #
        result                              = [x for x in raw.split("\n") if len(x) > 0]

        return result

    def last_commit(self):
        '''
        :return: A :class:`CommitInfo` with information about last commit"
        :rtype: str
        '''
        raw                                 = self.executor.execute(command = 'git log -1 --pretty=format:"%H|%as|%s"')

        # raw is something like
        #
        #   'a72013ecceca532f6d99453d4a9a5a67d5ce8a90|2023-06-05|Added logic to create submissions directory if missing'
        #
        # so we must split it by the delimeter "|" and parse each token as required
        #
        tokens                              = raw.split("|")
        commit_hash                         = tokens[0]
        commit_ts                           = Timestamp.from_datetime(_dt.datetime.strptime(tokens[1], "%Y-%m-%d"))
        commit_msg                          = "|".join(tokens[2:])

        result                              = CommitInfo(commit_hash, commit_msg, commit_ts)

        return result
    
    def branches(self):
        '''
        :return: (local) branches for the repo
        :rtype: list[str]
        '''
        raw                                 = self.executor.execute(command = 'git log -1 --pretty=format:"%H')
        # raw is something like
        #
        #               '  ah-dev\n  integration\n  operate\n* story_1485'
        #
        # so to turn it into a list we must split by new lines and then strip out empty spaces and the "*"
        result                              = [b.strip("*").strip() for b in raw.split("\n") if not "->" in b]
        return result

    def checkout(self, branch_name):
        '''
        :return: A status from switching to branch ``branch_name``
        :rtype: str
        '''
        result                              = self.executor.execute(command = "git checkout " + str(branch_name))
        return result

class CommitInfo():

    '''
    Helper data structure to contain some information about a commit

    :param str commit_hash: Hash for a commit. Example: "15e5a7f280096c84ed08b72371580907d0f52ff5"
    :param str commit_msg: Message for a commit. Example: "Added logic to create submissions directory if missing"
    :param Timestamp commit_ts: Timestamp as of when the commit was made
    '''
    def __init__(self, commit_hash, commit_msg, commit_ts):
        self.commit_hash                    = commit_hash
        self.commit_msg                     = commit_msg
        self.commit_ts                      = commit_ts
