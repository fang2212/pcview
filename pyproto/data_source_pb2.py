# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: data_source.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='data_source.proto',
  package='minieye',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x11\x64\x61ta_source.proto\x12\x07minieye*G\n\nDataSource\x12\x0c\n\x08kMinieye\x10\x00\x12\n\n\x06kEyeQ3\x10\x01\x12\n\n\x06kEyeQ4\x10\x02\x12\x07\n\x03kJ2\x10\x03\x12\n\n\x06kLidar\x10\x04\x62\x06proto3'
)

_DATASOURCE = _descriptor.EnumDescriptor(
  name='DataSource',
  full_name='minieye.DataSource',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='kMinieye', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kEyeQ3', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kEyeQ4', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kJ2', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLidar', index=4, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=30,
  serialized_end=101,
)
_sym_db.RegisterEnumDescriptor(_DATASOURCE)

DataSource = enum_type_wrapper.EnumTypeWrapper(_DATASOURCE)
kMinieye = 0
kEyeQ3 = 1
kEyeQ4 = 2
kJ2 = 3
kLidar = 4


DESCRIPTOR.enum_types_by_name['DataSource'] = _DATASOURCE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)