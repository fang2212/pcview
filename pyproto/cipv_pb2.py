# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cipv.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ncipv.proto\x12\nperception\"\xc0\x01\n\x04\x43IPV\x12\x10\n\x08\x66rame_id\x18\x01 \x01(\x04\x12\x0c\n\x04tick\x18\x02 \x01(\x04\x12\x11\n\ttimestamp\x18\x03 \x01(\x04\x12\x12\n\nvehicle_id\x18\x04 \x01(\x05\x12\x16\n\x0elongitude_dist\x18\x05 \x01(\x02\x12\x14\n\x0clateral_dist\x18\x06 \x01(\x02\x12\x1b\n\x13rel_longitude_speed\x18\x07 \x01(\x02\x12\x19\n\x11rel_lateral_speed\x18\x08 \x01(\x02\x12\x0b\n\x03ttc\x18\t \x01(\x02\x62\x06proto3')



_CIPV = DESCRIPTOR.message_types_by_name['CIPV']
CIPV = _reflection.GeneratedProtocolMessageType('CIPV', (_message.Message,), {
  'DESCRIPTOR' : _CIPV,
  '__module__' : 'cipv_pb2'
  # @@protoc_insertion_point(class_scope:perception.CIPV)
  })
_sym_db.RegisterMessage(CIPV)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CIPV._serialized_start=27
  _CIPV._serialized_end=219
# @@protoc_insertion_point(module_scope)
