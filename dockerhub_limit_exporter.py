#!/usr/bin/env python3
#coding: utf-8

'''Docker Hub Limit Exporter'''

import logging
import os
import sys
import time
import requests
from prometheus_client.core import REGISTRY, Metric
from prometheus_client import start_http_server, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL = os.environ.get('DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL',
                                                   'INFO').upper()
DOCKERHUB_LIMIT_EXPORTER_NAME = os.environ.get('DOCKERHUB_LIMIT_EXPORTER_NAME',
                                               'dockerhub-limit-exporter')

HEADERS = [
   {'name': 'ratelimit-limit',
    'description': 'total number of pulls that can be performed within a six hour window',
    'type': 'gauge'},
   {'name': 'ratelimit-remaining',
    'description': 'number of pulls remaining for the six hour rolling window',
    'type': 'gauge'},
]

# Logging Configuration
try:
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level=DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL)
except ValueError:
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level='INFO')
    logging.error("DOCKERHUB_LIMIT_EXPORTER_LOGLEVEL invalid !")
    sys.exit(1)

# Exporter Configuration
try:
    DOCKERHUB_LIMIT_EXPORTER_PORT = int(os.environ.get('DOCKERHUB_LIMIT_EXPORTER_PORT', '8123'))
except ValueError:
    logging.error("DOCKERHUB_LIMIT_EXPORTER_PORT must be int !")
    sys.exit(1)

# Docker Hub Configuration
IMAGE = "ratelimitpreview/test"
DOCKERHUB_USERNAME = os.environ.get('DOCKERHUB_USERNAME')
DOCKERHUB_PASSWORD = os.environ.get('DOCKERHUB_PASSWORD')
REGISTRY_URL = f"https://registry-1.docker.io/v2/{IMAGE}/manifests/latest"
TOKEN_URL = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{IMAGE}:pull"

# REGISTRY Configuration
REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(REGISTRY._names_to_collectors['python_gc_objects_collected_total'])

# Docker Hub Limit Collector Class
class DockerHubLimitCollector():
    '''Docker Hub Limit Collector Class'''
    def __init__(self):
        return

    def get_limits(self):
        '''Get Docker Hub Limits'''
        limits = {}
        headers = {'Authorization': f'Bearer {self._get_token()}'}
        # Fetch Headers With HEAD Request & Avoid Pull Count
        request = requests.head(REGISTRY_URL, headers=headers)
        for key, value in request.headers.items():
            if key in [i['name'] for i in HEADERS]:
                limit, interval = self._parse_limit(value)
                limits[key] = limit
                limits[f'{key}-interval'] = interval
        logging.info(limits)
        return limits

    def collect(self):
        '''Collect Prometheus Metrics'''
        limits = self.get_limits()
        if DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD:
            labels = {'job': DOCKERHUB_LIMIT_EXPORTER_NAME,
                      'dockerhub_username': DOCKERHUB_USERNAME.lower()}
        else:
            labels = {'job': DOCKERHUB_LIMIT_EXPORTER_NAME,
                      'dockerhub_username': 'anonymous'}
        metrics = []
        for key, value in limits.items():
            if key in [i['name'] for i in HEADERS]:
                description = [i['description'] for i in HEADERS if key == i['name']][0]
                metric_type = [i['type'] for i in HEADERS if key == i['name']][0]
                if metric_type in ['counter', 'gauge', 'histogram', 'summary']:
                    metrics.append({'name': f'dockerhub_{key.lower().replace('-', '_')}',
                                    'value': int(value),
                                    'description': description,
                                    'type': metric_type})
            else:
                labels[key.lower().replace('-', '_')] = value

        # Return Prometheus Metrics
        for metric in metrics:
            prometheus_metric = Metric(metric['name'], metric['description'], metric['type'])
            prometheus_metric.add_sample(metric['name'], value=metric['value'], labels=labels)
            yield prometheus_metric

    @staticmethod
    def _get_token():
        '''Get Docker Hub Token'''
        if DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD:
            auth = (DOCKERHUB_USERNAME.lower(), DOCKERHUB_PASSWORD)
            request = requests.get(TOKEN_URL, auth=auth)
            if request.status_code == 401:
                logging.error("Invalid Docker Hub Credentials !")
                sys.exit(1)
        else:
            request = requests.get(TOKEN_URL)
        token = request.json()['token']
        logging.debug("TOKEN : %s", token)
        return token

    @staticmethod
    def _parse_limit(value):
        '''Extract Limit & Interval From Header'''
        limit, interval = value.split(';')
        return limit, interval.replace('w=', '')

if __name__ == '__main__':
    logging.info("Starting Docker Hub Limit Exporter on port %s.", DOCKERHUB_LIMIT_EXPORTER_PORT)
    logging.debug("DOCKERHUB_LIMIT_EXPORTER_PORT: %s.", DOCKERHUB_LIMIT_EXPORTER_PORT)
    logging.debug("DOCKERHUB_LIMIT_EXPORTER_NAME: %s.", DOCKERHUB_LIMIT_EXPORTER_NAME)
    if DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD:
        logging.info("Mode : LOGIN.")
    else:
        logging.info("Mode : ANONYMOUS.")
    # Start Prometheus HTTP Server
    start_http_server(DOCKERHUB_LIMIT_EXPORTER_PORT)
    # Init LinkyCollector
    REGISTRY.register(DockerHubLimitCollector())
    # Loop Infinity
    while True:
        time.sleep(1)
