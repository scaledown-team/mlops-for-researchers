# Prefect Setup

Prefect is an orchestrator that helps you schedule and run tasks in an environment. You can use prefect to run tasks using kubernetes, or in the location where the prefect server and prefect agent is running.

You can start prefect using either the docker file or using the command below. An issue with using docker to run prefect is that you can then not run docker containers in prefect due to the docker-in-docker issue. We suggest running prefect using the command below. To have prefect persist running in a remote environment, you can use `nohup` or `tmux`.

```bash
pip install prefect
prefect server start --host=0.0.0.0
```
