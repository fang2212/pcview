# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ins.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import data_header_pb2 as data__header__pb2
import geometry_pb2 as geometry__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tins.proto\x12\x07minieye\x1a\x11\x64\x61ta_header.proto\x1a\x0egeometry.proto\"\xc8\x03\n\x07InsData\x12\x1f\n\x06header\x18\x01 \x01(\x0b\x32\x0f.minieye.Header\x12\x10\n\x08is_valid\x18\x02 \x01(\x08\x12\x10\n\x08gps_week\x18\x03 \x01(\r\x12\x0f\n\x07gps_sec\x18\x04 \x01(\x01\x12\x10\n\x08latitude\x18\x05 \x01(\x01\x12\x11\n\tlongitude\x18\x06 \x01(\x01\x12\x11\n\televation\x18\x07 \x01(\x01\x12,\n\x08\x61ttitude\x18\x08 \x01(\x0b\x32\x1a.perception.common.Point3f\x12\x33\n\x0flinear_velocity\x18\t \x01(\x0b\x32\x1a.perception.common.Point3f\x12/\n\x0bsd_position\x18\n \x01(\x0b\x32\x1a.perception.common.Point3f\x12/\n\x0bsd_attitude\x18\x0b \x01(\x0b\x32\x1a.perception.common.Point3f\x12/\n\x0bsd_velocity\x18\x0c \x01(\x0b\x32\x1a.perception.common.Point3f\x12\x12\n\nsys_status\x18\r \x01(\r\x12\x12\n\ngps_status\x18\x0e \x01(\r\x12\x11\n\twarn_info\x18\x0f \x01(\rb\x06proto3')



_INSDATA = DESCRIPTOR.message_types_by_name['InsData']
InsData = _reflection.GeneratedProtocolMessageType('InsData', (_message.Message,), {
  'DESCRIPTOR' : _INSDATA,
  '__module__' : 'ins_pb2'
  # @@protoc_insertion_point(class_scope:minieye.InsData)
  })
_sym_db.RegisterMessage(InsData)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _INSDATA._serialized_start=58
  _INSDATA._serialized_end=514
# @@protoc_insertion_point(module_scope)
