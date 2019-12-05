#include <iostream>
//#include "common/time/stopwatch.h"
//#include "common/concurrency/this_thread.h"
#include "bird_perspective_mapping.h"

#define MAX_POINT_NUM 500

void BirdPerspectiveMapping::Initialize(const CameraPara& camera_para, int8_t parallel_num)
{
    m_camera_para = camera_para;

    m_parallel_num = parallel_num;
    m_i2g_in_buff_mat.resize(parallel_num);
    m_g2i_in_buff_mat.resize(parallel_num);
    m_out_buff_mat.resize(parallel_num);
    for (int8_t i = 0; i < parallel_num; ++i) {
        m_i2g_in_buff_mat[i] = cv::Mat::zeros(4, MAX_POINT_NUM, CV_32FC1);
        m_g2i_in_buff_mat[i] = cv::Mat::zeros(3, MAX_POINT_NUM, CV_32FC1);
        cv::Mat in1_s3 = m_i2g_in_buff_mat[i].row(2);
        in1_s3.setTo(cv::Scalar(1));

        cv::Mat in2_s3 = m_g2i_in_buff_mat[i].row(2);
        in2_s3.setTo(cv::Scalar(m_camera_para.height));

        m_out_buff_mat[i] = cv::Mat::zeros(4, MAX_POINT_NUM, CV_32FC1);
    }

    InitYawTransformMatrix();
    InitPitchTransformMatrix();
    InitRollTransformMatrix();
    InitPerspTransformMatrix();
    CalcTransformMatrix();
}

BirdPerspectiveMapping::~BirdPerspectiveMapping()
{
}

// rotate with z axis
void BirdPerspectiveMapping::InitYawTransformMatrix()
{
    // transform from world to camera coordinates
    //
    // rotation matrix for yaw
    m_yaw_matrix = cv::Mat::zeros(3, 3, CV_32FC1);

    m_yaw_matrix.at<float>(0, 0) = cos(m_camera_para.yaw);
    m_yaw_matrix.at<float>(0, 1) = sin(m_camera_para.yaw);
    m_yaw_matrix.at<float>(0, 2) = 0;

    m_yaw_matrix.at<float>(1, 0) = -sin(m_camera_para.yaw);
    m_yaw_matrix.at<float>(1, 1) = cos(m_camera_para.yaw);
    m_yaw_matrix.at<float>(1, 2) = 0;

    m_yaw_matrix.at<float>(2, 0) = 0;
    m_yaw_matrix.at<float>(2, 1) = 0;
    m_yaw_matrix.at<float>(2, 2) = 1;
}

// rotate with y axis
void BirdPerspectiveMapping::InitPitchTransformMatrix()
{
    // rotation matrix for pitch
    m_pitch_matrix = cv::Mat::zeros(3, 3, CV_32FC1);

    m_pitch_matrix.at<float>(0, 0) = cos(m_camera_para.pitch);
    m_pitch_matrix.at<float>(0, 1) = 0;
    m_pitch_matrix.at<float>(0, 2) = -sin(m_camera_para.pitch);

    m_pitch_matrix.at<float>(1, 0) = 0;
    m_pitch_matrix.at<float>(1, 1) = 1;
    m_pitch_matrix.at<float>(1, 2) = 0;

    m_pitch_matrix.at<float>(2, 0) = sin(m_camera_para.pitch);
    m_pitch_matrix.at<float>(2, 1) = 0;
    m_pitch_matrix.at<float>(2, 2) = cos(m_camera_para.pitch);
}

// rotate with x axis
void BirdPerspectiveMapping::InitRollTransformMatrix()
{
    m_roll_matrix = cv::Mat::zeros(3, 3, CV_32FC1);
    m_roll_matrix.at<float>(0, 0) = 1;
    m_roll_matrix.at<float>(0, 1) = 0;
    m_roll_matrix.at<float>(0, 2) = 0;

    m_roll_matrix.at<float>(1, 0) = 0;
    m_roll_matrix.at<float>(1, 1) = cos(m_camera_para.roll);
    m_roll_matrix.at<float>(1, 2) = sin(m_camera_para.roll);

    m_roll_matrix.at<float>(2, 0) = 0;
    m_roll_matrix.at<float>(2, 1) = -sin(m_camera_para.roll);
    m_roll_matrix.at<float>(2, 2) = cos(m_camera_para.roll);
}

void BirdPerspectiveMapping::InitPerspTransformMatrix()
{
    m_persp_matrix = cv::Mat::zeros(3, 3, CV_32FC1);
    m_persp_matrix.at<float>(0, 0) = m_camera_para.fu;
    m_persp_matrix.at<float>(0, 1) = 0;
    m_persp_matrix.at<float>(0, 2) = m_camera_para.cu;

    m_persp_matrix.at<float>(1, 0) = 0;
    m_persp_matrix.at<float>(1, 1) = m_camera_para.fv;
    m_persp_matrix.at<float>(1, 2) = m_camera_para.cv;

    m_persp_matrix.at<float>(2, 0) = 0;
    m_persp_matrix.at<float>(2, 1) = 0;
    m_persp_matrix.at<float>(2, 2) = 1;
}

