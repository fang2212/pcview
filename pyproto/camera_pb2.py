# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: camera.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0c\x63\x61mera.proto\x12\x07minieye\"\xe4\x03\n\x17\x43\x61meraFrameExtendedInfo\x12\x0b\n\x03seq\x18\x01 \x01(\r\x12\x12\n\nframe_type\x18\x02 \x01(\r\x12\x11\n\tdata_size\x18\x03 \x01(\x05\x12\r\n\x05width\x18\x04 \x01(\x05\x12\x0e\n\x06height\x18\x05 \x01(\x05\x12\x15\n\rfsync_ads_sec\x18\x06 \x01(\r\x12\x16\n\x0e\x66sync_ads_nsec\x18\x07 \x01(\r\x12\x16\n\x0e\x66sync_gnss_sec\x18\x08 \x01(\r\x12\x17\n\x0f\x66sync_gnss_nsec\x18\t \x01(\r\x12\x19\n\x11\x65xp_start_ads_sec\x18\n \x01(\r\x12\x1a\n\x12\x65xp_start_ads_nsec\x18\x0b \x01(\r\x12\x1a\n\x12\x65xp_start_gnss_sec\x18\x0c \x01(\r\x12\x1b\n\x13\x65xp_start_gnss_nsec\x18\r \x01(\r\x12\x17\n\x0f\x65xp_end_ads_sec\x18\x0e \x01(\r\x12\x18\n\x10\x65xp_end_ads_nsec\x18\x0f \x01(\r\x12\x18\n\x10\x65xp_end_gnss_sec\x18\x10 \x01(\r\x12\x19\n\x11\x65xp_end_gnss_nsec\x18\x11 \x01(\r\x12\x11\n\tshutter_1\x18\x12 \x01(\r\x12\x11\n\tshutter_2\x18\x13 \x01(\r\x12\x18\n\x10image_supplement\x18\x14 \x01(\x0c\"\x8f\x02\n\x0b\x43\x61meraFrame\x12\x11\n\tcamera_id\x18\x01 \x01(\r\x12\x11\n\ttimestamp\x18\x02 \x01(\x04\x12\x0c\n\x04tick\x18\x03 \x01(\x04\x12\x10\n\x08\x66rame_id\x18\x04 \x01(\x04\x12\x18\n\x10image_plane_addr\x18\x05 \x03(\x04\x12\x13\n\x0bimage_width\x18\x06 \x01(\r\x12\x14\n\x0cimage_height\x18\x07 \x01(\r\x12\x0e\n\x06stride\x18\x08 \x01(\r\x12\x12\n\nimage_type\x18\t \x01(\r\x12\x18\n\x10image_supplement\x18\n \x01(\x0c\x12\x37\n\rextended_info\x18\x0b \x01(\x0b\x32 .minieye.CameraFrameExtendedInfo\"E\n\x05\x43\x61mID\x12\x12\n\ncam_direct\x18\x01 \x01(\x05\x12\x1c\n\x03\x66ov\x18\x02 \x01(\x0e\x32\x0f.minieye.CamFov\x12\n\n\x02id\x18\x03 \x01(\x05\"[\n\x0bTransMatrix\x12\x12\n\nvcsgnd2img\x18\x01 \x03(\x02\x12\x12\n\nimg2vcsgnd\x18\x02 \x03(\x02\x12\x11\n\tlocal2img\x18\x03 \x03(\x02\x12\x11\n\timg2local\x18\x04 \x03(\x02\"\xf9\x02\n\x0b\x43\x61meraParam\x12\x0f\n\x07\x66ocal_u\x18\x01 \x01(\x02\x12\x0f\n\x07\x66ocal_v\x18\x02 \x01(\x02\x12\n\n\x02\x63u\x18\x03 \x01(\x02\x12\n\n\x02\x63v\x18\x04 \x01(\x02\x12\x0b\n\x03pos\x18\x05 \x03(\x02\x12\r\n\x05pitch\x18\x06 \x01(\x02\x12\x0b\n\x03yaw\x18\x07 \x01(\x02\x12\x0c\n\x04roll\x18\x08 \x01(\x02\x12\x0b\n\x03\x66ov\x18\t \x01(\x02\x12\x14\n\x0cimage_format\x18\n \x01(\x05\x12\x0f\n\x07isp_ver\x18\x0b \x01(\t\x12\x19\n\x11install_direction\x18\x0c \x01(\x05\x12\'\n\ttrans_mtx\x18\r \x01(\x0b\x32\x14.minieye.TransMatrix\x12+\n\tprj_model\x18\x0e \x01(\x0e\x32\x18.minieye.ProjectionModel\x12\x13\n\x0bimage_width\x18\x0f \x01(\r\x12\x14\n\x0cimage_height\x18\x10 \x01(\r\x12\x16\n\x0e\x64istort_coeffs\x18\x11 \x03(\x01\x12\x11\n\tcamera_id\x18\x12 \x01(\r*\x80\x01\n\x0bImageFormat\x12\x12\n\x0e\x46ORMAT_UNKNOWN\x10\x00\x12\x08\n\x04GRAY\x10\x01\x12\x08\n\x04YV12\x10\x02\x12\x08\n\x04JPEG\x10\x03\x12\x07\n\x03PNG\x10\x04\x12\x08\n\x04\x43R12\x10\x05\x12\x07\n\x03\x42\x41\x44\x10\x06\x12\x08\n\x04NV12\x10\x07\x12\x08\n\x04NV21\x10\x08\x12\x0f\n\x0b\x42YPASS_ONLY\x10\t*I\n\tCamDirect\x12\x12\n\x0e\x44IRECT_UNKNOWN\x10\x00\x12\t\n\x05\x46RONT\x10\x01\x12\x08\n\x04REAR\x10\x02\x12\x08\n\x04LEFT\x10\x04\x12\t\n\x05RIGHT\x10\x08*2\n\x06\x43\x61mFov\x12\x0f\n\x0bkFovUnknown\x10\x00\x12\n\n\x06kFov30\x10\x01\x12\x0b\n\x07kFov100\x10\x02*m\n\x0fProjectionModel\x12\x15\n\x11PRJ_MODEL_UNKNOWN\x10\x00\x12\x0b\n\x07\x46ISHEYE\x10\x01\x12\x07\n\x03MEI\x10\x02\x12\x0c\n\x08PIN_HOLE\x10\x03\x12\x08\n\x04\x41TAN\x10\x04\x12\x15\n\x11\x44\x41VIDE_SCARAMUZZA\x10\x05\x62\x06proto3')

