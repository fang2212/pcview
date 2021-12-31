# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: object_warning.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14object_warning.proto\x12\x11perception.object\"\xa9\x01\n\x0eVehicleWarning\x12\x12\n\nvehicle_id\x18\x01 \x01(\x05\x12\x0f\n\x07headway\x18\x02 \x01(\x02\x12\x15\n\rwarning_level\x18\x03 \x01(\x05\x12\x0b\n\x03\x66\x63w\x18\x04 \x01(\x05\x12\x0c\n\x04ufcw\x18\x05 \x01(\x05\x12\x17\n\x0fheadway_warning\x18\x06 \x01(\x05\x12\x12\n\nvb_warning\x18\x07 \x01(\x05\x12\x13\n\x0bsag_warning\x18\x08 \x01(\x05\"\x93\x01\n\x0cVehicleState\x12\x11\n\tfcw_state\x18\x01 \x01(\x05\x12\x11\n\thmw_state\x18\x02 \x01(\x05\x12\x11\n\tfcw_level\x18\n \x01(\x05\x12\x12\n\nufcw_level\x18\x0b \x01(\x05\x12\x11\n\thmw_level\x18\x0c \x01(\x05\x12\x10\n\x08vb_level\x18\r \x01(\x05\x12\x11\n\tsag_level\x18\x0e \x01(\x05\"G\n\nPedWarning\x12\x0e\n\x06ped_on\x18\x01 \x01(\x08\x12\x0e\n\x06pcw_on\x18\x02 \x01(\x08\x12\x19\n\x11pcw_warning_level\x18\x03 \x01(\x05\"0\n\x08PedState\x12\x11\n\tpcw_state\x18\x01 \x01(\x05\x12\x11\n\tpcw_level\x18\n \x01(\x05\"\xba\x02\n\nTsrWarning\x12\x14\n\x0cheight_limit\x18\x01 \x01(\x02\x12\x14\n\x0cweight_limit\x18\x02 \x01(\x02\x12\x13\n\x0bspeed_limit\x18\x03 \x01(\x05\x12\x19\n\x11tsr_warning_level\x18\x04 \x01(\x05\x12\x1c\n\x14no_overtaking_status\x18\x05 \x01(\x05\x12\x46\n\x0clight_signal\x18\x06 \x01(\x0b\x32\x30.perception.object.TsrWarning.TrafficLightSignal\x12\x1b\n\x13removal_speed_limit\x18\x07 \x01(\x05\x12\x1c\n\x14speed_limit_distance\x18\x08 \x01(\x02\x1a/\n\x12TrafficLightSignal\x12\x19\n\x11right_turn_on_red\x18\x01 \x01(\x08\"0\n\x08TsrState\x12\x11\n\ttsr_state\x18\x01 \x01(\x05\x12\x11\n\ttsr_level\x18\n \x01(\x05\"\xa6\x01\n\tIhcSignal\x12\x42\n\x0e\x63ontrol_signal\x18\x01 \x01(\x0e\x32*.perception.object.IhcSignal.IhcSignalType\"U\n\rIhcSignalType\x12\x11\n\rkLightInvalid\x10\x00\x12\r\n\tkLightOff\x10\x01\x12\x11\n\rkDippedBeamOn\x10\x02\x12\x0f\n\x0bkHighBeamOn\x10\x03\"\x1d\n\x08IhcState\x12\x11\n\tihc_state\x18\x01 \x01(\x05\"P\n\nBsdWarning\x12\x14\n\x0cleft_warning\x18\x01 \x01(\x05\x12\x15\n\rright_warning\x18\x02 \x01(\x05\x12\x15\n\rfront_warning\x18\x03 \x01(\x05\"\x1d\n\x08\x42sdState\x12\x11\n\tbsd_state\x18\x01 \x01(\x05\"9\n\nLcaWarning\x12\x14\n\x0cleft_warning\x18\x01 \x01(\x05\x12\x15\n\rright_warning\x18\x02 \x01(\x05\"\x1d\n\x08LcaState\x12\x11\n\tlca_state\x18\x01 \x01(\x05\"\x85\x05\n\x07Warning\x12:\n\x0fvehicle_warning\x18\x01 \x01(\x0b\x32!.perception.object.VehicleWarning\x12\x32\n\x0bped_warning\x18\x02 \x01(\x0b\x32\x1d.perception.object.PedWarning\x12\x32\n\x0btsr_warning\x18\x03 \x01(\x0b\x32\x1d.perception.object.TsrWarning\x12\x30\n\nihc_signal\x18\x04 \x01(\x0b\x32\x1c.perception.object.IhcSignal\x12\x32\n\x0b\x62sd_warning\x18\x05 \x01(\x0b\x32\x1d.perception.object.BsdWarning\x12\x32\n\x0blca_warning\x18\x06 \x01(\x0b\x32\x1d.perception.object.LcaWarning\x12\x36\n\rvehicle_state\x18\n \x01(\x0b\x32\x1f.perception.object.VehicleState\x12.\n\tped_state\x18\x0b \x01(\x0b\x32\x1b.perception.object.PedState\x12.\n\ttsr_state\x18\x0c \x01(\x0b\x32\x1b.perception.object.TsrState\x12.\n\tihc_state\x18\r \x01(\x0b\x32\x1b.perception.object.IhcState\x12.\n\tbsd_state\x18\x0e \x01(\x0b\x32\x1b.perception.object.BsdState\x12.\n\tlca_state\x18\x0f \x01(\x0b\x32\x1b.perception.object.LcaState\x12\x14\n\x0cobject_valid\x18\x14 \x01(\x05\x62\x06proto3')



