# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from airflow.executors.scheduling_action import SchedulingAction
from airflow.utils import dates
from enum import Enum
from notification_service.base_notification import BaseEvent
import json

EXECUTION_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class SchedulerInnerEventType(Enum):
    STOP_SCHEDULER = 'STOP_SCHEDULER'
    TASK_STATUS_CHANGED = 'TASK_STATUS_CHANGED'
    TASK_SCHEDULING = 'TASK_SCHEDULING'
    DAG_EXECUTABLE = 'DAG_EXECUTABLE'
    EVENT_HANDLE = 'EVENT_HANDLE'
    REQUEST = 'REQUEST'
    RESPONSE = 'RESPONSE'


class SchedulerInnerEvent(object):

    @classmethod
    def to_base_event(cls, event: 'SchedulerInnerEvent') -> BaseEvent:
        raise NotImplementedError()

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'SchedulerInnerEvent':
        raise NotImplementedError()

    def to_event(self) -> BaseEvent:
        return self.to_base_event(self)


class UserDefineMessageType(Enum):
    RUN_DAG = 'RUN_DAG'
    STOP_DAG_RUN = 'STOP_DAG_RUN'
    EXECUTE_TASK = 'EXECUTE_TASK'


class BaseUserDefineMessage(object):
    def __init__(self, message_type: UserDefineMessageType = None):
        self.message_type = message_type
        
    def to_json(self) -> str:
        o = {}
        for k, v in self.__dict__.items():
            if k == 'message_type':
                o[k] = v.value
            else:
                o[k] = v
        return json.dumps(o)

    def from_json(self, json_str):
        o = json.loads(json_str)
        for k, v in o.items():
            if k == 'message_type':
                self.__dict__[k] = UserDefineMessageType(v)
            else:
                self.__dict__[k] = v


class RunDagMessage(BaseUserDefineMessage):
    def __init__(self, dag_id):
        super().__init__(UserDefineMessageType.RUN_DAG)
        self.dag_id = dag_id
        
        
class StopDagRunMessage(BaseUserDefineMessage):
    def __init__(self, dagrun_id):
        super().__init__(UserDefineMessageType.RUN_DAG)
        self.dagrun_id = dagrun_id
        
        
class ExecuteTaskMessage(BaseUserDefineMessage):
    def __init__(self, dagrun_id, task_id, action):
        super().__init__(UserDefineMessageType.EXECUTE_TASK)
        self.dagrun_id = dagrun_id
        self.task_id = task_id
        self.action = action


class RequestEvent(SchedulerInnerEvent):
    def __init__(self, request_id, body):
        self.request_id = request_id
        self.body = body

    @classmethod
    def to_base_event(cls, event: 'RequestEvent') -> BaseEvent:
        return BaseEvent(key=str(event.request_id), value=event.body, event_type=SchedulerInnerEventType.REQUEST.value)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'SchedulerInnerEvent':
        return RequestEvent(event.key, event.value)


class ResponseEvent(SchedulerInnerEvent):
    def __init__(self, request_id, body):
        self.request_id = request_id
        self.body = body

    @classmethod
    def to_base_event(cls, event: 'ResponseEvent') -> BaseEvent:
        return BaseEvent(key=str(event.request_id), value=event.body, event_type=SchedulerInnerEventType.RESPONSE.value)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'SchedulerInnerEvent':
        return ResponseEvent(event.key, event.value)


class StopSchedulerEvent(SchedulerInnerEvent):
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id

    @classmethod
    def to_base_event(cls, event: 'StopSchedulerEvent') -> BaseEvent:
        return BaseEvent(key=str(event.job_id), value='', event_type=SchedulerInnerEventType.STOP_SCHEDULER.value)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'SchedulerInnerEvent':
        return StopSchedulerEvent(int(event.key))


class TaskStatusChangedEvent(SchedulerInnerEvent):

    def __init__(self, task_id, dag_id, execution_date, status):
        super().__init__()
        self.task_id = task_id
        self.dag_id = dag_id
        self.execution_date = execution_date
        self.status = status

    @classmethod
    def to_base_event(cls, event: 'TaskStatusChangedEvent') -> BaseEvent:
        o = {}
        for k, v in event.__dict__.items():
            if 'execution_date' == k:
                o[k] = v.strftime(EXECUTION_DATE_FORMAT)
            else:
                o[k] = v
        return BaseEvent(key=event.dag_id,
                         value=json.dumps(o),
                         event_type=SchedulerInnerEventType.TASK_STATUS_CHANGED.value,
                         namespace=event.dag_id)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'TaskStatusChangedEvent':
        o = json.loads(event.value)
        return TaskStatusChangedEvent(task_id=o['task_id'],
                                      dag_id=o['dag_id'],
                                      execution_date=dates.parse_execution_date(o['execution_date']),
                                      status=o['status'])


