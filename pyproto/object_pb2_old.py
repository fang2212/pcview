# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: object.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import geometry_pb2 as geometry__pb2
import data_source_pb2 as data__source__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='object.proto',
  package='perception',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0cobject.proto\x12\nperception\x1a\x0egeometry.proto\x1a\x11\x64\x61ta_source.proto\"\xeb\x01\n\tImageInfo\x12+\n\x08\x64\x65t_rect\x18\x01 \x01(\x0b\x32\x19.perception.common.Rect2f\x12+\n\x08reg_rect\x18\x02 \x01(\x0b\x32\x19.perception.common.Rect2f\x12-\n\ntrack_rect\x18\x03 \x01(\x0b\x32\x19.perception.common.Rect2f\x12.\n\x0bsmooth_rect\x18\x04 \x01(\x0b\x32\x19.perception.common.Rect2f\x12%\n\x03\x62ox\x18\n \x01(\x0b\x32\x18.perception.common.Box3D\"\x9c\x03\n\tWorldInfo\x12\'\n\x03vel\x18\x01 \x01(\x0b\x32\x1a.perception.common.Point3D\x12+\n\x07rel_vel\x18\x02 \x01(\x0b\x32\x1a.perception.common.Point3D\x12\'\n\x03\x61\x63\x63\x18\x03 \x01(\x0b\x32\x1a.perception.common.Point3D\x12\'\n\x03pos\x18\x04 \x01(\x0b\x32\x1a.perception.common.Point3D\x12\'\n\x04size\x18\x05 \x01(\x0b\x32\x19.perception.common.Size3D\x12)\n\x05\x61ngle\x18\x06 \x01(\x0b\x32\x1a.perception.common.Angle3f\x12%\n\x03\x62ox\x18\n \x01(\x0b\x32\x18.perception.common.Box3D\x12\n\n\x02id\x18\x0b \x01(\x05\x12\x0b\n\x03\x63ls\x18\x0c \x01(\x05\x12\x0b\n\x03val\x18\r \x01(\x02\x12\x0c\n\x04pose\x18\x0e \x01(\x05\x12\x0b\n\x03ttc\x18\x0f \x01(\x02\x12\x0f\n\x07headway\x18\x10 \x01(\x02\x12\x0c\n\x04\x63ipv\x18\x11 \x01(\x05\x12\x0c\n\x04\x63ipp\x18\x12 \x01(\x05\"D\n\nSourceInfo\x12\x11\n\tfile_path\x18\x01 \x01(\t\x12\x11\n\tframe_num\x18\x02 \x01(\x05\x12\x10\n\x08\x66rame_id\x18\x03 \x01(\x05\"\xe8\x01\n\x06Object\x12\x0e\n\x06hit_id\x18\x01 \x01(\x05\x12(\n\x08hit_type\x18\x02 \x01(\x0e\x32\x16.perception.ObjectType\x12\x14\n\x0chit_type_str\x18\x06 \x01(\t\x12\x12\n\nconfidence\x18\x03 \x01(\x02\x12\x11\n\tframe_cnt\x18\x04 \x01(\x05\x12\x11\n\tlife_time\x18\x05 \x01(\x05\x12)\n\nimage_info\x18\x08 \x01(\x0b\x32\x15.perception.ImageInfo\x12)\n\nworld_info\x18\t \x01(\x0b\x32\x15.perception.WorldInfo\"\xca\x01\n\nObjectList\x12 \n\x04list\x18\x01 \x03(\x0b\x32\x12.perception.Object\x12+\n\x0bsource_info\x18\x02 \x01(\x0b\x32\x16.perception.SourceInfo\x12\x0f\n\x07version\x18\x03 \x01(\t\x12\x10\n\x08\x66rame_id\x18\x04 \x01(\x04\x12\x11\n\ttimestamp\x18\x05 \x01(\x04\x12\r\n\x05speed\x18\x06 \x01(\x02\x12(\n\x0b\x64\x61ta_source\x18\x0f \x01(\x0e\x32\x13.minieye.DataSource*\xb8\x01\n\nObjectType\x12\t\n\x05kNone\x10\x00\x12\x0c\n\x08kVehicle\x10\x01\x12\x08\n\x04kPed\x10\x02\x12\t\n\x05kBike\x10\x03\x12\t\n\x05kCone\x10\x04\x12\x11\n\rkVehicleWheel\x10\x05\x12\x11\n\rkVehiclePlate\x10\x06\x12\x0c\n\x08kPedHead\x10\x07\x12\x15\n\x11kSmallTrafficSign\x10\n\x12\x13\n\x0fkBigTrafficSign\x10\x0b\x12\x11\n\rkTrafficLight\x10\x0c*\xd8\x01\n\x0bVehiclePose\x12\x0c\n\x08kInvalid\x10\x00\x12\r\n\tkLeftTail\x10\x01\x12\x0c\n\x08kMidTail\x10\x02\x12\x0e\n\nkRightTail\x10\x03\x12\r\n\tkLeftHead\x10\x04\x12\x0c\n\x08kMidHead\x10\x05\x12\x0e\n\nkRightHead\x10\x06\x12\r\n\tkLeftSide\x10\x07\x12\x0e\n\nkRightSide\x10\x08\x12\x0e\n\nkLeftCutIn\x10\t\x12\x0f\n\x0bkRightCutIn\x10\n\x12\x0f\n\x0bkLeftCutOut\x10\x0b\x12\x10\n\x0ckRightCutOut\x10\x0c*\xe5\x01\n\x0cVehicleClass\x12\r\n\tkNegative\x10\x00\x12\x08\n\x04kBus\x10\x01\x12\x08\n\x04kCar\x10\x02\x12\x0c\n\x08kMiniBus\x10\x03\x12\x10\n\x0ckBucketTruck\x10\x04\x12\x13\n\x0fkContainerTruck\x10\x05\x12\r\n\tkTricycle\x10\x06\x12\x0b\n\x07kTanker\x10\x07\x12\x14\n\x10kCementTankTruck\x10\x08\x12\x0b\n\x07kPickup\x10\t\x12\x12\n\x0ekSedimentTruck\x10\n\x12\n\n\x06kIveco\x10\x0b\x12\x0f\n\x0bkSpecialCar\x10\x0c\x12\r\n\tkCityAuto\x10\rb\x06proto3'
  ,
  dependencies=[geometry__pb2.DESCRIPTOR,data__source__pb2.DESCRIPTOR,])

