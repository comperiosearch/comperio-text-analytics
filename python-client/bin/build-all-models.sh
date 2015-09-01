#!/usr/bin/env bash

# Builds all the models for Norwegian NLP functionality and places them in the default locations

SELF_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

mkdir -p ${SELF_DIR}\..\..\models

python ${SELF_DIR}\build_no_tagger.py -m ${SELF_DIR}\..\..\models\no-tagger-default-model --features simple
