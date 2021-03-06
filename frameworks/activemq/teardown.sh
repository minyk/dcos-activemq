#!/usr/bin/env bash
set -e -x

frameworkid=${1}

echo "Remove app /activemq"
curl -XDELETE "http://172.17.0.2/marathon/v2/apps/activemq"
curl -XPOST "http://172.17.0.2/mesos/master/teardown" -d"frameworkId=${frameworkid}"
curl -XDELETE "http://172.17.0.2/exhibitor/exhibitor/v1/explorer/znode/dcos-service-activemq"