_OBJECTTYPE = _descriptor.EnumDescriptor(
  name='ObjectType',
  full_name='perception.ObjectType',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='kNone', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kVehicle', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kPed', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kBike', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kCone', index=4, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kVehicleWheel', index=5, number=5,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kVehiclePlate', index=6, number=6,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kPedHead', index=7, number=7,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kSmallTrafficSign', index=8, number=10,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kBigTrafficSign', index=9, number=11,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kTrafficLight', index=10, number=12,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1227,
  serialized_end=1411,
)
_sym_db.RegisterEnumDescriptor(_OBJECTTYPE)

ObjectType = enum_type_wrapper.EnumTypeWrapper(_OBJECTTYPE)
_VEHICLEPOSE = _descriptor.EnumDescriptor(
  name='VehiclePose',
  full_name='perception.VehiclePose',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='kInvalid', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLeftTail', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kMidTail', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kRightTail', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLeftHead', index=4, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kMidHead', index=5, number=5,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kRightHead', index=6, number=6,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLeftSide', index=7, number=7,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kRightSide', index=8, number=8,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLeftCutIn', index=9, number=9,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kRightCutIn', index=10, number=10,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kLeftCutOut', index=11, number=11,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kRightCutOut', index=12, number=12,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1414,
  serialized_end=1630,
)
_sym_db.RegisterEnumDescriptor(_VEHICLEPOSE)

VehiclePose = enum_type_wrapper.EnumTypeWrapper(_VEHICLEPOSE)
_VEHICLECLASS = _descriptor.EnumDescriptor(
  name='VehicleClass',
  full_name='perception.VehicleClass',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='kNegative', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kBus', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kCar', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kMiniBus', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kBucketTruck', index=4, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kContainerTruck', index=5, number=5,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kTricycle', index=6, number=6,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kTanker', index=7, number=7,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kCementTankTruck', index=8, number=8,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kPickup', index=9, number=9,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kSedimentTruck', index=10, number=10,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kIveco', index=11, number=11,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kSpecialCar', index=12, number=12,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='kCityAuto', index=13, number=13,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1633,
  serialized_end=1862,
)
_sym_db.RegisterEnumDescriptor(_VEHICLECLASS)

