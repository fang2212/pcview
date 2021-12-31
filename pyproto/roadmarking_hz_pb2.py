# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: roadmarking_hz.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import geometry_pb2 as geometry__pb2
import data_source_pb2 as data__source__pb2
import odometry_pb2 as odometry__pb2
import camera_pb2 as camera__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14roadmarking_hz.proto\x12\rperception.hz\x1a\x0egeometry.proto\x1a\x11\x64\x61ta_source.proto\x1a\x0eodometry.proto\x1a\x0c\x63\x61mera.proto\"j\n\x10RoadSysProfiling\x12\x33\n\x05items\x18\x03 \x03(\x0b\x32$.perception.hz.RoadSysProfiling.Item\x1a!\n\x04Item\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0b\n\x03val\x18\x02 \x01(\x02\"\xe7\x37\n\x0bRoadmarking\x12\x10\n\x08\x66rame_id\x18\x01 \x01(\x04\x12\x11\n\ttimestamp\x18\x02 \x01(\x04\x12\x39\n\x08laneline\x18\x03 \x01(\x0b\x32\'.perception.hz.Roadmarking.LanelineList\x12\x39\n\nfreespaces\x18\x04 \x01(\x0b\x32%.perception.hz.Roadmarking.FreeSpaces\x12\x39\n\x0broadmarkers\x18\x06 \x01(\x0b\x32$.perception.hz.Roadmarking.Roadmarks\x12;\n\nroad_edges\x18\x07 \x01(\x0b\x32\'.perception.hz.Roadmarking.RoadEdgeList\x12\x34\n\x08ldw_info\x18\x08 \x01(\x0b\x32\".perception.hz.Roadmarking.LDWInfo\x12<\n\x0b\x63\x61lib_lines\x18\t \x01(\x0b\x32\'.perception.hz.Roadmarking.LanelineList\x12\x34\n\x06motion\x18\n \x01(\x0b\x32$.perception.hz.Roadmarking.MotionEst\x12\x30\n\x04pose\x18\x0b \x01(\x0b\x32\".perception.hz.Roadmarking.PoseEst\x12\x34\n\x08hpp_info\x18\x0c \x01(\x0b\x32\".perception.hz.Roadmarking.HppInfo\x12\x0c\n\x04tick\x18\r \x01(\x04\x12(\n\x0b\x64\x61ta_source\x18\x0e \x01(\x0e\x32\x13.minieye.DataSource\x12=\n\x0eslope_equation\x18\x0f \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12\x13\n\x0b\x66inish_time\x18\x10 \x01(\x04\x12:\n\tjunc_list\x18\x11 \x01(\x0b\x32\'.perception.hz.Roadmarking.JunctionList\x12\x38\n\x0fprofiling_items\x18\x12 \x01(\x0b\x32\x1f.perception.hz.RoadSysProfiling\x12\x11\n\trecv_time\x18\x13 \x01(\x04\x12\x0b\n\x03\x66ps\x18\x14 \x01(\x02\x12&\n\nego_motion\x18\x15 \x01(\x0b\x32\x12.minieye.EgoMotion\x12\x16\n\x0e\x65go_lane_width\x18\x16 \x01(\x02\x12\x1e\n\x06\x63\x61m_id\x18\x17 \x01(\x0b\x32\x0e.minieye.CamID\x1a\xaa\x01\n\nCurveCoeff\x12\x15\n\rlongitude_min\x18\x01 \x01(\x02\x12\x15\n\rlongitude_max\x18\x02 \x01(\x02\x12\n\n\x02\x63\x30\x18\x03 \x01(\x01\x12\n\n\x02\x63\x31\x18\x04 \x01(\x01\x12\n\n\x02\x63\x32\x18\x05 \x01(\x01\x12\n\n\x02\x63\x33\x18\x06 \x01(\x01\x12\x0e\n\x06\x64\x65v_c0\x18\x07 \x01(\x01\x12\x0e\n\x06\x64\x65v_c1\x18\x08 \x01(\x01\x12\x0e\n\x06\x64\x65v_c2\x18\t \x01(\x01\x12\x0e\n\x06\x64\x65v_c3\x18\n \x01(\x01\x1a\x8a\x06\n\x08Laneline\x12\x31\n\x04type\x18\x01 \x01(\x0e\x32#.perception.hz.Roadmarking.LineType\x12\x41\n\x08pos_type\x18\x02 \x01(\x0e\x32/.perception.hz.Roadmarking.LanelinePositionType\x12\x38\n\ncolor_type\x18\x03 \x01(\x0e\x32$.perception.hz.Roadmarking.ColorType\x12\x42\n\x13\x63urve_vehicle_coord\x18\x04 \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12@\n\x11\x63urve_image_coord\x18\x05 \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12:\n\x12points_image_coord\x18\x06 \x01(\x0b\x32\x1e.perception.common.Point2fList\x12<\n\x14points_vehicle_coord\x18\x07 \x01(\x0b\x32\x1e.perception.common.Point3fList\x12>\n\x16\x66it_points_image_coord\x18\x08 \x01(\x0b\x32\x1e.perception.common.Point2fList\x12@\n\x18\x66it_points_vehicle_coord\x18\t \x01(\x0b\x32\x1e.perception.common.Point3fList\x12\n\n\x02id\x18\n \x01(\x04\x12\x38\n\nline_state\x18\x0b \x01(\x0e\x32$.perception.hz.Roadmarking.LineState\x12\x12\n\nconfidence\x18\x0c \x01(\x02\x12\r\n\x05width\x18\r \x01(\x02\x12\x0b\n\x03\x61ge\x18\x0e \x01(\r\x12\x14\n\x0cpoint_cam_id\x18\x0f \x03(\r\x12/\n\x0b\x63\x65ntroid_pt\x18\x10 \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x0f\n\x07lane_id\x18\x11 \x01(\x05\x1a\x41\n\x0cLanelineList\x12\x31\n\x04line\x18\x01 \x03(\x0b\x32#.perception.hz.Roadmarking.Laneline\x1a\xc8\x04\n\nFreeSpaces\x12@\n\x08\x66reezone\x18\x01 \x03(\x0b\x32..perception.hz.Roadmarking.FreeSpaces.FreeZone\x12\x10\n\x08\x64ist_std\x18\x02 \x01(\x02\x12\x11\n\tangle_std\x18\x03 \x01(\x02\x12\x12\n\nheight_std\x18\x04 \x01(\x02\x1a\x86\x03\n\x08\x46reeZone\x12\x35\n\x11point_image_coord\x18\x01 \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x37\n\x13point_vehicle_coord\x18\x02 \x01(\x0b\x32\x1a.perception.common.Point3f\x12\x0c\n\x04\x64ist\x18\x03 \x01(\x02\x12\r\n\x05\x61ngle\x18\x04 \x01(\x02\x12\x36\n\nlane_index\x18\x05 \x01(\x0e\x32\".perception.hz.Roadmarking.LaneIdx\x12\x12\n\nconfidence\x18\x06 \x01(\x02\x12\x32\n\x04type\x18\x07 \x01(\x0e\x32$.perception.hz.Roadmarking.SpaceType\x12\x45\n\x0bmotion_prop\x18\x08 \x01(\x0e\x32\x30.perception.hz.Roadmarking.FreeSpaces.MotionProp\x12\x11\n\tcamera_id\x18\t \x01(\r\x12\x13\n\x0bsensor_type\x18\n \x01(\r\"6\n\nMotionProp\x12\x0c\n\x08kMovable\x10\x00\x12\x0e\n\nkUnmovable\x10\x01\x12\n\n\x06kStill\x10\x02\x1a\x8f\x04\n\x08RoadEdge\x12\n\n\x02id\x18\x01 \x01(\r\x12\x0b\n\x03\x61ge\x18\x02 \x01(\r\x12\x42\n\x13\x63urve_vehicle_coord\x18\x03 \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12@\n\x11\x63urve_image_coord\x18\x04 \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12<\n\x14points_vehicle_coord\x18\x05 \x01(\x0b\x32\x1e.perception.common.Point3fList\x12:\n\x12points_image_coord\x18\x06 \x01(\x0b\x32\x1e.perception.common.Point2fList\x12>\n\x16\x66it_points_image_coord\x18\x07 \x01(\x0b\x32\x1e.perception.common.Point2fList\x12@\n\x18\x66it_points_vehicle_coord\x18\x08 \x01(\x0b\x32\x1e.perception.common.Point3fList\x12\x33\n\x05state\x18\t \x01(\x0e\x32$.perception.hz.Roadmarking.LineState\x12\x0c\n\x04side\x18\n \x01(\x05\x12\x12\n\nconfidence\x18\x0b \x01(\x02\x12\x11\n\tcamera_id\x18\x0c \x03(\r\x1aG\n\x0cRoadEdgeList\x12\x37\n\nroad_edges\x18\x01 \x03(\x0b\x32#.perception.hz.Roadmarking.RoadEdge\x1a\xbc\x08\n\tRoadmarks\x12@\n\troadmarks\x18\x01 \x03(\x0b\x32-.perception.hz.Roadmarking.Roadmarks.Roadmark\x1a\x81\x04\n\x08Roadmark\x12\n\n\x02id\x18\x01 \x01(\r\x12\x37\n\x04type\x18\x02 \x01(\x0e\x32).perception.hz.Roadmarking.Roadmarks.Type\x12=\n\x15\x63orner_pt_image_coord\x18\x03 \x01(\x0b\x32\x1e.perception.common.Point2fList\x12?\n\x17\x63orner_pt_vehicle_coord\x18\x04 \x01(\x0b\x32\x1e.perception.common.Point3fList\x12:\n\x16\x63\x65ntroid_vehicle_coord\x18\x05 \x01(\x0b\x32\x1a.perception.common.Point3f\x12\x12\n\nconfidence\x18\x06 \x01(\x02\x12\x10\n\x08lane_idx\x18\x07 \x01(\r\x12\x37\n\x04\x66orm\x18\x08 \x01(\x0e\x32).perception.hz.Roadmarking.Roadmarks.Form\x12\x39\n\x05state\x18\t \x01(\x0e\x32*.perception.hz.Roadmarking.Roadmarks.State\x12\x38\n\x14\x63\x65ntroid_image_coord\x18\n \x01(\x0b\x32\x1a.perception.common.Point2f\x12\r\n\x05width\x18\x0b \x01(\x02\x12\x11\n\tcamera_id\x18\x0c \x01(\r\"\xc4\x02\n\x04Type\x12\x0f\n\x0bkBackGround\x10\x00\x12\x12\n\x0ekStraightArrow\x10\x01\x12\x0e\n\nkLeftArrow\x10\x02\x12\x0f\n\x0bkRightArrow\x10\x03\x12\x0f\n\x0bkUturnArrow\x10\x04\x12\x0c\n\x08kDiamond\x10\x05\x12\x15\n\x11kInvertedTriangle\x10\x06\x12\x12\n\x0ekOppositemarks\x10\x07\x12\r\n\tkStopLane\x10\x08\x12\x12\n\x0ekZebraCrossing\x10\t\x12\x12\n\x0ekNoParkingArea\x10\n\x12\r\n\tkGoreArea\x10\x0b\x12\x10\n\x0ckGroundWords\x10\x0c\x12\x0b\n\x07kOthers\x10\r\x12\x15\n\x11kDecelerationLine\x10\x0e\x12\r\n\tkTypeNums\x10\x0f\x12\x0e\n\nkSpeedBump\x10\x10\x12\x11\n\rkManholeCover\x10\x11\"Y\n\x04\x46orm\x12\x14\n\x10kRoadmarkUnknown\x10\x00\x12\x12\n\x0ekRoadmarkPoint\x10\x01\x12\x11\n\rkRoadmarkLine\x10\x02\x12\x14\n\x10kRoadmarkPolygon\x10\x03\"G\n\x05State\x12\x11\n\rkStateUnknown\x10\x00\x12\r\n\tkObserved\x10\x01\x12\x0e\n\nkPredicted\x10\x02\x12\x0c\n\x08kUpdated\x10\x03\x1a\x82\x04\n\x07LDWInfo\x12>\n\tldw_state\x18\x01 \x01(\x0e\x32+.perception.hz.Roadmarking.LDWInfo.LdwState\x12\x17\n\x0fleft_wheel_dist\x18\x02 \x01(\x02\x12\x18\n\x10right_wheel_dist\x18\x03 \x01(\x02\x12\x14\n\x0cwarning_dist\x18\x04 \x01(\x02\x12\x15\n\rearliest_dist\x18\x05 \x01(\x02\x12\x13\n\x0blatest_dist\x18\x06 \x01(\x02\x12\x19\n\x11ldw_state_changed\x18\x07 \x01(\x08\x12G\n\x0eldw_work_state\x18\x08 \x01(\x0e\x32/.perception.hz.Roadmarking.LDWInfo.LdwWorkState\x12\x13\n\x0bturn_radius\x18\t \x01(\x02\x12\x17\n\x0fnearest_line_id\x18\n \x01(\x04\x12\x11\n\tldw_level\x18\x0b \x01(\r\"5\n\x08LdwState\x12\x0c\n\x08kLdwNone\x10\x00\x12\x0c\n\x08kLdwLeft\x10\x01\x12\r\n\tkLdwRight\x10\x02\"f\n\x0cLdwWorkState\x12\x10\n\x0ckUnavailable\x10\x00\x12\x08\n\x04kOff\x10\x01\x12\x0c\n\x08kStandby\x10\x02\x12\x0b\n\x07kActive\x10\x03\x12\x11\n\rkNotAvailable\x10\x04\x12\x0c\n\x08kUnknown\x10\x05\x1aK\n\tMotionEst\x12\x15\n\rlateral_speed\x18\x01 \x01(\x02\x12\x13\n\x0blateral_acc\x18\x02 \x01(\x02\x12\x12\n\nconfidence\x18\x03 \x01(\x02\x1a\xc4\x01\n\x07PoseEst\x12\x11\n\tpitch_est\x18\x01 \x01(\x02\x12-\n\tvanish_pt\x18\x02 \x01(\x0b\x32\x1a.perception.common.Point2f\x12.\n\nvanish_cov\x18\x03 \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x10\n\x08is_valid\x18\x04 \x01(\x08\x12\x11\n\tcamera_id\x18\x05 \x01(\r\x12\x0e\n\x06\x64pitch\x18\x06 \x01(\x02\x12\x12\n\nconfidence\x18\x07 \x01(\x02\x1a\xbd\x05\n\x07HppInfo\x12\x44\n\x15path_prediction_coeff\x18\x01 \x01(\x0b\x32%.perception.hz.Roadmarking.CurveCoeff\x12\x19\n\x11is_laneline_valid\x18\x03 \x01(\x08\x12\x10\n\x08is_valid\x18\x04 \x01(\x08\x12\x17\n\x0fplanning_source\x18\x05 \x01(\r\x12\x12\n\nconfidence\x18\x06 \x01(\x02\x12\x16\n\x0e\x65go_lane_width\x18\x07 \x01(\x02\x12\x35\n\x08hpp_line\x18\x08 \x01(\x0b\x32#.perception.hz.Roadmarking.Laneline\x12\x42\n\x15virtual_ego_lane_left\x18\t \x01(\x0b\x32#.perception.hz.Roadmarking.Laneline\x12\x43\n\x16virtual_ego_lane_right\x18\n \x01(\x0b\x32#.perception.hz.Roadmarking.Laneline\x12.\n\npreview_pt\x18\x0b \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x34\n\x10preview_pt_persp\x18\x0c \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x17\n\x0f\x65go_lane_radius\x18\r \x01(\x02\"\xba\x01\n\x0ePlanningSource\x12\x0c\n\x08kInvalid\x10\x00\x12\x13\n\x0fkDoubleLaneline\x10\x01\x12\x11\n\rkLeftLaneline\x10\x02\x12\x12\n\x0ekRightLaneline\x10\x03\x12\x11\n\rkLeftRoadEdge\x10\x04\x12\x12\n\x0ekRightRoadEdge\x10\x05\x12\x14\n\x10kHeadingVehTrace\x10\x06\x12\x0e\n\nkFreespace\x10\x07\x12\x11\n\rkSelfVehTrace\x10\x08\x1a\x96\x02\n\x08Junction\x12\x36\n\x04type\x18\x01 \x01(\x0e\x32(.perception.hz.Roadmarking.Junction.Type\x12\x32\n\x0ept_image_coord\x18\x02 \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x34\n\x10pt_vehicle_coord\x18\x03 \x01(\x0b\x32\x1a.perception.common.Point2f\x12\x13\n\x0blaneline_id\x18\x04 \x03(\x04\x12\r\n\x05state\x18\x05 \x01(\x05\x12\x12\n\nconfidence\x18\x06 \x01(\x02\"0\n\x04Type\x12\x12\n\x0ekMergingPoints\x10\x00\x12\x14\n\x10kDivergingPoints\x10\x01\x1a\x41\n\x0cJunctionList\x12\x31\n\x04junc\x18\x01 \x03(\x0b\x32#.perception.hz.Roadmarking.Junction\"\xaa\x01\n\x14LanelinePositionType\x12\x11\n\rkAdjacentLeft\x10\x00\x12\x0c\n\x08kEgoLeft\x10\x01\x12\r\n\tkEgoRight\x10\x02\x12\x12\n\x0ekAdjacentRight\x10\x03\x12\x0e\n\nkThirdLeft\x10\x04\x12\x0f\n\x0bkThirdRight\x10\x05\x12\x0f\n\x0bkFourthLeft\x10\x06\x12\x10\n\x0ckFourthRight\x10\x07\x12\n\n\x06kOther\x10\x08\"\xdf\x01\n\x08LineType\x12\x14\n\x10kLineSingleSolid\x10\x00\x12\x15\n\x11kLineSingleDashed\x10\x01\x12\r\n\tkLineBold\x10\x02\x12\x14\n\x10kLineDoubleSolid\x10\x03\x12\x15\n\x11kLineDoubleDashed\x10\x04\x12\x14\n\x10kLineSolidDashed\x10\x05\x12\x14\n\x10kLineDashedSolid\x10\x06\x12\n\n\x06kFence\x10\x07\x12\t\n\x05kCurb\x10\x08\x12\x15\n\x11kLineDeceleration\x10\t\x12\x10\n\x0ckLineUnknown\x10\n\"\xce\x01\n\tColorType\x12\x0f\n\x0bkColorWhite\x10\x00\x12\x10\n\x0ckColorYellow\x10\x01\x12\x10\n\x0ckColorOrange\x10\x02\x12\x0e\n\nkColorBlue\x10\x03\x12\x0f\n\x0bkColorGreen\x10\x04\x12\x0e\n\nkColorGray\x10\x05\x12\x15\n\x11kColorWhiteYellow\x10\x06\x12\x15\n\x11kColorYellowWhite\x10\x07\x12\x1a\n\x16kColorYellowGrayFusion\x10\x08\x12\x11\n\rkColorUnknown\x10\t\"<\n\tLineState\x12\r\n\tkDetected\x10\x00\x12\x0e\n\nkPredicted\x10\x01\x12\x10\n\x0ckStableTrack\x10\x02\"\xb5\x01\n\x07LaneIdx\x12\x13\n\x0fkLaneIdxUnknown\x10\x00\x12\x0c\n\x08kEgoLane\x10\x01\x12\x15\n\x11kAdjacentLeftLane\x10\x02\x12\x16\n\x12kAdjacentRightLane\x10\x03\x12\x16\n\x12kSecondaryLeftLane\x10\x04\x12\x17\n\x13kSecondaryRightLane\x10\x05\x12\x12\n\x0ekThirdLeftLane\x10\x06\x12\x13\n\x0fkThirdRightLane\x10\x07\"\x8b\x01\n\tSpaceType\x12\x0f\n\x0bkBackground\x10\x00\x12\x0e\n\nkFreeSpace\x10\x01\x12\x11\n\rkRoadBoundary\x10\x02\x12\x0c\n\x08kVehicle\x10\x03\x12\r\n\tkRoadSign\x10\x04\x12\t\n\x05kPole\x10\x05\x12\x0e\n\nkGuardrail\x10\x06\x12\x12\n\x0ekSpaceTypeNums\x10\x07\"6\n\x0e\x44irectPosition\x12\x0f\n\x0bkDirectSame\x10\x00\x12\x13\n\x0fkDirectOpposite\x10\x01\x62\x06proto3')



