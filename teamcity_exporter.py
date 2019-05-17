#!/usr/bin/python
# Author: Artem Shepelev <shepelev.artem@gmail.com>
# Version: 0.1
# Modification date: 2019-05-17
# This script collects several metrics from TeamCity Server

import base64
import logging
import sys
import time
import urllib2
import json
import os
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.core import REGISTRY

# Metric map for each metric we collect from TeamCity
# Includes:
# metric name
# metric description
# API URL to collect metric
# metric key which determines which dictionary key of the output to use
metric_map = {
    "teamcity_build_queue_length": {
        "name": "teamcity_build_queue_length",
        "description": "TeamCity Build Queue Length",
        "api_url": "/app/rest/buildQueue",
        "metric_key": "count"
    },
    "teamcity_agents_count": {
        "name": "teamcity_agents_count",
        "description": "TeamCity Agents Count",
        "api_url": "/app/rest/agents",
        "metric_key": "count",
    },
    "teamcity_disabled_agents_count": {
        "name": "teamcity_disabled_agents_count",
        "description": "TeamCity Disabled Agents Count",
        "api_url": "/app/rest/agents?locator=enabled:false",
        "metric_key": "count",
    },
    "teamcity_unauthorized_agents_count": {
        "name": "teamcity_unauthorized_agents_count",
        "description": "TeamCity Unauthorized Agents Count",
        "api_url": "/app/rest/agents?locator=authorized:false",
        "metric_key": "count",
    },
    "teamcity_disconnected_agents_count": {
        "name": "teamcity_disconnected_agents_count",
        "description": "TeamCity Disconnected Agents Count",
        "api_url": "/app/rest/agents?locator=connected:false",
        "metric_key": "count",
    },
    "teamcity_investigations_count": {
        "name": "teamcity_investigations_count",
        "description": "TeamCity Investigations Count",
        "api_url": "/app/rest/investigations",
        "metric_key": "count"
    },
    "teamcity_running_builds": {
        "name": "teamcity_running_builds",
        "description": "TeamCity Running Builds",
        "api_url": "/app/rest/builds?locator=running:true",
        "metric_key": "count"
    },
    "teamcity_hanging_builds": {
        "name": "teamcity_hanging_builds",
        "description": "TeamCity Hanging Builds",
        "api_url": "/app/rest/builds?locator=state:running,hanging:true",
        "metric_key": "count"
    }
    # # Uncomment in 2017.2
    # "teamcity_muted_tests_and_build_problems_count": {
    #     "name": "teamcity_muted_tests_and_build_problems_count",
    #     "description": "TeamCity Muted Tests and Build Problems",
    #     "api_url": "/app/rest/mutes",
    #     "metric_key": "count",
    # }
}

logger = logging.getLogger('teamcity-exporter')

# Default params which can be changed
TE_LISTEN_ADDRESS = os.environ['TE_LISTEN_ADDRESS'] if "TE_LISTEN_ADDRESS" in os.environ else "0.0.0.0"
TE_LISTEN_PORT = os.environ['TE_LISTEN_PORT'] if "TE_LISTEN_PORT" in os.environ else 9190
TE_LOG_LEVEL = os.environ['TE_LOG_LEVEL'] if "TE_LOG_LEVEL" in os.environ else "ERROR"

# Sets up DEBUG, INFO and ERROR log levels
def setup_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if TE_LOG_LEVEL == "DEBUG":
        logger.setLevel(logging.DEBUG) # Handles debug only with logger default level set to default
        debug_logger = logging.StreamHandler(sys.stdout)
        debug_logger.setLevel(logging.DEBUG)
        debug_logger.setFormatter(formatter)
        logger.addHandler(debug_logger)
    error_logger = logging.StreamHandler(sys.stderr)
    error_logger.setLevel(logging.ERROR)
    error_logger.setFormatter(formatter)
    logger.addHandler(error_logger)

    info_logger = logging.StreamHandler(sys.stdout)
    info_logger.setLevel(logging.INFO)
    info_logger.setFormatter(formatter)
    logger.addHandler(info_logger)

# Wrapper class for collector object
class TeamcityCollector(object):
    def __init__(self, login, password, server, port=80):
        self.login = login
        self.password = password
        self.server = server
        self.port = port
    # Needs a collect method to be defined. This method needs to yield metrics
    def collect(self):
        # Password header
        base64string = base64.b64encode('%s:%s' % (self.login, self.password))
        # Server URL
        serverurl = self.server+":"+str(self.port)
        scrape_error = lambda sample: GaugeMetricFamily("teamcity_scrape_error", "If exporter was able to call API methods", value=sample)
        for metric, params in metric_map.iteritems():
            # Creating the request
            request = urllib2.Request(serverurl + params["api_url"])
            request.add_header("Authorization", "Basic %s" % base64string)
            request.add_header("Accept", "application/json")
            # Sending the request
            logger.debug("Sending URL request: {0}".format(serverurl + params["api_url"]))
            try:
                result = urllib2.urlopen(request)
            except:
                logger.error("Error sending request {0}".format(serverurl + params["api_url"]))
                yield scrape_error(1)
                return
            try:
                json_result = json.loads(result.read())
            except:
                logger.error("Error parsing JSON response for request: {0}".format(serverurl + params["api_url"]))
                continue
            logger.debug("Received answer: {0}".format(str(json_result)))
            # Creating Gauge with metric value and yielding it
            func = lambda sample: GaugeMetricFamily(params["name"], params["description"], value=sample)
            try:
                value = json_result[params["metric_key"]]
            except:
                logger.error("Error parsing metric value.String: {0} Request: {1}  MetricKey: {2}".format(str(json_result),
                    serverurl + params["api_url"],params["metric_key"]))
                continue
            yield func(value)
        yield scrape_error(0)

def main():
    setup_logger()
    # Reading credentials and teamcity URL
    logger.debug("Getting API credenetials and TeamCity URL")
    if "TE_API_LOGIN" in os.environ:
        TE_API_LOGIN = os.environ['TE_API_LOGIN']
    else:
        logger.error("TE_API_LOGIN env not defined")
        sys.exit(1)

    if "TE_API_PASSWORD" in os.environ:
        TE_API_PASSWORD = os.environ['TE_API_PASSWORD']
    else:
        logger.error("TE_API_PASSWORD env not defined")
        sys.exit(1)

    if "TE_API_URL" in os.environ:
        TE_API_URL = os.environ['TE_API_URL']
    else:
        logger.error("TE_API_URL env not defined")
        sys.exit(1)
    TE_API_URL = TE_API_URL.strip("/")

    # Registering metrics collector and starting http server to process requests
    REGISTRY.register(TeamcityCollector(TE_API_LOGIN, TE_API_PASSWORD, TE_API_URL))
    try:
        start_http_server(port=int(TE_LISTEN_PORT), addr=TE_LISTEN_ADDRESS)
    except:
        logger.error("An error occured while starting HTTP Listener")
        sys.exit(1)
    logger.info("Starting listening on {0}:{1}".format(TE_LISTEN_ADDRESS,TE_LISTEN_PORT))
    while True: time.sleep(1)

if __name__ == '__main__':
    main()