VehicleClass = enum_type_wrapper.EnumTypeWrapper(_VEHICLECLASS)
kNone = 0
kVehicle = 1
kPed = 2
kBike = 3
kCone = 4
kVehicleWheel = 5
kVehiclePlate = 6
kPedHead = 7
kSmallTrafficSign = 10
kBigTrafficSign = 11
kTrafficLight = 12
kInvalid = 0
kLeftTail = 1
kMidTail = 2
kRightTail = 3
kLeftHead = 4
kMidHead = 5
kRightHead = 6
kLeftSide = 7
kRightSide = 8
kLeftCutIn = 9
kRightCutIn = 10
kLeftCutOut = 11
kRightCutOut = 12
kNegative = 0
kBus = 1
kCar = 2
kMiniBus = 3
kBucketTruck = 4
kContainerTruck = 5
kTricycle = 6
kTanker = 7
kCementTankTruck = 8
kPickup = 9
kSedimentTruck = 10
kIveco = 11
kSpecialCar = 12
kCityAuto = 13



_IMAGEINFO = _descriptor.Descriptor(
  name='ImageInfo',
  full_name='perception.ImageInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='det_rect', full_name='perception.ImageInfo.det_rect', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='reg_rect', full_name='perception.ImageInfo.reg_rect', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='track_rect', full_name='perception.ImageInfo.track_rect', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='smooth_rect', full_name='perception.ImageInfo.smooth_rect', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='box', full_name='perception.ImageInfo.box', index=4,
      number=10, type=11, cpp_type=10, label=1,
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
  serialized_start=64,
  serialized_end=299,
)


_WORLDINFO = _descriptor.Descriptor(
  name='WorldInfo',
  full_name='perception.WorldInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='vel', full_name='perception.WorldInfo.vel', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rel_vel', full_name='perception.WorldInfo.rel_vel', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='acc', full_name='perception.WorldInfo.acc', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pos', full_name='perception.WorldInfo.pos', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='size', full_name='perception.WorldInfo.size', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='angle', full_name='perception.WorldInfo.angle', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='box', full_name='perception.WorldInfo.box', index=6,
      number=10, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='perception.WorldInfo.id', index=7,
      number=11, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cls', full_name='perception.WorldInfo.cls', index=8,
      number=12, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='val', full_name='perception.WorldInfo.val', index=9,
      number=13, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='pose', full_name='perception.WorldInfo.pose', index=10,
      number=14, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ttc', full_name='perception.WorldInfo.ttc', index=11,
      number=15, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='headway', full_name='perception.WorldInfo.headway', index=12,
      number=16, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cipv', full_name='perception.WorldInfo.cipv', index=13,
      number=17, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cipp', full_name='perception.WorldInfo.cipp', index=14,
      number=18, type=5, cpp_type=1, label=1,
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
  serialized_start=302,
  serialized_end=714,
)


_SOURCEINFO = _descriptor.Descriptor(
  name='SourceInfo',
  full_name='perception.SourceInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='file_path', full_name='perception.SourceInfo.file_path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='frame_num', full_name='perception.SourceInfo.frame_num', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='frame_id', full_name='perception.SourceInfo.frame_id', index=2,
      number=3, type=5, cpp_type=1, label=1,
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
  serialized_start=716,
  serialized_end=784,
)


_OBJECT = _descriptor.Descriptor(
  name='Object',
  full_name='perception.Object',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='hit_id', full_name='perception.Object.hit_id', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='hit_type', full_name='perception.Object.hit_type', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='hit_type_str', full_name='perception.Object.hit_type_str', index=2,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='confidence', full_name='perception.Object.confidence', index=3,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='frame_cnt', full_name='perception.Object.frame_cnt', index=4,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='life_time', full_name='perception.Object.life_time', index=5,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='image_info', full_name='perception.Object.image_info', index=6,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='world_info', full_name='perception.Object.world_info', index=7,
      number=9, type=11, cpp_type=10, label=1,
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
  serialized_start=787,
  serialized_end=1019,
)


_OBJECTLIST = _descriptor.Descriptor(
  name='ObjectList',
  full_name='perception.ObjectList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='list', full_name='perception.ObjectList.list', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='source_info', full_name='perception.ObjectList.source_info', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='version', full_name='perception.ObjectList.version', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='frame_id', full_name='perception.ObjectList.frame_id', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='perception.ObjectList.timestamp', index=4,
      number=5, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='speed', full_name='perception.ObjectList.speed', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='data_source', full_name='perception.ObjectList.data_source', index=6,
      number=15, type=14, cpp_type=8, label=1,
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
  serialized_start=1022,
  serialized_end=1224,
)

