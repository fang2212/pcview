# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gnssvel.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rgnssvel.proto\x12\x07minieye\"\xcd\x02\n\x0bGnssvelData\x12\n\n\x02id\x18\x01 \x01(\x04\x12\x0b\n\x03seq\x18\x02 \x01(\x04\x12\x11\n\ttimestamp\x18\x03 \x01(\x04\x12\x0c\n\x04tick\x18\x04 \x01(\x04\x12\x10\n\x08is_valid\x18\x05 \x01(\x08\x12\x10\n\x08gps_week\x18\x06 \x01(\r\x12\x0f\n\x07gps_sec\x18\x07 \x01(\x01\x12\x12\n\nsol_status\x18\x08 \x01(\r\x12\x10\n\x08vel_type\x18\t \x01(\r\x12\x0f\n\x07hor_spd\x18\n \x01(\x02\x12\x10\n\x08vert_spd\x18\x0b \x01(\x02\x12\x0f\n\x07trk_gnd\x18\x0c \x01(\x02\x12\x0f\n\x07latency\x18\r \x01(\x02\x12\r\n\x05vel_x\x18\x0e \x01(\x02\x12\r\n\x05vel_y\x18\x0f \x01(\x02\x12\r\n\x05vel_z\x18\x10 \x01(\x02\x12\x11\n\tvel_x_std\x18\x11 \x01(\x02\x12\x11\n\tvel_y_std\x18\x12 \x01(\x02\x12\x11\n\tvel_z_std\x18\x13 \x01(\x02\x62\x06proto3')



_GNSSVELDATA = DESCRIPTOR.message_types_by_name['GnssvelData']
GnssvelData = _reflection.GeneratedProtocolMessageType('GnssvelData', (_message.Message,), {
  'DESCRIPTOR' : _GNSSVELDATA,
  '__module__' : 'gnssvel_pb2'
  # @@protoc_insertion_point(class_scope:minieye.GnssvelData)
  })
_sym_db.RegisterMessage(GnssvelData)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GNSSVELDATA._serialized_start=27
  _GNSSVELDATA._serialized_end=360
# @@protoc_insertion_point(module_scope)