class DagExecutableEvent(SchedulerInnerEvent):
    def __init__(self, dag_id):
        super().__init__()
        self.dag_id = dag_id

    @classmethod
    def to_base_event(cls, event: 'DagExecutableEvent') -> BaseEvent:
        return BaseEvent(key=event.dag_id, value='', event_type=SchedulerInnerEventType.DAG_EXECUTABLE.value,
                         namespace=event.dag_id)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'DagExecutableEvent':
        return DagExecutableEvent(dag_id=event.key)


class TaskSchedulingEvent(SchedulerInnerEvent):
    def __init__(self, task_id, dag_id, execution_date, try_number, action: SchedulingAction):
        super().__init__()
        self.task_id = task_id
        self.dag_id = dag_id
        self.execution_date = execution_date
        self.try_number = try_number
        self.action = action

    @classmethod
    def to_base_event(cls, event: 'TaskSchedulingEvent') -> BaseEvent:
        o = {}
        for k, v in event.__dict__.items():
            if 'execution_date' == k:
                o[k] = v.strftime(EXECUTION_DATE_FORMAT)
            elif 'action' == k:
                o[k] = v.value
            else:
                o[k] = v
        return BaseEvent(key=event.dag_id,
                         value=json.dumps(o),
                         event_type=SchedulerInnerEventType.TASK_SCHEDULING.value,
                         namespace=event.dag_id)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'TaskSchedulingEvent':
        o = json.loads(event.value)
        return TaskSchedulingEvent(task_id=o['task_id'],
                                   dag_id=o['dag_id'],
                                   execution_date=dates.parse_execution_date(o['execution_date']),
                                   try_number=int(o['try_number']),
                                   action=SchedulingAction(o['action']))


class EventHandleEvent(SchedulerInnerEvent):
    def __init__(self, dag_id, dag_run_id, task_id, action: SchedulingAction):
        super().__init__()
        self.task_id = task_id
        self.dag_id = dag_id
        self.dag_run_id = dag_run_id
        self.action = action

    @classmethod
    def to_base_event(cls, event: 'EventHandleEvent') -> BaseEvent:
        o = {}
        for k, v in event.__dict__.items():
            if 'action' == k:
                o[k] = v.value
            else:
                o[k] = v
        return BaseEvent(key=event.dag_id,
                         value=json.dumps(o),
                         event_type=SchedulerInnerEventType.EVENT_HANDLE.value,
                         namespace=event.dag_id)

    @classmethod
    def from_base_event(cls, event: BaseEvent) -> 'EventHandleEvent':
        o = json.loads(event.value)
        return EventHandleEvent(task_id=o['task_id'],
                                dag_run_id=o['dag_run_id'],
                                dag_id=o['dag_id'],
                                action=SchedulingAction(o['action']))


class SchedulerInnerEventUtil(object):
    @staticmethod
    def is_inner_event(event: BaseEvent) -> bool:
        try:
            SchedulerInnerEventType(event.event_type)
            return True
        except ValueError as e:
            return False

    @staticmethod
    def event_type(event: BaseEvent) -> SchedulerInnerEventType:
        try:
            return SchedulerInnerEventType(event.event_type)
        except ValueError as e:
            return None

    @staticmethod
    def to_inner_event(event: BaseEvent) -> SchedulerInnerEvent:
        event_type = SchedulerInnerEventUtil.event_type(event)
        if SchedulerInnerEventType.STOP_SCHEDULER == event_type:
            return StopSchedulerEvent.from_base_event(event)
        elif SchedulerInnerEventType.TASK_SCHEDULING == event_type:
            return TaskSchedulingEvent.from_base_event(event)
        elif SchedulerInnerEventType.TASK_STATUS_CHANGED == event_type:
            return TaskStatusChangedEvent.from_base_event(event)
        elif SchedulerInnerEventType.DAG_EXECUTABLE == event_type:
            return DagExecutableEvent.from_base_event(event)
        elif SchedulerInnerEventType.EVENT_HANDLE == event_type:
            return EventHandleEvent.from_base_event(event)
        elif SchedulerInnerEventType.REQUEST == event_type:
            return RequestEvent.from_base_event(event)
        elif SchedulerInnerEventType.RESPONSE == event_type:
            return ResponseEvent.from_base_event(event)
        else:
            return None