_IMAGEINFO.fields_by_name['det_rect'].message_type = geometry__pb2._RECT2F
_IMAGEINFO.fields_by_name['reg_rect'].message_type = geometry__pb2._RECT2F
_IMAGEINFO.fields_by_name['track_rect'].message_type = geometry__pb2._RECT2F
_IMAGEINFO.fields_by_name['smooth_rect'].message_type = geometry__pb2._RECT2F
_IMAGEINFO.fields_by_name['box'].message_type = geometry__pb2._BOX3D
_WORLDINFO.fields_by_name['vel'].message_type = geometry__pb2._POINT3D
_WORLDINFO.fields_by_name['rel_vel'].message_type = geometry__pb2._POINT3D
_WORLDINFO.fields_by_name['acc'].message_type = geometry__pb2._POINT3D
_WORLDINFO.fields_by_name['pos'].message_type = geometry__pb2._POINT3D
_WORLDINFO.fields_by_name['size'].message_type = geometry__pb2._SIZE3D
_WORLDINFO.fields_by_name['angle'].message_type = geometry__pb2._ANGLE3F
_WORLDINFO.fields_by_name['box'].message_type = geometry__pb2._BOX3D
_OBJECT.fields_by_name['hit_type'].enum_type = _OBJECTTYPE
_OBJECT.fields_by_name['image_info'].message_type = _IMAGEINFO
_OBJECT.fields_by_name['world_info'].message_type = _WORLDINFO
_OBJECTLIST.fields_by_name['list'].message_type = _OBJECT
_OBJECTLIST.fields_by_name['source_info'].message_type = _SOURCEINFO
_OBJECTLIST.fields_by_name['data_source'].enum_type = data__source__pb2._DATASOURCE
DESCRIPTOR.message_types_by_name['ImageInfo'] = _IMAGEINFO
DESCRIPTOR.message_types_by_name['WorldInfo'] = _WORLDINFO
DESCRIPTOR.message_types_by_name['SourceInfo'] = _SOURCEINFO
DESCRIPTOR.message_types_by_name['Object'] = _OBJECT
DESCRIPTOR.message_types_by_name['ObjectList'] = _OBJECTLIST
DESCRIPTOR.enum_types_by_name['ObjectType'] = _OBJECTTYPE
DESCRIPTOR.enum_types_by_name['VehiclePose'] = _VEHICLEPOSE
DESCRIPTOR.enum_types_by_name['VehicleClass'] = _VEHICLECLASS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ImageInfo = _reflection.GeneratedProtocolMessageType('ImageInfo', (_message.Message,), {
  'DESCRIPTOR' : _IMAGEINFO,
  '__module__' : 'object_pb2'
  # @@protoc_insertion_point(class_scope:perception.ImageInfo)
  })
_sym_db.RegisterMessage(ImageInfo)

WorldInfo = _reflection.GeneratedProtocolMessageType('WorldInfo', (_message.Message,), {
  'DESCRIPTOR' : _WORLDINFO,
  '__module__' : 'object_pb2'
  # @@protoc_insertion_point(class_scope:perception.WorldInfo)
  })
_sym_db.RegisterMessage(WorldInfo)

SourceInfo = _reflection.GeneratedProtocolMessageType('SourceInfo', (_message.Message,), {
  'DESCRIPTOR' : _SOURCEINFO,
  '__module__' : 'object_pb2'
  # @@protoc_insertion_point(class_scope:perception.SourceInfo)
  })
_sym_db.RegisterMessage(SourceInfo)

Object = _reflection.GeneratedProtocolMessageType('Object', (_message.Message,), {
  'DESCRIPTOR' : _OBJECT,
  '__module__' : 'object_pb2'
  # @@protoc_insertion_point(class_scope:perception.Object)
  })
_sym_db.RegisterMessage(Object)

ObjectList = _reflection.GeneratedProtocolMessageType('ObjectList', (_message.Message,), {
  'DESCRIPTOR' : _OBJECTLIST,
  '__module__' : 'object_pb2'
  # @@protoc_insertion_point(class_scope:perception.ObjectList)
  })
_sym_db.RegisterMessage(ObjectList)


# @@protoc_insertion_point(module_scope)
