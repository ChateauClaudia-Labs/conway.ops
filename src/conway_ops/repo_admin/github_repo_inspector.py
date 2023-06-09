import requests                                             as _requests
from dateutil                                               import parser as _parser

from conway.util.timestamp                                  import Timestamp
from conway.util.yaml_utils                                 import YAML_Utils
from conway_ops.repo_admin.repo_inspector                   import RepoInspector, CommitInfo, CommittedFileInfo

class GitHub_RepoInspector(RepoInspector):

    '''
    Utility class that is able to execute GIT commands for public repos located in GitHub

    :param str parent_url: A string identifying the location under which the repo of interest lives as
        a "subfolder" or "sub resource". May be a path to the local file system or the URL to a remote server.
    :param str repo_name: A string identifying the name of the repo of interest, as a "subfolder"
        or "sub resource" under the ``parent_url``.

    '''
    def __init__(self, parent_url, repo_name):

        super().__init__(parent_url, repo_name)

        # parent_url is something like 
        #
        #       "https://github.com/alejandro-fin"
        #
        # so we can extract the owner name from it ("alejandro-fin" in the example). This will be needed
        # to construct the URLs for other calls to the Git Hub API
        #
        cleaned_url                                     = parent_url.strip("/").strip()
        self.owner                                      = cleaned_url.split("/")[-1]

        if len(self.owner) == 0:
            raise ValueError("No owner was included in parent url '" + str(parent_url) + "', so can't call Git Hub APIs")
        
        # Get GitHub token to make authenticated calls
        #
        SECRETS_PATH                                    = "C:/Alex/Code/conway_fork/secrets.yaml"
        secrets_dict                                    = YAML_Utils().load(SECRETS_PATH)
        self.github_token                               = secrets_dict['secrets']['github_token']

    GIT_HUB_API                                         = "https://api.github.com"
    

    def _get_resource(self, resource_path):
        '''
        Invokes the Git Hub API to get information about the repo associated to this inspector.

        :param str resource_path: Indicates the path of a desired resource under the URL for the
            repo for which self is an inspector. Examples: "/commits/master", "/branches"
        :return: A Json representation of the resource as given by the GitHub API
        :rtype: str
        '''
        root_path                           = self.GIT_HUB_API + "/repos/" + self.owner + "/" + self.repo_name
        url                                 = root_path + resource_path

        return self._get_from_url(url)     
    
    def _get_from_url(self, url):
        '''
        Invokes the URL to get information about the repo associated to this inspector.

        :param str url: Indicates the absolute url in the GitHub API. 
        :return: A Json representation of the resource as given by the GitHub API
        :rtype: str
        '''
        headers = {
            'Authorization': 'Bearer ' + self.github_token,
            'Content-Type' : 'application/json',
            'Accept'       : 'application/json'
        }
        try:
            response                        = _requests.request(method          = 'GET', 
                                                                url             = url, 
                                                                params          = {}, 
                                                                data            = '', \
                                                                headers         = headers, 
                                                                timeout         = 20,
                                                                verify          = True) 

            data                            = response.json()

        except Exception as ex:
            raise ValueError("Problem connecting to Git Hub. Error is: " + str(ex))

        if response.status_code != 200:
            raise ValueError("Error status " + str(r.status_code) + " from doing: GET on '" + str(url) + "'")  
        return data      


    def current_branch(self):
        '''
        :return: The name of the current branch
        :rtype: str
        '''
        # In the Git Hub world there is no notion of "current branch" - this is a GIT-in-the-filesystem
        # notion. 
        # Since for practical purposes this is invoked when comparating some cloned repo to the master
        # branch in the remote, we just treat "master" as the "current branch" in GitHub
        return "master"
    
    def modified_files(self):
        '''
        :return: List of files that have been modified but not yet staged. In the boundary case where a file
            has an unstaged deletion, that does not count as "modified" as per the semantics of this method.
        :rtype: list
        '''
        # In the Git Hub world there is no notion of "modified files" - this is a GIT-in-the-filesystem
        # notion. 
        # So we return an empty list
        return []
    
    def deleted_files(self):
        '''
        :return: List of files with an unstaged deletion
        :rtype: list
        '''
        # In the Git Hub world there is no notion of "deleted files" - this is a GIT-in-the-filesystem
        # notion. 
        # So we return an empty list
        return []
    
    def untracked_files(self):
        '''
        :return: List of files that are not tracked
        :rtype: list
        '''
        # In the Git Hub world there is no notion of "untracked files" - this is a GIT-in-the-filesystem
        # notion. 
        # So we return an empty list
        return []

    def last_commit(self):
        '''
        :return: A :class:`CommitInfo` with information about last commit"
        :rtype: str
        '''
        data                                = self._get_resource("/commits/master")
        
        commit_datetime                     = _parser.parse(data['commit']['author']['date'])
        
        commit_hash                         = data['sha']
        commit_ts                           = Timestamp.from_datetime(commit_datetime)
        commit_msg                          = data['commit']['message']

        result                              = CommitInfo(commit_hash, commit_msg, commit_ts)

        return result

        
    def branches(self):
        '''
        :return: (local) branches for the repo
        :rtype: list[str]
        '''
        data                                = self._get_resource("/branches")

        result                              = [b['name'] for b in data]

        return result


    def committed_files(self):
        '''
        Returns an iterable over CommitedFileInfo objects, yielding in chronological order the history of commits
        (i.e., a log) for the repo associated to this :class:`RepoInspector`
        '''
        # This provides the first most recent commit, and links to "parent" commits - the commits right before it
        data                                = self._get_resource("/commits/master")

        return self._committed_files_impl(results_so_far=[], commit_count=0, data=data)

    def _committed_files_impl(self, results_so_far, commit_count, data):
        '''
        Helper method used to implement the recursion approach behind the method committed_files
        '''
        commit_date                         = data['commit']['author']['date']
        commit_author                       = data['commit']['author']['name']
        
        commit_hash                         = data['sha']
        commit_msg                          = data['commit']['message']

        file_count                          = 0
        result                              = results_so_far
        for file_info_dict in data['files']:
            filename                        = file_info_dict['filename']
            cfi                             = CommittedFileInfo(commit_nb           = commit_count,
                                                                commit_date         = commit_date,
                                                                summary             = commit_msg,
                                                                commit_file_nb      = file_count,
                                                                commit_file         = filename,
                                                                commit_hash         = commit_hash,
                                                                commit_author       = commit_author)
            result.append(cfi)

        # Now do recursion, for each parent
        parents                             = data['parents']
        for p in parents:
            p_data                          = self._get_from_url(p['url'])
            result                          = self._committed_files_impl(result, commit_count + 1, p_data)

        return result