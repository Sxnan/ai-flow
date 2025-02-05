#!/usr/bin/env bash
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
set -e

coverage run -p \
  --source="ai_flow" \
  --omit="ai_flow/test/*,ai_flow/protobuf/*" \
  --branch \
  -m unittest discover -v ai_flow/test

coverage run -p \
  --source="ai_flow_plugins" \
  --omit="ai_flow_plugins/tests/*" \
  --branch \
  -m unittest discover -v ai_flow_plugins/tests

coverage run -p \
  --source="lib/notification_service" \
  --omit="lib/notification_service/tests/*,lib/notification_service/notification_service/proto/*" \
  --branch \
  -m unittest discover -v lib/notification_service/tests

coverage combine
coverage report
coverage xml
