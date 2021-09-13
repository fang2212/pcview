# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: odometry.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='odometry.proto',
  package='minieye',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0eodometry.proto\x12\x07minieye\"\xca\x01\n\x0cOdometryPose\x12\x11\n\ttimestamp\x18\x01 \x01(\x04\x12\r\n\x05pitch\x18\x02 \x01(\x02\x12\x11\n\tpitch_var\x18\x03 \x01(\x02\x12\x16\n\x0eis_pitch_valid\x18\x04 \x01(\x08\x12\x0b\n\x03rot\x18\x05 \x03(\x02\x12\x0b\n\x03pos\x18\x06 \x03(\x02\x12\x0b\n\x03vel\x18\x07 \x03(\x02\x12\x0f\n\x07imu_acc\x18\x08 \x03(\x02\x12\x0f\n\x07imu_gyr\x18\t \x03(\x02\x12\n\n\x02\x62\x61\x18\n \x03(\x02\x12\n\n\x02\x62g\x18\x0b \x03(\x02\x12\x0c\n\x04tick\x18\x0c \x01(\x04\"c\n\x08Odometry\x12*\n\x0b\x66ilter_pose\x18\x01 \x01(\x0b\x32\x15.minieye.OdometryPose\x12+\n\x0cpredict_pose\x18\x02 \x01(\x0b\x32\x15.minieye.OdometryPoseb\x06proto3'
)




_ODOMETRYPOSE = _descriptor.Descriptor(
  name='OdometryPose',
  full_name='minieye.OdometryPose',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='minieye.OdometryPose.timestamp', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pitch', full_name='minieye.OdometryPose.pitch', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pitch_var', full_name='minieye.OdometryPose.pitch_var', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='is_pitch_valid', full_name='minieye.OdometryPose.is_pitch_valid', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rot', full_name='minieye.OdometryPose.rot', index=4,
      number=5, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pos', full_name='minieye.OdometryPose.pos', index=5,
      number=6, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='vel', full_name='minieye.OdometryPose.vel', index=6,
      number=7, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='imu_acc', full_name='minieye.OdometryPose.imu_acc', index=7,
      number=8, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='imu_gyr', full_name='minieye.OdometryPose.imu_gyr', index=8,
      number=9, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ba', full_name='minieye.OdometryPose.ba', index=9,
      number=10, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='bg', full_name='minieye.OdometryPose.bg', index=10,
      number=11, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tick', full_name='minieye.OdometryPose.tick', index=11,
      number=12, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=28,
  serialized_end=230,
)


_ODOMETRY = _descriptor.Descriptor(
  name='Odometry',
  full_name='minieye.Odometry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='filter_pose', full_name='minieye.Odometry.filter_pose', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='predict_pose', full_name='minieye.Odometry.predict_pose', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=232,
  serialized_end=331,
)

_ODOMETRY.fields_by_name['filter_pose'].message_type = _ODOMETRYPOSE
_ODOMETRY.fields_by_name['predict_pose'].message_type = _ODOMETRYPOSE
DESCRIPTOR.message_types_by_name['OdometryPose'] = _ODOMETRYPOSE
DESCRIPTOR.message_types_by_name['Odometry'] = _ODOMETRY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

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


# @@protoc_insertion_point(module_scope)