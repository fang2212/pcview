import struct

def decode_bytes_2_number(signal: dict, data: bytes):
    if signal['size'] != len(data):
        print(__name__, "size not equal data length")
        return None
    
    if signal['type'] == 0:
        return int.from_bytes(data, byteorder="little", signed=signal["signed"])
    
    elif signal['type'] == 1:
        return struct.unpack("<f", data)[0]
    
    elif signal['type'] == 2:
        return struct.unpack("<d", data)[0]



def decode_sample(stream_info, data):
    pass

def decode_lane_marker(stream_info, data):
    """
    Lane marker type
        0=DASHED
        1=SOLID
        2=UNDECIDED
        3=DLM
        4=BOTTS
        5=DECEL
        6=INVALID
    
    The color of the detected lane marker.
        0 = Unknown
        1 = White
        2 = Yellow
        3 = Blue
    """

    prefix = "vision_road_info.roadInfo.roadMarkerInfo"
    lane_type = [
        "hostRightMarker",
        "hostLeftMarker",
        "nextLeftLeftMarker",
        "nextLeftRightMarker",
        "nextRightRightMarker",
        "nextRightLeftMarker"
    ]

    lane_key = [
        "laneMarker.a0",
        "laneMarker.a1",
        "laneMarker.a2",
        "laneMarker.a3",
        "laneMarker.startRange",
        "laneMarker.endRange",
        "laneMarkerConf.confidence",
        "measuredViewRange",
        "laneMarkerType",
        "laneMarkerColor",
        "laneMarkerWidth"
    ]

    lane_res = []
    for i, o in enumerate(lane_type):
        lane = {"type": "lane", "sensor":"ifv410", "id": i}
        for p in lane_key:
            signal = ".".join([prefix, o, p])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            lane[p.split(".")[-1]] = num

        if lane["laneMarkerType"] >= 6 or lane["measuredViewRange"] <= 0.1:
            continue
        lane["range"] = lane["measuredViewRange"]
        # print(lane)
        lane_res.append(lane)
    return lane_res


def decode_hpp(stream_info, data):
    prefix = "vision_road_info.roadInfo.roadHppFusionInfo"
    hpp_key = [
        "laneCenter.a0",
        "laneCenter.a1",
        "laneCenter.a2",
        "laneCenter.a3",
        "laneCenter.startRange",
        "laneCenter.endRange",
        "roadFusionConf",
        "halfWidth",
        "hppLeftWeight",
        "hppRightWeight",
        "roadLeftWeight",
        "roadRightWeight"
    ]

    hpp_res = []
    hpp = {"type": "hpp"}
    for p in hpp_key:
        signal = ".".join([prefix, p])
        signal = stream_info[signal]
        num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
        if num is None:
            continue
        hpp[p.split(".")[-1]] = num
    hpp_res.append(hpp)
    return hpp_res


