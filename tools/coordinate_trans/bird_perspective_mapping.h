/// @file bird_perspective_mapping.h
/// @brief  mapping between bird-view image and perspective image
///        coordinate system : north(x) -> east(y) -> ground (z)
///
/// @author Devin (devin@minieye.cc)

#ifndef  BIRD_PERSPECTIVE_MAPPING_H
#define  BIRD_PERSPECTIVE_MAPPING_H

#include "opencv2/opencv.hpp"

// @brief parameters for camera
struct CameraPara {
    float fu; // focal length in x
    float fv; // focal length in y
    float cu; // optical center coordinates in image frame (origin is (0,0) at top left)
    float cv;

    float height; // height of camera above ground (mm)
    float pitch;  // pitch angle in radians (+ve upwards)
    float yaw;    // yaw angle in radians (+ve clockwise)
    float roll;   // roll angle in radians (+ve clockwise)

    float image_width; // width of images
    float image_height; // height of images
    const CameraPara& operator = (const CameraPara& lhs)
    {
        fu = lhs.fu;
        fv = lhs.fv;
        cu = lhs.cu;
        cv = lhs.cv;
        height = lhs.height;
        pitch = lhs.pitch;
        yaw = lhs.yaw;
        roll = lhs.roll;
        image_width = lhs.image_width;
        image_height = lhs.image_height;
        return *this;
    }
};

struct IPMPara
{
    // min and max x-value on ground in world coordinates (north direction)
    double x_limits[2];

    // min and max y-value on ground in world coordinates (east direction)
    double y_limits[2];

    // conversion between mm in world coordinate on the ground
    // in x-direction and pixel in image (north res)
    float x_scale;

    // conversion between mm in world coordinate on the ground
    // in y-direction and pixel in image (east res)
    float y_scale;

    // width in pixel
    int width;

    // height in pixel
    int height;

    // portion of image height to add to y-coordinate of vanishing point
    float vp_portion;

    // min and max u-value on ground in image plane (width direction)
    double u_limits[2];

    // min and max v-value on ground in image plane (height direction)
    double v_limits[2];

    // u/v-value with size(2, width*height) in image plane
    cv::Mat uv_grid;
};

class BirdPerspectiveMapping
{
public:
    BirdPerspectiveMapping() {}
    ~BirdPerspectiveMapping();

    void Initialize(const CameraPara& camera_para, int8_t parallel_num = 1);

    /// @brief compute u/v limits, uv_grid, width, height according to xy-limits
    void GetUVLimitsFromXY(IPMPara* ipm_para);

    /// @brief tansforms points from the image (uv-coordinates) into the real
    ///        world frame on the ground plane (z = height)
    /// @param in_points input points in the image frame (2xN matrix)
    /// @param out_points output points in the world frame on the ground (z = height) (2xN matrix
    ///                   with xw, yw, and implicit z = height)
    void TransformImage2Ground(const cv::Mat& in_points, cv::Mat* out_points);

    /// @brief transforms points from the ground plane (z = height) in the world frame
    ///        into points on the image in image frame (uv-coordinates)
    /// @param in_points 2xN matrix of input points on the ground in world coordinates
    /// @param out_points 2xN matrix points on the image in image coordinates
    //
    void TransformGround2Image(const cv::Mat& in_points, cv::Mat* out_points);

    const cv::Mat& GetImage2GroundMatrix() const;
    const cv::Mat& GetGround2ImageMatrix() const;

    void GetRMatrix(cv::Mat* res) const;

private:
    void InitYawTransformMatrix();
    void InitPitchTransformMatrix();
    void InitRollTransformMatrix();
    void InitPerspTransformMatrix();
    void CalcTransformMatrix();

private:
    CameraPara m_camera_para;
    cv::Mat m_yaw_matrix;
    cv::Mat m_pitch_matrix;
    cv::Mat m_roll_matrix;
    cv::Mat m_shift_matrix;
    cv::Mat m_persp_matrix;
    cv::Mat m_ground2image_matrix; // 3 X 3
    cv::Mat m_image2ground_matrix; // 3 X 3
    cv::Mat m_vp; // vanishing point
    // accelerate spped
    std::deque<cv::Mat> m_out_buff_mat;
    std::deque<cv::Mat> m_i2g_in_buff_mat;
    std::deque<cv::Mat> m_g2i_in_buff_mat;
    int8_t m_parallel_num;
};

#endif  // BIRD_PERSPECTIVE_MAPPING_H