_VEHICLEWARNING = DESCRIPTOR.message_types_by_name['VehicleWarning']
_VEHICLESTATE = DESCRIPTOR.message_types_by_name['VehicleState']
_PEDWARNING = DESCRIPTOR.message_types_by_name['PedWarning']
_PEDSTATE = DESCRIPTOR.message_types_by_name['PedState']
_TSRWARNING = DESCRIPTOR.message_types_by_name['TsrWarning']
_TSRWARNING_TRAFFICLIGHTSIGNAL = _TSRWARNING.nested_types_by_name['TrafficLightSignal']
_TSRSTATE = DESCRIPTOR.message_types_by_name['TsrState']
_IHCSIGNAL = DESCRIPTOR.message_types_by_name['IhcSignal']
_IHCSTATE = DESCRIPTOR.message_types_by_name['IhcState']
_BSDWARNING = DESCRIPTOR.message_types_by_name['BsdWarning']
_BSDSTATE = DESCRIPTOR.message_types_by_name['BsdState']
_LCAWARNING = DESCRIPTOR.message_types_by_name['LcaWarning']
_LCASTATE = DESCRIPTOR.message_types_by_name['LcaState']
_WARNING = DESCRIPTOR.message_types_by_name['Warning']
_IHCSIGNAL_IHCSIGNALTYPE = _IHCSIGNAL.enum_types_by_name['IhcSignalType']
VehicleWarning = _reflection.GeneratedProtocolMessageType('VehicleWarning', (_message.Message,), {
  'DESCRIPTOR' : _VEHICLEWARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.VehicleWarning)
  })
_sym_db.RegisterMessage(VehicleWarning)

VehicleState = _reflection.GeneratedProtocolMessageType('VehicleState', (_message.Message,), {
  'DESCRIPTOR' : _VEHICLESTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.VehicleState)
  })
_sym_db.RegisterMessage(VehicleState)

PedWarning = _reflection.GeneratedProtocolMessageType('PedWarning', (_message.Message,), {
  'DESCRIPTOR' : _PEDWARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.PedWarning)
  })
_sym_db.RegisterMessage(PedWarning)

PedState = _reflection.GeneratedProtocolMessageType('PedState', (_message.Message,), {
  'DESCRIPTOR' : _PEDSTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.PedState)
  })
_sym_db.RegisterMessage(PedState)