_ROADSYSPROFILING = DESCRIPTOR.message_types_by_name['RoadSysProfiling']
_ROADSYSPROFILING_ITEM = _ROADSYSPROFILING.nested_types_by_name['Item']
_ROADMARKING = DESCRIPTOR.message_types_by_name['Roadmarking']
_ROADMARKING_CURVECOEFF = _ROADMARKING.nested_types_by_name['CurveCoeff']
_ROADMARKING_LANELINE = _ROADMARKING.nested_types_by_name['Laneline']
_ROADMARKING_LANELINELIST = _ROADMARKING.nested_types_by_name['LanelineList']
_ROADMARKING_FREESPACES = _ROADMARKING.nested_types_by_name['FreeSpaces']
_ROADMARKING_FREESPACES_FREEZONE = _ROADMARKING_FREESPACES.nested_types_by_name['FreeZone']
_ROADMARKING_ROADEDGE = _ROADMARKING.nested_types_by_name['RoadEdge']
_ROADMARKING_ROADEDGELIST = _ROADMARKING.nested_types_by_name['RoadEdgeList']
_ROADMARKING_ROADMARKS = _ROADMARKING.nested_types_by_name['Roadmarks']
_ROADMARKING_ROADMARKS_ROADMARK = _ROADMARKING_ROADMARKS.nested_types_by_name['Roadmark']
_ROADMARKING_LDWINFO = _ROADMARKING.nested_types_by_name['LDWInfo']
_ROADMARKING_MOTIONEST = _ROADMARKING.nested_types_by_name['MotionEst']
_ROADMARKING_POSEEST = _ROADMARKING.nested_types_by_name['PoseEst']
_ROADMARKING_HPPINFO = _ROADMARKING.nested_types_by_name['HppInfo']
_ROADMARKING_JUNCTION = _ROADMARKING.nested_types_by_name['Junction']
_ROADMARKING_JUNCTIONLIST = _ROADMARKING.nested_types_by_name['JunctionList']
_ROADMARKING_FREESPACES_MOTIONPROP = _ROADMARKING_FREESPACES.enum_types_by_name['MotionProp']
_ROADMARKING_ROADMARKS_TYPE = _ROADMARKING_ROADMARKS.enum_types_by_name['Type']
_ROADMARKING_ROADMARKS_FORM = _ROADMARKING_ROADMARKS.enum_types_by_name['Form']
_ROADMARKING_ROADMARKS_STATE = _ROADMARKING_ROADMARKS.enum_types_by_name['State']
_ROADMARKING_LDWINFO_LDWSTATE = _ROADMARKING_LDWINFO.enum_types_by_name['LdwState']
_ROADMARKING_LDWINFO_LDWWORKSTATE = _ROADMARKING_LDWINFO.enum_types_by_name['LdwWorkState']
_ROADMARKING_HPPINFO_PLANNINGSOURCE = _ROADMARKING_HPPINFO.enum_types_by_name['PlanningSource']
_ROADMARKING_JUNCTION_TYPE = _ROADMARKING_JUNCTION.enum_types_by_name['Type']
_ROADMARKING_LANELINEPOSITIONTYPE = _ROADMARKING.enum_types_by_name['LanelinePositionType']
_ROADMARKING_LINETYPE = _ROADMARKING.enum_types_by_name['LineType']
_ROADMARKING_COLORTYPE = _ROADMARKING.enum_types_by_name['ColorType']
_ROADMARKING_LINESTATE = _ROADMARKING.enum_types_by_name['LineState']
_ROADMARKING_LANEIDX = _ROADMARKING.enum_types_by_name['LaneIdx']
_ROADMARKING_SPACETYPE = _ROADMARKING.enum_types_by_name['SpaceType']
_ROADMARKING_DIRECTPOSITION = _ROADMARKING.enum_types_by_name['DirectPosition']
RoadSysProfiling = _reflection.GeneratedProtocolMessageType('RoadSysProfiling', (_message.Message,), {

  'Item' : _reflection.GeneratedProtocolMessageType('Item', (_message.Message,), {
    'DESCRIPTOR' : _ROADSYSPROFILING_ITEM,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.RoadSysProfiling.Item)
    })
  ,
  'DESCRIPTOR' : _ROADSYSPROFILING,
  '__module__' : 'roadmarking_hz_pb2'
  # @@protoc_insertion_point(class_scope:perception.hz.RoadSysProfiling)
  })
