# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: odometry.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0eodometry.proto\x12\x07minieye\"\xf5\x03\n\x0cOdometryPose\x12\x11\n\ttimestamp\x18\x01 \x01(\x04\x12\x0c\n\x04tick\x18\x02 \x01(\x04\x12\r\n\x05pitch\x18\x03 \x01(\x02\x12\x11\n\tpitch_var\x18\x04 \x01(\x02\x12\x16\n\x0eis_pitch_valid\x18\x05 \x01(\x08\x12\x0b\n\x03rot\x18\x06 \x03(\x02\x12\x0b\n\x03pos\x18\x07 \x03(\x02\x12\x0b\n\x03vel\x18\x08 \x03(\x02\x12\x0f\n\x07imu_acc\x18\t \x03(\x02\x12\x0f\n\x07imu_gyr\x18\n \x03(\x02\x12\n\n\x02\x62\x61\x18\x0b \x03(\x02\x12\n\n\x02\x62g\x18\x0c \x03(\x02\x12\n\n\x02vx\x18\r \x01(\x02\x12\x0e\n\x06vx_var\x18\x0e \x01(\x02\x12\x13\n\x0bis_vx_valid\x18\x0f \x01(\x08\x12\n\n\x02\x61x\x18\x10 \x01(\x02\x12\x0e\n\x06\x61x_var\x18\x11 \x01(\x02\x12\x13\n\x0bis_ax_valid\x18\x12 \x01(\x08\x12\x10\n\x08yaw_rate\x18\x13 \x01(\x02\x12\x14\n\x0cyaw_rate_var\x18\x14 \x01(\x02\x12\x19\n\x11is_yaw_rate_valid\x18\x15 \x01(\x08\x12\x12\n\npitch_rate\x18\x16 \x01(\x02\x12\x16\n\x0epitch_rate_var\x18\x17 \x01(\x02\x12\x1b\n\x13is_pitch_rate_valid\x18\x18 \x01(\x08\x12\x0e\n\x06\x63\x61n_ax\x18\x19 \x01(\x02\x12\x12\n\ncan_ax_var\x18\x1a \x01(\x02\x12\x17\n\x0fis_can_ax_valid\x18\x1b \x01(\x08\"7\n\x08Odometry\x12+\n\x0cpredict_pose\x18\x01 \x03(\x0b\x32\x15.minieye.OdometryPose\"\xa9\x01\n\tEgoMotion\x12\x11\n\tspeed_mps\x18\x01 \x01(\x02\x12\x14\n\x0cis_imu_valid\x18\x02 \x01(\x08\x12\x0c\n\x04\x64yaw\x18\x03 \x01(\x02\x12\x15\n\ris_dyaw_valid\x18\x04 \x01(\x08\x12\x0e\n\x06\x64pitch\x18\x05 \x01(\x02\x12\x17\n\x0fis_dpitch_valid\x18\x06 \x01(\x08\x12\r\n\x05\x64t_ms\x18\x07 \x01(\x05\x12\x16\n\x0e\x63urr_timestamp\x18\x08 \x01(\x04\x62\x06proto3')



_ODOMETRYPOSE = DESCRIPTOR.message_types_by_name['OdometryPose']
_ODOMETRY = DESCRIPTOR.message_types_by_name['Odometry']
_EGOMOTION = DESCRIPTOR.message_types_by_name['EgoMotion']
OdometryPose = _reflection.GeneratedProtocolMessageType('OdometryPose', (_message.Message,), {
  'DESCRIPTOR' : _ODOMETRYPOSE,
  '__module__' : 'odometry_pb2'
  # @@protoc_insertion_point(class_scope:minieye.OdometryPose)
  })
_sym_db.RegisterMessage(OdometryPose)

Odometry = _reflection.GeneratedProtocolMessageType('Odometry', (_message.Message,), {
  'DESCRIPTOR' : _ODOMETRY,
  '__module__' : 'odometry_pb2'
  # @@protoc_insertion_point(class_scope:minieye.Odometry)
  })
_sym_db.RegisterMessage(Odometry)

EgoMotion = _reflection.GeneratedProtocolMessageType('EgoMotion', (_message.Message,), {
  'DESCRIPTOR' : _EGOMOTION,
  '__module__' : 'odometry_pb2'
  # @@protoc_insertion_point(class_scope:minieye.EgoMotion)
  })
_sym_db.RegisterMessage(EgoMotion)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ODOMETRYPOSE._serialized_start=28
  _ODOMETRYPOSE._serialized_end=529
  _ODOMETRY._serialized_start=531
  _ODOMETRY._serialized_end=586
  _EGOMOTION._serialized_start=589
  _EGOMOTION._serialized_end=758
# @@protoc_insertion_point(module_scope)