TsrWarning = _reflection.GeneratedProtocolMessageType('TsrWarning', (_message.Message,), {

  'TrafficLightSignal' : _reflection.GeneratedProtocolMessageType('TrafficLightSignal', (_message.Message,), {
    'DESCRIPTOR' : _TSRWARNING_TRAFFICLIGHTSIGNAL,
    '__module__' : 'object_warning_pb2'
    # @@protoc_insertion_point(class_scope:perception.object.TsrWarning.TrafficLightSignal)
    })
  ,
  'DESCRIPTOR' : _TSRWARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.TsrWarning)
  })
_sym_db.RegisterMessage(TsrWarning)
_sym_db.RegisterMessage(TsrWarning.TrafficLightSignal)

TsrState = _reflection.GeneratedProtocolMessageType('TsrState', (_message.Message,), {
  'DESCRIPTOR' : _TSRSTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.TsrState)
  })
_sym_db.RegisterMessage(TsrState)

IhcSignal = _reflection.GeneratedProtocolMessageType('IhcSignal', (_message.Message,), {
  'DESCRIPTOR' : _IHCSIGNAL,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.IhcSignal)
  })
_sym_db.RegisterMessage(IhcSignal)

IhcState = _reflection.GeneratedProtocolMessageType('IhcState', (_message.Message,), {
  'DESCRIPTOR' : _IHCSTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.IhcState)
  })
_sym_db.RegisterMessage(IhcState)

BsdWarning = _reflection.GeneratedProtocolMessageType('BsdWarning', (_message.Message,), {
  'DESCRIPTOR' : _BSDWARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.BsdWarning)
  })
_sym_db.RegisterMessage(BsdWarning)

BsdState = _reflection.GeneratedProtocolMessageType('BsdState', (_message.Message,), {
  'DESCRIPTOR' : _BSDSTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.BsdState)
  })
_sym_db.RegisterMessage(BsdState)

LcaWarning = _reflection.GeneratedProtocolMessageType('LcaWarning', (_message.Message,), {
  'DESCRIPTOR' : _LCAWARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.LcaWarning)
  })
_sym_db.RegisterMessage(LcaWarning)

LcaState = _reflection.GeneratedProtocolMessageType('LcaState', (_message.Message,), {
  'DESCRIPTOR' : _LCASTATE,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.LcaState)
  })
_sym_db.RegisterMessage(LcaState)

Warning = _reflection.GeneratedProtocolMessageType('Warning', (_message.Message,), {
  'DESCRIPTOR' : _WARNING,
  '__module__' : 'object_warning_pb2'
  # @@protoc_insertion_point(class_scope:perception.object.Warning)
  })
_sym_db.RegisterMessage(Warning)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _VEHICLEWARNING._serialized_start=44
  _VEHICLEWARNING._serialized_end=213
  _VEHICLESTATE._serialized_start=216
  _VEHICLESTATE._serialized_end=363
  _PEDWARNING._serialized_start=365
  _PEDWARNING._serialized_end=436
  _PEDSTATE._serialized_start=438
  _PEDSTATE._serialized_end=486
  _TSRWARNING._serialized_start=489
  _TSRWARNING._serialized_end=803
  _TSRWARNING_TRAFFICLIGHTSIGNAL._serialized_start=756
  _TSRWARNING_TRAFFICLIGHTSIGNAL._serialized_end=803
  _TSRSTATE._serialized_start=805
  _TSRSTATE._serialized_end=853
  _IHCSIGNAL._serialized_start=856
  _IHCSIGNAL._serialized_end=1022
  _IHCSIGNAL_IHCSIGNALTYPE._serialized_start=937
  _IHCSIGNAL_IHCSIGNALTYPE._serialized_end=1022
  _IHCSTATE._serialized_start=1024
  _IHCSTATE._serialized_end=1053
  _BSDWARNING._serialized_start=1055
  _BSDWARNING._serialized_end=1135
  _BSDSTATE._serialized_start=1137
  _BSDSTATE._serialized_end=1166
  _LCAWARNING._serialized_start=1168
  _LCAWARNING._serialized_end=1225
  _LCASTATE._serialized_start=1227
  _LCASTATE._serialized_end=1256
  _WARNING._serialized_start=1259
  _WARNING._serialized_end=1904
# @@protoc_insertion_point(module_scope)