void BirdPerspectiveMapping::CalcTransformMatrix()
{
    m_ground2image_matrix = m_pitch_matrix * m_yaw_matrix;
    m_ground2image_matrix = m_roll_matrix * m_ground2image_matrix;
    // 转成成相机-图像坐标系
    cv::Mat c12 = cv::Mat::zeros(3, 3, CV_32FC1);
    c12.at<float>(0, 0) = 0;
    c12.at<float>(0, 1) = 1;
    c12.at<float>(0, 2) = 0;

    c12.at<float>(1, 0) = 0;
    c12.at<float>(1, 1) = 0;
    c12.at<float>(1, 2) = 1;

    c12.at<float>(2, 0) = 1;
    c12.at<float>(2, 1) = 0;
    c12.at<float>(2, 2) = 0;
    m_ground2image_matrix = c12 * m_ground2image_matrix;
    m_ground2image_matrix = m_persp_matrix * m_ground2image_matrix;
    cv::invert(m_ground2image_matrix, m_image2ground_matrix);
}

/*
void BirdPerspectiveMapping::GetUVLimitsFromXY(IPMPara* ipm_para)
{
    ipm_para->height = static_cast<int>((ipm_para->x_limits[1] - ipm_para->x_limits[0]) /
            ipm_para->x_scale);

    ipm_para->width = static_cast<int>((ipm_para->y_limits[1] - ipm_para->y_limits[0]) /
            ipm_para->y_scale);
    // calc uv limits (x, y)
    cv::Mat xy_limits_pts = cv::Mat::zeros(2, 4, CV_32FC1);
    xy_limits_pts.at<float>(0, 0) = ipm_para->x_limits[0];
    xy_limits_pts.at<float>(0, 1) = ipm_para->x_limits[0];
    xy_limits_pts.at<float>(0, 2) = ipm_para->x_limits[1];
    xy_limits_pts.at<float>(0, 3) = ipm_para->x_limits[1];

    xy_limits_pts.at<float>(1, 0) = ipm_para->y_limits[0];
    xy_limits_pts.at<float>(1, 1) = ipm_para->y_limits[1];
    xy_limits_pts.at<float>(1, 2) = ipm_para->y_limits[0];
    xy_limits_pts.at<float>(1, 3) = ipm_para->y_limits[1];

    cv::Mat uv_limits = cv::Mat::zeros(2, 4, CV_32FC1);
    TransformGround2Image(xy_limits_pts, &uv_limits);

    cv::Mat row1 = uv_limits.row(0);
    cv::Mat row2 = uv_limits.row(1);
    cv::minMaxLoc(row1, &(ipm_para->u_limits[0]), &(ipm_para->u_limits[1]));
    cv::minMaxLoc(row2, &(ipm_para->v_limits[0]), &(ipm_para->v_limits[1]));

    // confined
    float u = m_camera_para.image_width;
    float v = m_camera_para.image_height;

    ipm_para->u_limits[0] = std::max(double(0), ipm_para->u_limits[0]);
    ipm_para->u_limits[1] = std::min(double(u-1), ipm_para->u_limits[1]);
    ipm_para->v_limits[0] = std::max(double(0), ipm_para->v_limits[0]);
    ipm_para->v_limits[1] = std::min(double(v-1), ipm_para->v_limits[1]);

    int i, j;
    float x, y;
    int total_num = ipm_para->width * ipm_para->height;
    cv::Mat xy_grid = cv::Mat::zeros(2, total_num, CV_32FC1);
    for (i = 0, x = ipm_para->x_limits[1] - 0.5 * ipm_para->x_scale;
            i < ipm_para->height; ++i, x -= ipm_para->x_scale) {
            int base = i * ipm_para->width;
        for (j = 0, y = ipm_para->y_limits[0] + 0.5 * ipm_para->y_scale;
                j < ipm_para->width; ++j, y += ipm_para->y_scale) {
            int offset = base + j;
            xy_grid.at<float>(0, offset) = x;
            xy_grid.at<float>(1, offset) = y;
        }
    }
    TransformGround2Image(xy_grid, &(ipm_para->uv_grid));
}

void BirdPerspectiveMapping::TransformImage2Ground(const cv::Mat& in_points, cv::Mat* out_points)
{
    // 初始化输入参数
    *out_points = cv::Mat::zeros(2, in_points.cols, CV_32FC1);
    // get idx
    int8_t idx = ThisThread::GetId() % m_parallel_num;
    for (int col = 0; col < in_points.cols;) {
        int num = in_points.cols - col;
        if (num > MAX_POINT_NUM)
            num = MAX_POINT_NUM;
        cv::Mat in_points_t = in_points.colRange(col, col+num);
        cv::Mat out_points_t = out_points->colRange(col, col+num);
        cv::Rect roi(0, 0, num, 3);
        cv::Mat in_points4 = m_i2g_in_buff_mat[idx](roi);
        // copy inpoints to first two rows
        cv::Mat in_points2 = in_points4.rowRange(0, 2);
        cv::Mat in_points3 = in_points4.rowRange(0, 3);
        in_points_t.copyTo(in_points2);

        cv::Mat dst = m_out_buff_mat[idx](roi);
        dst = m_image2ground_matrix * in_points3;

        float* in_pointsr3 = dst.ptr<float>(2);
        float* out_s1 = out_points_t.ptr<float>(0);
        float* out_s2 = out_points_t.ptr<float>(1);
        float* in_s1 = dst.ptr<float>(0);
        float* in_s2 = dst.ptr<float>(1);

        for(int i = 0; i < num; ++i) {
            float div = in_pointsr3[i] / m_camera_para.height;
            out_s1[i] = in_s1[i] / div;
            out_s2[i] = in_s2[i] / div;
        }

        col += num;
    }
}

void BirdPerspectiveMapping::TransformGround2Image(const cv::Mat& in_points, cv::Mat* out_points)
{
    *out_points = cv::Mat::zeros(2, in_points.cols, CV_32FC1);
    int8_t idx = ThisThread::GetId() % m_parallel_num;
    for (int col = 0; col < in_points.cols;) {
        int num = in_points.cols - col;
        if (num > MAX_POINT_NUM)
            num = MAX_POINT_NUM;
        cv::Mat in_points_t = in_points.colRange(col, col+num);
        cv::Mat out_points_t = out_points->colRange(col, col+num);
        cv::Rect roi(0, 0, num, 3);

        cv::Mat in_points3 = m_g2i_in_buff_mat[idx](roi);
        cv::Mat in_points2 = in_points3.rowRange(0, 2);
        in_points_t.copyTo(in_points2);

        cv::Mat out_s3 = m_out_buff_mat[idx](roi);
        float* in_pointsr3 = out_s3.ptr<float>(2);
        out_s3 = m_ground2image_matrix * in_points3;

        float* out_s1 = out_points_t.ptr<float>(0);
        float* out_s2 = out_points_t.ptr<float>(1);
        float* in_s1 = out_s3.ptr<float>(0);
        float* in_s2 = out_s3.ptr<float>(1);

        for (int i = 0; i < num;  ++i) {
            float div = in_pointsr3[i];

            out_s1[i] = in_s1[i] / div;
            out_s2[i] = in_s2[i] / div;
        }
        col += num;
    }
}
*/