_IMAGEFORMAT = DESCRIPTOR.enum_types_by_name['ImageFormat']
ImageFormat = enum_type_wrapper.EnumTypeWrapper(_IMAGEFORMAT)
_CAMDIRECT = DESCRIPTOR.enum_types_by_name['CamDirect']
CamDirect = enum_type_wrapper.EnumTypeWrapper(_CAMDIRECT)
_CAMFOV = DESCRIPTOR.enum_types_by_name['CamFov']
CamFov = enum_type_wrapper.EnumTypeWrapper(_CAMFOV)
_PROJECTIONMODEL = DESCRIPTOR.enum_types_by_name['ProjectionModel']
ProjectionModel = enum_type_wrapper.EnumTypeWrapper(_PROJECTIONMODEL)
FORMAT_UNKNOWN = 0
GRAY = 1
YV12 = 2
JPEG = 3
PNG = 4
CR12 = 5
BAD = 6
NV12 = 7
NV21 = 8
BYPASS_ONLY = 9
DIRECT_UNKNOWN = 0
FRONT = 1
REAR = 2
LEFT = 4
RIGHT = 8
kFovUnknown = 0
kFov30 = 1
kFov100 = 2
PRJ_MODEL_UNKNOWN = 0
FISHEYE = 1
MEI = 2
PIN_HOLE = 3
ATAN = 4
DAVIDE_SCARAMUZZA = 5


_CAMERAFRAMEEXTENDEDINFO = DESCRIPTOR.message_types_by_name['CameraFrameExtendedInfo']
_CAMERAFRAME = DESCRIPTOR.message_types_by_name['CameraFrame']
_CAMID = DESCRIPTOR.message_types_by_name['CamID']
_TRANSMATRIX = DESCRIPTOR.message_types_by_name['TransMatrix']
_CAMERAPARAM = DESCRIPTOR.message_types_by_name['CameraParam']
CameraFrameExtendedInfo = _reflection.GeneratedProtocolMessageType('CameraFrameExtendedInfo', (_message.Message,), {
  'DESCRIPTOR' : _CAMERAFRAMEEXTENDEDINFO,
  '__module__' : 'camera_pb2'
  # @@protoc_insertion_point(class_scope:minieye.CameraFrameExtendedInfo)
  })
_sym_db.RegisterMessage(CameraFrameExtendedInfo)

CameraFrame = _reflection.GeneratedProtocolMessageType('CameraFrame', (_message.Message,), {
  'DESCRIPTOR' : _CAMERAFRAME,
  '__module__' : 'camera_pb2'
  # @@protoc_insertion_point(class_scope:minieye.CameraFrame)
  })
_sym_db.RegisterMessage(CameraFrame)

CamID = _reflection.GeneratedProtocolMessageType('CamID', (_message.Message,), {
  'DESCRIPTOR' : _CAMID,
  '__module__' : 'camera_pb2'
  # @@protoc_insertion_point(class_scope:minieye.CamID)
  })
_sym_db.RegisterMessage(CamID)

TransMatrix = _reflection.GeneratedProtocolMessageType('TransMatrix', (_message.Message,), {
  'DESCRIPTOR' : _TRANSMATRIX,
  '__module__' : 'camera_pb2'
  # @@protoc_insertion_point(class_scope:minieye.TransMatrix)
  })
_sym_db.RegisterMessage(TransMatrix)

CameraParam = _reflection.GeneratedProtocolMessageType('CameraParam', (_message.Message,), {
  'DESCRIPTOR' : _CAMERAPARAM,
  '__module__' : 'camera_pb2'
  # @@protoc_insertion_point(class_scope:minieye.CameraParam)
  })
_sym_db.RegisterMessage(CameraParam)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _IMAGEFORMAT._serialized_start=1331
  _IMAGEFORMAT._serialized_end=1459
  _CAMDIRECT._serialized_start=1461
  _CAMDIRECT._serialized_end=1534
  _CAMFOV._serialized_start=1536
  _CAMFOV._serialized_end=1586
  _PROJECTIONMODEL._serialized_start=1588
  _PROJECTIONMODEL._serialized_end=1697
  _CAMERAFRAMEEXTENDEDINFO._serialized_start=26
  _CAMERAFRAMEEXTENDEDINFO._serialized_end=510
  _CAMERAFRAME._serialized_start=513
  _CAMERAFRAME._serialized_end=784
  _CAMID._serialized_start=786
  _CAMID._serialized_end=855
  _TRANSMATRIX._serialized_start=857
  _TRANSMATRIX._serialized_end=948
  _CAMERAPARAM._serialized_start=951
  _CAMERAPARAM._serialized_end=1328
# @@protoc_insertion_point(module_scope)