_sym_db.RegisterMessage(RoadSysProfiling)
_sym_db.RegisterMessage(RoadSysProfiling.Item)

Roadmarking = _reflection.GeneratedProtocolMessageType('Roadmarking', (_message.Message,), {

  'CurveCoeff' : _reflection.GeneratedProtocolMessageType('CurveCoeff', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_CURVECOEFF,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.CurveCoeff)
    })
  ,

  'Laneline' : _reflection.GeneratedProtocolMessageType('Laneline', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_LANELINE,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.Laneline)
    })
  ,

  'LanelineList' : _reflection.GeneratedProtocolMessageType('LanelineList', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_LANELINELIST,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.LanelineList)
    })
  ,

  'FreeSpaces' : _reflection.GeneratedProtocolMessageType('FreeSpaces', (_message.Message,), {

    'FreeZone' : _reflection.GeneratedProtocolMessageType('FreeZone', (_message.Message,), {
      'DESCRIPTOR' : _ROADMARKING_FREESPACES_FREEZONE,
      '__module__' : 'roadmarking_hz_pb2'
      # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.FreeSpaces.FreeZone)
      })
    ,
    'DESCRIPTOR' : _ROADMARKING_FREESPACES,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.FreeSpaces)
    })
  ,

  'RoadEdge' : _reflection.GeneratedProtocolMessageType('RoadEdge', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_ROADEDGE,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.RoadEdge)
    })
  ,

  'RoadEdgeList' : _reflection.GeneratedProtocolMessageType('RoadEdgeList', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_ROADEDGELIST,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.RoadEdgeList)
    })
  ,

  'Roadmarks' : _reflection.GeneratedProtocolMessageType('Roadmarks', (_message.Message,), {

    'Roadmark' : _reflection.GeneratedProtocolMessageType('Roadmark', (_message.Message,), {
      'DESCRIPTOR' : _ROADMARKING_ROADMARKS_ROADMARK,
      '__module__' : 'roadmarking_hz_pb2'
      # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.Roadmarks.Roadmark)
      })
    ,
    'DESCRIPTOR' : _ROADMARKING_ROADMARKS,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.Roadmarks)
    })
  ,

  'LDWInfo' : _reflection.GeneratedProtocolMessageType('LDWInfo', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_LDWINFO,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.LDWInfo)
    })
  ,

  'MotionEst' : _reflection.GeneratedProtocolMessageType('MotionEst', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_MOTIONEST,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.MotionEst)
    })
  ,

  'PoseEst' : _reflection.GeneratedProtocolMessageType('PoseEst', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_POSEEST,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.PoseEst)
    })
  ,

  'HppInfo' : _reflection.GeneratedProtocolMessageType('HppInfo', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_HPPINFO,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.HppInfo)
    })
  ,

  'Junction' : _reflection.GeneratedProtocolMessageType('Junction', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_JUNCTION,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.Junction)
    })
  ,

  'JunctionList' : _reflection.GeneratedProtocolMessageType('JunctionList', (_message.Message,), {
    'DESCRIPTOR' : _ROADMARKING_JUNCTIONLIST,
    '__module__' : 'roadmarking_hz_pb2'
    # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking.JunctionList)
    })
  ,
  'DESCRIPTOR' : _ROADMARKING,
  '__module__' : 'roadmarking_hz_pb2'
  # @@protoc_insertion_point(class_scope:perception.hz.Roadmarking)
  })
