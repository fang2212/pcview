# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: imu.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='imu.proto',
  package='minieye',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\timu.proto\x12\x07minieye\"U\n\x07ImuData\x12\r\n\x05\x61\x63\x63\x65l\x18\x01 \x03(\x05\x12\x0c\n\x04gyro\x18\x02 \x03(\x05\x12\x0c\n\x04temp\x18\x03 \x01(\x05\x12\x11\n\ttimestamp\x18\x04 \x01(\x04\x12\x0c\n\x04tick\x18\x05 \x01(\x04\">\n\x0bImuDataList\x12#\n\timu_datas\x18\x01 \x03(\x0b\x32\x10.minieye.ImuData\x12\n\n\x02id\x18\x02 \x01(\x04\x62\x06proto3'
)




_IMUDATA = _descriptor.Descriptor(
  name='ImuData',
  full_name='minieye.ImuData',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='accel', full_name='minieye.ImuData.accel', index=0,
      number=1, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='gyro', full_name='minieye.ImuData.gyro', index=1,
      number=2, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='temp', full_name='minieye.ImuData.temp', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='minieye.ImuData.timestamp', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tick', full_name='minieye.ImuData.tick', index=4,
      number=5, type=4, cpp_type=4, label=1,
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
  serialized_start=22,
  serialized_end=107,
)


_IMUDATALIST = _descriptor.Descriptor(
  name='ImuDataList',
  full_name='minieye.ImuDataList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='imu_datas', full_name='minieye.ImuDataList.imu_datas', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='minieye.ImuDataList.id', index=1,
      number=2, type=4, cpp_type=4, label=1,
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
  serialized_start=109,
  serialized_end=171,
)

_IMUDATALIST.fields_by_name['imu_datas'].message_type = _IMUDATA
DESCRIPTOR.message_types_by_name['ImuData'] = _IMUDATA
DESCRIPTOR.message_types_by_name['ImuDataList'] = _IMUDATALIST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ImuData = _reflection.GeneratedProtocolMessageType('ImuData', (_message.Message,), {
  'DESCRIPTOR' : _IMUDATA,
  '__module__' : 'imu_pb2'
  # @@protoc_insertion_point(class_scope:minieye.ImuData)
  })
_sym_db.RegisterMessage(ImuData)

ImuDataList = _reflection.GeneratedProtocolMessageType('ImuDataList', (_message.Message,), {
  'DESCRIPTOR' : _IMUDATALIST,
  '__module__' : 'imu_pb2'
  # @@protoc_insertion_point(class_scope:minieye.ImuDataList)
  })
_sym_db.RegisterMessage(ImuDataList)


# @@protoc_insertion_point(module_scope)
