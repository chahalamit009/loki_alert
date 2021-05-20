# loki_slack
This app targets to make a better view of looking at loki alert in the flask webapp and then sending loki alerts to slack and linking back it to grafana.

# Screenshot

# Deployment Instructions

The webapp can be deployed directly via flask and also on Kubernetes via Dockerfile

Add your configurations to the config.py file.

- Things to be set as enviornment variales:\
  ```redis_host```\
  ```redis_port```\
  ```landing_url``` - The URL where your webapp will be hosted

- Run it directly via python server locally

  ```python index.py```

- Run it via dockerfile

  ```Docker build --tag loki_slack```\
  ```docker run -i loki_slack```


