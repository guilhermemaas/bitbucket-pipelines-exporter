import requests
from requests.auth import HTTPBasicAuth
import json
from os import environ
from prometheus_client import start_http_server, Gauge, Info
import time


def get_so_env(env_name:str)->str:
    return environ.get(env_name)


def get_current_time()->str:
    return {time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())}


def return_base_url()-> str:
    return 'https://api.bitbucket.org/2.0'


def return_workspace_uuid()-> json:
    base_url = return_base_url()

    request_url = f'{base_url}/user/permission/workspaces'

    headers = {
        'Accept': 'application/json'
    }
    response = requests.request(
        'GET',
        request_url,
        headers=headers
    )

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(',', ': ')))    


def return_workspace_repositories(workspace: str, username:str, app_password:str)-> list:
    base_url = return_base_url()
    request_url = f'{base_url}/repositories/{workspace}'
    repo_names = []

    headers = {
        'Accept': 'application/json'
    }

    print(f'{get_current_time()}: Requesting...: {request_url}')

    while request_url:
        response = requests.get(
            request_url,
            auth=HTTPBasicAuth(username,app_password),
            headers=headers
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                repo_names.extend(repo['slug'] for repo in data['values'])
                request_url = data.get('next')
            except json.JSONDecodeError:
                print(f'{get_current_time()}: return_workspace_repositories - Failed to decode JSON from response.')
                break
            except KeyError:
                print(f'{get_current_time()}: return_workspace_repositories - Unexpected JSON format: {response.text}')
                break
        else:
            print(f'{get_current_time()}: return_workspace_repositories - Failed to fetch data: {response.status_code} - {response.text}')
            break

    print(json.dumps(repo_names, indent=4))
    return repo_names

def return_repository_pipelines(workspace: str, username:str, app_password:str, repository_slug:str)-> list:
    base_url = return_base_url()
    #request_url = f'{base_url}/repositories/{workspace}/{repository_slug}/pipelines'
    request_url = f'{base_url}/repositories/{workspace}/{repository_slug}/pipelines?sort=-created_on'
    pipelines = []
    pipeline_execution = {}

    headers = {
        'Accept': 'application/json'
    }

    print(f'{get_current_time()}: Requesting...: {request_url}')

    response = requests.get(
        request_url,
        auth=HTTPBasicAuth(username,app_password),
        headers=headers
    )

    data = response.json()
    
    if response.status_code == 200 and data['values']:
        try:
            data = response.json()
            for pipeline in data['values']:
                
                state_name = pipeline['state']['name']
                state_result = 'Unknown'
                

                if 'stage' in pipeline['state']:
                    state_result = pipeline['state']['stage']['name']
                elif 'result' in pipeline['state']:
                    state_result = pipeline['state']['result']['name']

                pipeline_execution = {
                    'build_number': pipeline['build_number'],
                    'state_name': state_name,
                    'state_result': state_result,
                    'duration_in_seconds': pipeline['duration_in_seconds'],
                    'creator_name': pipeline['creator']['display_name'],
                    'commit': pipeline['target']['commit']['links']['html']['href'],
                    'target_branch': pipeline['target']['selector']['pattern']
                }
                pipelines.append(pipeline_execution)
        except json.JSONDecodeError:
            print(f'{get_current_time()}: return_repository_pipelines - Failed to decode JSON from response.')
        except KeyError:
            print(f'{get_current_time()}: return_repository_pipelines - Unexpected JSON format: {response.text}')
    elif not data['values']:
        print(f'{get_current_time()}: return_repository_pipelines - This repository not have pipelines.')
        return None
    else:
        print(f'{get_current_time()}: return_repository_pipelines - Failed to fetch data: {response.status_code} - {response.text}')

    print(json.dumps(pipelines, indent=4))
    return pipelines


PIPELINE_DURATION = Gauge('pipeline_duration_seconds', 'Duration of pipeline builds', ['repository', 'state'])
PIPELINE_LAST_BUILD_NUMBER = Gauge('pipeline_last_build_number', 'Last build number', ['repository'])
PIPELINE_LAST_RESULT = Gauge('pipeline_last_result', 'Last build result as a label', ['repository', 'result'])
PIPELINE_LAST_CREATOR_NAME = Info('pipeline_last_creator', 'Last creator Name', ['repository', 'creator_name'])
PIPELINE_LAST_COMMIT = Info('pipeline_last_commit', 'Last commit that triggered the pipeline', ['repository', 'commit'])
PIPELINE_LAST_TARGET_BRANCH = Info('pipeline_last_target_branch', 'Last branch selected to start the pipeline', ['repository', 'target_branch'])


def update_metrics(workspace, username, app_password, repositories):

    for repository in repositories:
        pipelines = return_repository_pipelines(workspace, username, app_password, repository)
        if pipelines:
            last_pipeline = pipelines[0]
            PIPELINE_DURATION.labels(repository=repository, state=last_pipeline['state_name']).set(last_pipeline['duration_in_seconds'])
            PIPELINE_LAST_BUILD_NUMBER.labels(repository=repository).set(last_pipeline['build_number'])
            PIPELINE_LAST_RESULT.labels(repository=repository, result=last_pipeline['state_result']).set(1)
            PIPELINE_LAST_CREATOR_NAME.labels(repository=repository, creator_name=last_pipeline['creator_name'])
            PIPELINE_LAST_COMMIT.labels(repository=repository, commit=last_pipeline['commit'])
            PIPELINE_LAST_TARGET_BRANCH.labels(repository=repository, target_branch=last_pipeline['target_branch'])

def main():
    bitbucket_workspace = get_so_env('BITBUCKET_PIPELINES_EXPORTER_WORKSPACE')
    bitbucket_username = get_so_env('BITBUCKET_PIPELINES_EXPORTER_USERNAME')
    bitbucket_app_password = get_so_env('BITBUCKET_PIPELINES_EXPORTER_APP_PASSWORD')
    prometheus_metrics_interval = int(get_so_env('BITBUCKET_PIPELINES_EXPORTER_INTERVAL'))
    
    workspace_repositories = return_workspace_repositories(bitbucket_workspace, bitbucket_username, bitbucket_app_password)

    start_http_server(8000)
    print(f'{get_current_time()}: Prometheus metrics server running on port 8000')

    while True:
        update_metrics(bitbucket_workspace, bitbucket_username, bitbucket_app_password, workspace_repositories)
        time.sleep(prometheus_metrics_interval)


if __name__ == '__main__':
    main()