_sym_db.RegisterMessage(Roadmarking)
_sym_db.RegisterMessage(Roadmarking.CurveCoeff)
_sym_db.RegisterMessage(Roadmarking.Laneline)
_sym_db.RegisterMessage(Roadmarking.LanelineList)
_sym_db.RegisterMessage(Roadmarking.FreeSpaces)
_sym_db.RegisterMessage(Roadmarking.FreeSpaces.FreeZone)
_sym_db.RegisterMessage(Roadmarking.RoadEdge)
_sym_db.RegisterMessage(Roadmarking.RoadEdgeList)
_sym_db.RegisterMessage(Roadmarking.Roadmarks)
_sym_db.RegisterMessage(Roadmarking.Roadmarks.Roadmark)
_sym_db.RegisterMessage(Roadmarking.LDWInfo)
_sym_db.RegisterMessage(Roadmarking.MotionEst)
_sym_db.RegisterMessage(Roadmarking.PoseEst)
_sym_db.RegisterMessage(Roadmarking.HppInfo)
_sym_db.RegisterMessage(Roadmarking.Junction)
_sym_db.RegisterMessage(Roadmarking.JunctionList)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ROADSYSPROFILING._serialized_start=104
  _ROADSYSPROFILING._serialized_end=210
  _ROADSYSPROFILING_ITEM._serialized_start=177
  _ROADSYSPROFILING_ITEM._serialized_end=210
  _ROADMARKING._serialized_start=213
  _ROADMARKING._serialized_end=7356
  _ROADMARKING_CURVECOEFF._serialized_start=1164
  _ROADMARKING_CURVECOEFF._serialized_end=1334
  _ROADMARKING_LANELINE._serialized_start=1337
  _ROADMARKING_LANELINE._serialized_end=2115
  _ROADMARKING_LANELINELIST._serialized_start=2117
  _ROADMARKING_LANELINELIST._serialized_end=2182
  _ROADMARKING_FREESPACES._serialized_start=2185
  _ROADMARKING_FREESPACES._serialized_end=2769
  _ROADMARKING_FREESPACES_FREEZONE._serialized_start=2323
  _ROADMARKING_FREESPACES_FREEZONE._serialized_end=2713
  _ROADMARKING_FREESPACES_MOTIONPROP._serialized_start=2715
  _ROADMARKING_FREESPACES_MOTIONPROP._serialized_end=2769
  _ROADMARKING_ROADEDGE._serialized_start=2772
  _ROADMARKING_ROADEDGE._serialized_end=3299
  _ROADMARKING_ROADEDGELIST._serialized_start=3301
  _ROADMARKING_ROADEDGELIST._serialized_end=3372
  _ROADMARKING_ROADMARKS._serialized_start=3375
  _ROADMARKING_ROADMARKS._serialized_end=4459
  _ROADMARKING_ROADMARKS_ROADMARK._serialized_start=3455
  _ROADMARKING_ROADMARKS_ROADMARK._serialized_end=3968
  _ROADMARKING_ROADMARKS_TYPE._serialized_start=3971
  _ROADMARKING_ROADMARKS_TYPE._serialized_end=4295
  _ROADMARKING_ROADMARKS_FORM._serialized_start=4297
  _ROADMARKING_ROADMARKS_FORM._serialized_end=4386
  _ROADMARKING_ROADMARKS_STATE._serialized_start=4388
  _ROADMARKING_ROADMARKS_STATE._serialized_end=4459
  _ROADMARKING_LDWINFO._serialized_start=4462
  _ROADMARKING_LDWINFO._serialized_end=4976
  _ROADMARKING_LDWINFO_LDWSTATE._serialized_start=4819
  _ROADMARKING_LDWINFO_LDWSTATE._serialized_end=4872
  _ROADMARKING_LDWINFO_LDWWORKSTATE._serialized_start=4874
  _ROADMARKING_LDWINFO_LDWWORKSTATE._serialized_end=4976
  _ROADMARKING_MOTIONEST._serialized_start=4978
  _ROADMARKING_MOTIONEST._serialized_end=5053
  _ROADMARKING_POSEEST._serialized_start=5056
  _ROADMARKING_POSEEST._serialized_end=5252
  _ROADMARKING_HPPINFO._serialized_start=5255
  _ROADMARKING_HPPINFO._serialized_end=5956
  _ROADMARKING_HPPINFO_PLANNINGSOURCE._serialized_start=5770
  _ROADMARKING_HPPINFO_PLANNINGSOURCE._serialized_end=5956
  _ROADMARKING_JUNCTION._serialized_start=5959
  _ROADMARKING_JUNCTION._serialized_end=6237
  _ROADMARKING_JUNCTION_TYPE._serialized_start=6189
  _ROADMARKING_JUNCTION_TYPE._serialized_end=6237
  _ROADMARKING_JUNCTIONLIST._serialized_start=6239
  _ROADMARKING_JUNCTIONLIST._serialized_end=6304
  _ROADMARKING_LANELINEPOSITIONTYPE._serialized_start=6307
  _ROADMARKING_LANELINEPOSITIONTYPE._serialized_end=6477
  _ROADMARKING_LINETYPE._serialized_start=6480
  _ROADMARKING_LINETYPE._serialized_end=6703
  _ROADMARKING_COLORTYPE._serialized_start=6706
  _ROADMARKING_COLORTYPE._serialized_end=6912
  _ROADMARKING_LINESTATE._serialized_start=6914
  _ROADMARKING_LINESTATE._serialized_end=6974
  _ROADMARKING_LANEIDX._serialized_start=6977
  _ROADMARKING_LANEIDX._serialized_end=7158
  _ROADMARKING_SPACETYPE._serialized_start=7161
  _ROADMARKING_SPACETYPE._serialized_end=7300
  _ROADMARKING_DIRECTPOSITION._serialized_start=7302
  _ROADMARKING_DIRECTPOSITION._serialized_end=7356
# @@protoc_insertion_point(module_scope)
