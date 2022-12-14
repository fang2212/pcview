# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: scene.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bscene.proto\x12\x11perception.common\"\x07\n\x05Scene*\x86\x01\n\x0bWeatherType\x12\x12\n\x0eWEATHER_NORMAL\x10\x00\x12\x13\n\x0fWEATHER_NORMAL2\x10\x01\x12\x11\n\rWEATHER_RAINY\x10\x02\x12\x11\n\rWEATHER_SNOWY\x10\x03\x12\x15\n\x11WEATHER_HEAVYRAIN\x10\x04\x12\x11\n\rWEATHER_OTHER\x10\x05*|\n\tSceneType\x12\x11\n\rSCENE_HIGHWAY\x10\x00\x12\x0f\n\x0bSCENE_URBAN\x10\x01\x12\x0f\n\x0bSCENE_RURAL\x10\x02\x12\x10\n\x0cSCENE_TUNNEL\x10\x03\x12\x0f\n\x0bSCENE_OTHER\x10\x05\x12\x17\n\x13SCENE_CHARGESTATION\x10\x04*8\n\x08TimeType\x12\x0c\n\x08TIME_DAY\x10\x00\x12\x0e\n\nTIME_NIGHT\x10\x01\x12\x0e\n\nTIME_OTHER\x10\x02*\x80\x01\n\tLightType\x12\x16\n\x12LIGHT_NATRUALLIGHT\x10\x00\x12\x13\n\x0fLIGHT_LAMPLIGHT\x10\x01\x12\x13\n\x0fLIGHT_HARDLIGHT\x10\x02\x12\x10\n\x0cLIGHT_LOWSUN\x10\x03\x12\x0e\n\nLIGHT_DARK\x10\x04\x12\x0f\n\x0bLIGHT_OTHER\x10\x05*|\n\x11WorkConditionType\x12\x1a\n\x16WORK_CONDITION_WEATHER\x10\x00\x12\x18\n\x14WORK_CONDITION_LIGHT\x10\x01\x12\x18\n\x14WORK_CONDITION_SCENE\x10\x02\x12\x17\n\x13WORK_CONDITION_TIME\x10\x03\x62\x06proto3')

_WEATHERTYPE = DESCRIPTOR.enum_types_by_name['WeatherType']
WeatherType = enum_type_wrapper.EnumTypeWrapper(_WEATHERTYPE)
_SCENETYPE = DESCRIPTOR.enum_types_by_name['SceneType']
SceneType = enum_type_wrapper.EnumTypeWrapper(_SCENETYPE)
_TIMETYPE = DESCRIPTOR.enum_types_by_name['TimeType']
TimeType = enum_type_wrapper.EnumTypeWrapper(_TIMETYPE)
_LIGHTTYPE = DESCRIPTOR.enum_types_by_name['LightType']
LightType = enum_type_wrapper.EnumTypeWrapper(_LIGHTTYPE)
_WORKCONDITIONTYPE = DESCRIPTOR.enum_types_by_name['WorkConditionType']
WorkConditionType = enum_type_wrapper.EnumTypeWrapper(_WORKCONDITIONTYPE)
WEATHER_NORMAL = 0
WEATHER_NORMAL2 = 1
WEATHER_RAINY = 2
WEATHER_SNOWY = 3
WEATHER_HEAVYRAIN = 4
WEATHER_OTHER = 5
SCENE_HIGHWAY = 0
SCENE_URBAN = 1
SCENE_RURAL = 2
SCENE_TUNNEL = 3
SCENE_OTHER = 5
SCENE_CHARGESTATION = 4
TIME_DAY = 0
TIME_NIGHT = 1
TIME_OTHER = 2
LIGHT_NATRUALLIGHT = 0
LIGHT_LAMPLIGHT = 1
LIGHT_HARDLIGHT = 2
LIGHT_LOWSUN = 3
LIGHT_DARK = 4
LIGHT_OTHER = 5
WORK_CONDITION_WEATHER = 0
WORK_CONDITION_LIGHT = 1
WORK_CONDITION_SCENE = 2
WORK_CONDITION_TIME = 3


_SCENE = DESCRIPTOR.message_types_by_name['Scene']
Scene = _reflection.GeneratedProtocolMessageType('Scene', (_message.Message,), {
  'DESCRIPTOR' : _SCENE,
  '__module__' : 'scene_pb2'
  # @@protoc_insertion_point(class_scope:perception.common.Scene)
  })
_sym_db.RegisterMessage(Scene)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _WEATHERTYPE._serialized_start=44
  _WEATHERTYPE._serialized_end=178
  _SCENETYPE._serialized_start=180
  _SCENETYPE._serialized_end=304
  _TIMETYPE._serialized_start=306
  _TIMETYPE._serialized_end=362
  _LIGHTTYPE._serialized_start=365
  _LIGHTTYPE._serialized_end=493
  _WORKCONDITIONTYPE._serialized_start=495
  _WORKCONDITIONTYPE._serialized_end=619
  _SCENE._serialized_start=34
  _SCENE._serialized_end=41
# @@protoc_insertion_point(module_scope)