const cv::Mat& BirdPerspectiveMapping::GetImage2GroundMatrix() const
{
    return m_image2ground_matrix;
}

const cv::Mat& BirdPerspectiveMapping::GetGround2ImageMatrix() const
{
    return m_ground2image_matrix;
}

void BirdPerspectiveMapping::GetRMatrix(cv::Mat* res) const
{
    *res = m_pitch_matrix * m_yaw_matrix;
    *res = m_roll_matrix * (*res);
    cv::Mat c12 = cv::Mat::zeros(3, 3, CV_32FC1);
    c12.at<float>(0, 0) = 0;
    c12.at<float>(0, 1) = 1;
    c12.at<float>(0, 2) = 0;

    c12.at<float>(1, 0) = 0;
    c12.at<float>(1, 1) = 0;
    c12.at<float>(1, 2) = 1;

    c12.at<float>(2, 0) = 1;
    c12.at<float>(2, 1) = 0;
    c12.at<float>(2, 2) = 0;
    *res = c12 * (*res);
}

int main(int argc, char** argv) {
    /*
    --pitch=0.0
    --yaw=0.0
    --roll=0.0
    --camera_height=1.280000
    --fu=1458
    --fv=1458
    --cu=640
    --cv=360
    --image_width=1280
    --image_height=720
    */
    // printf("hello world\n");
    if (argc < 8) {
        fprintf(stderr, "Usage Error\n");
        exit(1);
    }

    BirdPerspectiveMapping bird_map;
    CameraPara camera_para;
    camera_para.pitch=atof(argv[1]);
    camera_para.yaw=atof(argv[2]);
    camera_para.roll=atof(argv[3]);
    camera_para.height=atof(argv[4]);
    camera_para.fu=atof(argv[5]);
    camera_para.fv=atof(argv[6]);
    camera_para.cu=atof(argv[7]);
    camera_para.cv=atof(argv[8]);

    camera_para.image_width=1280;
    camera_para.image_height=720;
    bird_map.Initialize(camera_para, 5);
    std::cout<<bird_map.GetImage2GroundMatrix()<<std::endl;
    cv::Mat matrix = bird_map.GetImage2GroundMatrix();
    for (int i=0; i<3; i++) {
        for (int j=0; j<3; j++) {
            std::cout<<matrix.at<float>(i, j)<<std::endl;
        }
    }
    std::cout<<std::endl;
    std::cout<<bird_map.GetGround2ImageMatrix()<<std::endl;
    return 1;
}