#!/usr/bin/env bash
rm -f *.zip
rm -f *.tar.gz

FRAMEWORK_DIR="$( dirname $(pwd) )"
REPO_ROOT_DIR=$(dirname $(dirname $FRAMEWORK_DIR))

echo "Get compiled bits"
cp $FRAMEWORK_DIR/build/distributions/$(basename $FRAMEWORK_DIR)-scheduler.zip .
cp $REPO_ROOT_DIR/sdk/executor/build/distributions/executor.zip .
cp $REPO_ROOT_DIR/sdk/bootstrap/bootstrap.zip .

echo "Download JRE and libmesos"
curl -L https://downloads.mesosphere.com/java/jre-8u152-linux-x64.tar.gz -o jre-8u152-linux-x64.tar.gz
curl -L https://downloads.mesosphere.io/libmesos-bundle/libmesos-bundle-master-28f8827.tar.gz -o libmesos-bundle-master-28f8827.tar.gz
