#!/bin/bash

if [ -z "${NODE_ID}" ]; then
    echo "SET NODE ID"
    exit 1
fi

python3 nodev2.py