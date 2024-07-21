# bitbucket-pipelines-exporter
Prometheus exporter to visualize status of Bitbucket pipelines
# Bitbucket Pipelines Prometheus Exporter

<p align="left">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Prometheus_software_logo.svg/1200px-Prometheus_software_logo.svg.png" alt="Prometheus Logo" width="100"/>
  <img src="https://upload.wikimedia.org/wikipedia/commons/f/fc/Bitbucket_Logo.png" alt="Bitbucket Logo" width="400"/>
</p>

## Introduction
This Docker image is a Prometheus exporter for Bitbucket Pipelines, designed to provide key metrics from your Pipeline executions.

## Why This Project?
Created because Bitbucket does not have an integrated view/page to view the Runners (self-hosted build agents) build queue.

## Features
Metrics exposed include:
- **`build_number`**: Numeric identifier of the build.
- **`state_name`**: Current state of the pipeline, possible values are `IN_PROGRESS`, `COMPLETED`, and `STOPPED`.
- **`state_result`**: Result of the pipeline execution which varies based on `state_name`:
  - When `IN_PROGRESS`, it can be `PAUSED` or `RUNNING`.
  - When `COMPLETED`, results include `SUCCESSFUL`, `FAILED`, and `ERROR`.
  - `STOPPED` does not have an associated result.
- **`duration_in_seconds`**: Execution time of the pipeline.
- **`creator_name`**: User who initiated the pipeline.
- **`commit`**: URL to the associated commit.
- **`target_branch`**: Branch target of the pipeline run.

## How to Use

### Docker Command
Run the container with the following command to expose metrics on port 8000:

```bash
docker run -p 8000:8000
-e BITBUCKET_PIPELINES_EXPORTER_WORKSPACE=$your_workspace_name
-e BITBUCKET_PIPELINES_EXPORTER_USERNAME=$your_username
-e BITBUCKET_PIPELINES_EXPORTER_APP_PASSWORD=$your_app_password
-e BITBUCKET_PIPELINES_EXPORTER_INTERVAL=$seconds
gmaas2/bitbucket-pipelines-prometheus-exporter:latest
```

## Configuration
Ensure your environment variables are set correctly. Each variable corresponds to necessary Bitbucket credentials and configurations for fetching pipeline data.

## Visualize Metrics

To test the exporter and see the metrics being exposed, open your web browser and navigate to `http://localhost:8000` and see something like this:

```yaml
# HELP pipeline_duration_seconds Duration of pipeline builds
# TYPE pipeline_duration_seconds gauge
pipeline_duration_seconds{repository="coruscant-analytics",state="IN_PROGRESS"} 187.0
pipeline_duration_seconds{repository="dantooine-base",state="COMPLETED"} 45.0
pipeline_duration_seconds{repository="endor-station",state="IN_PROGRESS"} 223.0

# HELP pipeline_last_build_number Last build number
# TYPE pipeline_last_build_number gauge
pipeline_last_build_number{repository="coruscant-analytics"} 149.0
pipeline_last_build_number{repository="dantooine-base"} 24.0
pipeline_last_build_number{repository="endor-station"} 6.0

# HELP pipeline_last_result Last build result as a label
# TYPE pipeline_last_result gauge
pipeline_last_result{repository="coruscant-analytics",result="PAUSED"} 1.0
pipeline_last_result{repository="dantooine-base",result="SUCCESSFUL"} 1.0
pipeline_last_result{repository="endor-station",result="PAUSED"} 1.0

# HELP pipeline_last_creator_info Last creator Name
# TYPE pipeline_last_creator_info gauge
pipeline_last_creator_info{creator_name="Leia Organa",repository="coruscant-analytics"} 1.0
pipeline_last_creator_info{creator_name="Han Solo",repository="dantooine-base"} 1.0
pipeline_last_creator_info{creator_name="Luke Skywalker",repository="endor-station"} 1.0

# HELP pipeline_last_commit_info Last commit that triggered the pipeline
# TYPE pipeline_last_commit_info gauge
pipeline_last_commit_info{commit="https://bitbucket.org/swprojects/15bab122a178",repository="coruscant-analytics"} 1.0
pipeline_last_commit_info{commit="https://bitbucket.org/swprojects/0c7a0ba3bb10",repository="dantooine-base"} 1.0
pipeline_last_commit_info{commit="https://bitbucket.org/swprojects/d342fa2cee7f",repository="endor-station"} 1.0

# HELP pipeline_last_target_branch_info Last branch selected to start the pipeline
# TYPE pipeline_last_target_branch_info gauge
pipeline_last_target_branch_info{repository="coruscant-analytics",target_branch="dev"} 1.0
pipeline_last_target_branch_info{repository="dantooine-base",target_branch="main"} 1.0
pipeline_last_target_branch_info{repository="endor-station",target_branch="dev"} 1.0

```

## Prometheus Configuration
Configure Prometheus to scrape this exporter by adding it to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'bitbucket_pipelines'
    scrape_interval: '3 minutes'
    static_configs:
      - targets: ['localhost:8000']
```

## Grafana Dashboard
TODO :/