SHELL := /bin/bash
VERSION := $(strip $(shell cat ./VERSION))
FILE := teamcity_exporter.py
NAME := teamcity_exporter

# Change me
REGISTRY := registry.hub.docker.com
REGISTRY_PROJECT := exporters

.PHONY: docker-build docker-test docker-push

docker-build:
	docker build -t ${REGISTRY}/${REGISTRY_PROJECT}/${NAME}:${VERSION} ./

docker-test: docker-build
	docker run -p 9190:9190 --env-file docker.env ${REGISTRY}/${REGISTRY_PROJECT}/${NAME}:${VERSION}

docker-push: docker-build
	docker push ${REGISTRY}/${REGISTRY_PROJECT}/${NAME}:${VERSION}