def decode_reflect_sign(stream_info, data):
    prefix = "vision_active_light_sensor_info.activeLightSensorInfo.reflectiveSigns"
    obs_key = [
        "lightSignLeftAngle",
        "lightSignRightAngle",
        "lightSignBottomAngle",
        "lightSignTopAngle",
        "lightSignID",
        "lightSignDistance",
        "lightSignGlareLevelMax",
        "lightSignGlareLevelCurrent",
    ]

    obs_res = []
    for i in range(12):
        obs = {"type": "reflect_sign", "sensor": "ifv410"}
        for o in obs_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num
        obs_res.append(obs)
    
    signal = stream_info["vision_active_light_sensor_info.activeLightSensorInfo.numOfReflectiveSigns"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return obs_res[:num]


def decode_light_spots(stream_info, data):
    """
    classification Enum (uint8_t) The classification of the active light spot.
        0 = None
        1 = Headlamp
        2 = Tail-lamp
        3 = Pair of Headlamps
        4 = Pair of Tail-lamps
        5 = Truck Cabin Top Lights
        6 = Weak Oncoming Pair of Headlamps OR Weak Oncoming Truck Cabin Top Lights or Weak Oncoming Single Headlamp (adding Weak Oncoming Single Headlamp for 3.18.1 bundle and
        later releases).
        7 = Cluster of lamps
    """
    prefix = "vision_active_light_sensor_info.activeLightSensorInfo.activeLightSpots"
    obs_key = [
        "leftAngle",
        "rightAngle",
        "topAngle",
        "bottomAngle",
        "id",
        "vdID",
        "longPos",
        "pixelTop",
        "pixelBottom",
        "pixelLeft",
        "pixelRight",
        "classification",
        "isTruck"
    ]

    light_spot_res = []
    for i in range(15):
        obs = {"type": "light_spot", "sensor": "ifv410"}
        for o in obs_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num
        light_spot_res.append(obs)
    

    signal = stream_info["vision_active_light_sensor_info.activeLightSensorInfo.numOfActiveLightSpots"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return light_spot_res[:num]



def decode_stop_line(stream_info, data):
    """
    stopLineType Type of stop line:
        0=solid
        8=Dashed
        9=Triangular
        0 to 9 n/a

        284 Road Solid Stop Line e_std_roadStopLine
        285 Road Dashed Stop Line e_std_roadDashedStopLine
        286 Road Double Solid Stop Line e_std_roadDoubleStopLine
        287 Road Dashed Solid Stop Line e_std_roadDashedSolidStopLine
        288 Road Solid Dashed Stop Line e_std_roadSolidDashedStopLine
        289 Road Double Dashed Stop Line e_std_roadDoubleDashedStopLine
        290 Road Triangular Stop Line e_std_roadTriangularStopLine


    stopLineColorType Enum (uint8_t) n/a Color of stop line:
        0=Green_Blue
        1=White
        2=Yellow_Orange_Red
    """


    prefix = "vision_traffic_sign_info.tsrInfo.roadMarkings.roadMarkingStopLines"
    obs_key = [
        "lateralDistance",
        "longitudinalDistance",
        "confidence",
        "angle",
        "isRelevant",
        "stopLineStatus",
        "id",
        "stopLineType",
        "stopLineColorType"
    ]

    stop_line_res = []
    for i in range(10):
        obs = {"type": "stop_line", "sensor": "ifv410"}
        for o in obs_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num
        stop_line_res.append(obs)
    

    signal = stream_info["vision_traffic_sign_info.tsrInfo.roadMarkings.numberOfStopLinesMarkings"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return stop_line_res[:num]


def decode_road_border(stream_info, data):
    prefix = "vision_road_info.roadInfo.roadBorderInfo"
    lane_type = [
        "leftRoadBorder",
        "rightRoadBorder"
    ]

    lane_key = [
        "roadBorder.a0",
        "roadBorder.a1",
        "roadBorder.a2",
        "roadBorder.a3",
        "roadBorder.startRange",
        "roadBorder.endRange",
        "roadBorderConf.confidence",
        "roadBorderConf.sfConf",
        "roadBorderHeight",
        "roadBorderType"
    ]

    lane_res = []
    for i, o in enumerate(lane_type):
        lane = {"type": "road_border", "sensor":"ifv410", "id": i}
        for p in lane_key:
            signal = ".".join([prefix, o, p])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            lane[p.split(".")[-1]] = num

        lane_res.append(lane)
    return lane_res


def decode_road_transition(stream_info, data):
    """
    transitionType uint8_t n/a 
        0 = split
        1 = merge

    transitionLineRole Enum (uint8_t) n/a 
    Position with respect to Host:
        0 = None
        1 = Host_Left
        2 = Host_Right
        3 = Next_Left_Left_Lanemark
        4 = Next_Left_Right_Lanemark
        5 = Next_Right_Left_Lanemark
        6 = Next_Right_Right_Lanemark
        7= Left_Road_Edge
        8 = Right_Road_Edge
        9 = Reserved_1
        10 = Reserved _2
        11 = Reserved _3
        12 = Reserved _4
        13 = Reserved _5
        14 = Reserved _6
        15 = Reserved _7

    """

    prefix = "vision_road_info.roadInfo.roadTransitionPoints"
    road_transition_key = [
       "transitionLongPosition",
       "transitionLatPosition",
       "transitionProbability",
       "transitionType",
       "transition_point_byte",
       "transitionLineRole"
    ]

    road_transition_res = []

    for i in range(12):
        obs = {"type": "road_transition"}
        for o in road_transition_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num

        road_transition_res.append(obs)
    return road_transition_res


def decode_road_arrow(stream_info, data):
    """
    arrowType
    The type of the arrow:
        0 = ARROW_STRAIGHT
        1 = ARROW_STRAIGHT_RIGHT
        2 = ARROW_STRAIGHT_LEFT
        3 = ARROW_RIGHT
        4 = ARROW_LEFT
        5 = ARROW_ONCOMING
        6 = ARROW_CAR_POOL
        7 = ARROW_STRAIGHT_LEFT_RIGHT
        8 = ARROW_LEFT_RIGHT

        14 road Arrow Straight e_std_roadArrowStraight
        15 road Arrow Straight Right e_std_roadArrowStraightRight
        16 road Arrow Straight Left e_std_roadArrowStraightLeft
        17 road Arrow Right e_std_roadArrowRight
        18 road Arrow Left e_std_roadArrowLeft
        19 road Arrow Oncoming e_std_roadArrowOncoming
        276 Road Arrow Straight Left Right e_std_roadArrowStraightLeftRight
        279 Road Arrow Left Right e_std_roadArrowLeftRight


    """

    
    prefix = "vision_traffic_sign_info.tsrInfo.roadMarkings.roadMarkingArrows"
    road_arrow_key = [
       "arrowLatPosition",
       "arrowLongPosition",
       "confidence",
       "id",
       "arrowType"
    ]

    road_arrow_res = []

    for i in range(10):
        obs = {"type": "road_arrow"}
        for o in road_arrow_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num

        road_arrow_res.append(obs)
    
    signal = stream_info["vision_traffic_sign_info.tsrInfo.roadMarkings.numberOfArrowsMarkings"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return road_arrow_res[:num]


def decode_road_speedlimit(stream_info, data):
    """
    speedLimitType in APPEDIX A

    400 Road Speed Limit 10 e_std_roadSpeedLimit_10
    401 Road Speed Limit 100 e_std_roadSpeedLimit_100
    402 Road Speed Limit 110 e_std_roadSpeedLimit_110
    403 Road Speed Limit 120 e_std_roadSpeedLimit_120
    404 Road Speed Limit 20 e_std_roadSpeedLimit_20
    405 Road Speed Limit 30 e_std_roadSpeedLimit_30
    406 Road Speed Limit 40 e_std_roadSpeedLimit_40
    407 Road Speed Limit 50 e_std_roadSpeedLimit_50
    408 Road Speed Limit 60 e_std_roadSpeedLimit_60
    409 Road Speed Limit 70 e_std_roadSpeedLimit_70
    410 Road Speed Limit 80 e_std_roadSpeedLimit_80
    411 Road Speed Limit 90 e_std_roadSpeedLimit_90

    """

    prefix = "vision_traffic_sign_info.tsrInfo.roadMarkings.roadMarkingSpeedLimits"
    road_arrow_key = [
       "speedLimitLatPosition",
       "speedLimitLongPosition",
       "confidence",
       "id",
       "speedLimitType"
    ]

    road_speedlimit_res = []

    for i in range(10):
        obs = {"type": "road_speedlimit"}
        for o in road_arrow_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num

        road_speedlimit_res.append(obs)
    
    signal = stream_info["vision_traffic_sign_info.tsrInfo.roadMarkings.numberOfSpeedLimitMarkings"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return road_speedlimit_res[:num]


def decode_road_cross(stream_info, data):

    """
    cross_type Enum Value Sign Semantic Name Mobileye Internal Enum Name
        291 Road Zebra Crossing e_std_roadZebraCrossing
        292 Road Solid Crossing e_std_roadSolidCrossing
        293 Road Dashed Crossing e_std_roadDashedCrossing

    """

    prefix = "vision_traffic_sign_info.tsrInfo.roadMarkings.roadMarkingCrossings"
    road_arrow_key = [
       "crossingLatPosition",
       "crossingLongPosition",
       "confidence",
       "id",
       "crossingType"
    ]

    road_cross_res = []

    for i in range(10):
        obs = {"type": "road_cross"}
        for o in road_arrow_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num

        road_cross_res.append(obs)
    
    signal = stream_info["vision_traffic_sign_info.tsrInfo.roadMarkings.numberOfCrossingMarkings"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0

    return road_cross_res[:num]


def decode_traffic_sign(stream_info, data):
    """
    trafficsSigns type in appendix A
    signFilterType
        0=NO_SLI_FILTER,
        1=IRRELEVANT_SIGN,
        2=TRUCK_FILTER,
        3=EMBEDDED_FILTER,
        4=MINIMUM_FILTER,
        5=ROAD_NUMBER_FILTER
    signRelevantDecision
        0=RELEVANT_SIGN
        1=HIGHWAY_EXIT_SIGN
        0 to 10 n/a
        62 | Page Polarion ALM 19 2020-10-16 07:552=LANE_ASSIGNMENT_SIGN
        3=PARRALEL_ROAD_SIGN
        4=SIGN_ON_TURN
        5=FAR_IRRELEVANT_SIGN
        6=INTERNAL_SIGN_CONTRADICTION
        7=ERROR_SIGN_CODE
        8= CIPV_IN_FRONT
        9= CONTRADICT_ARROW_SIGN
        10=OTHER_FILTER_REASON
    """

    prefix = "vision_traffic_sign_info.tsrInfo.trafficSigns"
    traffic_sign_key = [
       "signLongPosition",
       "signLatPosition",
       "signHeight",
       "signConfidence",
       "signSuppConfidence1",
       "signSuppConfidence2",
       "relevancyConfidence",
       "signPositionBottom",
       "signPositionTop",
       "signPositionRight",
       "signPositionLeft",
       "signType",
       "signFilterType",
       "signRelevantDecision",
       "signID"
    ]

    traffic_sign_res = []

    for i in range(20):
        obs = {"type": "traffic_sign"}
        for o in traffic_sign_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num

        traffic_sign_res.append(obs)
    
    signal = stream_info["vision_traffic_sign_info.tsrInfo.numberTrafficSigns"]
    num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])
    if num is None:
        num = 0
    return traffic_sign_res[:num]


def decode_obs(stream_info, data):
    """
    The classification of the object.
        0=car
        1=truck
        2=bike (motorcycle)
        3=bicycle
        4=pedestrian
        5= general object (not implemented)
        6= animal (not implemented)
        7= uncertain_vehicle
    
    the target the CIPV. Applies only to vehicles.
        0 = not relevant
        1 = no CIPV
        2 = CIPV

    laneAssignment The lane the target occupies:
        -2 = LEFT_NEXT_NEXT
        -1 = LEFT_NEXT
        0 = EGO_LANE
        1 = RIGHT_NEXT
        2 = RIGHT_NEXT_NEXT
        3 = UNKNOWN
    """

    prefix = "vision_obstacles_info.visObjects.visObs"
    obs_key = [
        "physicalState.width",
        "physicalState.length",
        "physicalState.height",
        "physicalState.longDistance",
        "physicalState.latDistance",
        "physicalState.absoluteLongVelocity",
        "physicalState.absoluteLatVelocity",
        "physicalState.absoluteLongAcc",
        "physicalState.absoluteLatAcc",
        "physicalState.heading",
        "laneAssignment",
        "id",
        "isCipv",
        "confidence",
        "age",
        "classification",
        "ttc_const_vel"
    ]

    obs_res = []
    for i in range(15):
        obs = {"type": "obstacle", "sensor": "ifv410"}
        for o in obs_key:
            signal = ".".join([prefix, o, str(i)])
            signal = stream_info[signal]
            num = decode_bytes_2_number(signal, data[signal['offset']: signal['offset'] + signal['size']])

            if num is None:
                continue
            obs[o.split(".")[-1]] = num
        
        if obs["id"] <= 0:
            continue

        obs["pos_lon"] = obs["longDistance"]
        obs["pos_lat"] = obs["latDistance"]
        obs["cipo"] = 1 if obs["isCipv"] == 2 else 0
        obs["vel_lon"] = obs["absoluteLongVelocity"]
        obs["vel_lat"] = obs["absoluteLatVelocity"]
        obs["acc_lon"] = obs["absoluteLongAcc"]
        obs["acc_lat"] = obs["absoluteLatAcc"]
        obs["TTC"] = obs["ttc_const_vel"]
        obs["class"] = obs["classification"]
        # print(obs)
        obs_res.append(obs)
    return obs_res
