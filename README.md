## Teamcity Prometheus Exporter

#### Required envs
* TE_API_LOGIN
* TE_API_PASSWORD
* TE_API_URL

###### example
* TE_API_LOGIN=teamcity_service
* TE_API_PASSWORD=$3(r3tp@$$
* TE_API_URL=http://teamcity.exmaple.com

#### Default envs
* TE_LISTEN_ADDRESS=0.0.0.0
* TE_LISTEN_PORT=9190
* TE_LOG_LEVEL=INFO

#### Exposed metrics
* teamcity_build_queue_length
* teamcity_agents_count
* teamcity_disabled_agents_count
* teamcity_unauthorized_agents_count
* teamcity_disconnected_agents_count
* teamcity_investigations_count
* teamcity_running_builds

#### Build and Test
```bash
make docker-build
```
Fill docker.env with actual params, then:

```bash
make docker-test

```