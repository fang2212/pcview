import numpy as np


class ObjectInThreeD:

    def __init__(self):
        '''
        Initialize the object with zero state space and the gravity constant
        '''
        # The default coordinate is setting is in right hand rule, x forward, y right, z is below.
        # In this example, yaw angle is assumed as zero.
        # initialization 假设了所有参数从零开始计算。也就是说，所有参数的初始值都是0
        self.X = np.zeros((8, 1))
        # The opposite of the gravity thus directed opposite of the z-axis.
        self.g = 9.81 * np.array([[0], [0], [-1]])

    def rotation_matrix(self, phi, theta, psi):
        '''
        Generates the rotation matrix for the given roll and pitch angles
        The yaw angle is assumed to be equal to zero.
        Note, the psi, phi, theta is the angle between imu frame(body frame) and inertia frame.
        So this roration_matrix is a matrixn that transform pose in inertia frame to body frame.
        pose_body = rotation_matrix*pose_inertial
        '''
        # 这是从惯性坐标系到body坐标系
        # psi = 0.0
        r_x = np.array([[1, 0, 0],
                        [0, np.cos(phi), -np.sin(phi)],
                        [0, np.sin(phi), np.cos(phi)]])

        r_y = np.array([[np.cos(theta), 0, np.sin(theta)],
                        [0, 1, 0],
                        [-np.sin(theta), 0, np.cos(theta)]])

        r_z = np.array([[np.cos(psi), -np.sin(psi), 0],
                        [np.sin(psi), np.cos(psi), 0],
                        [0, 0, 1]])

        r = np.matmul(r_z, np.matmul(r_y, r_x))
        # 返还一个rotation matrix
        return r

    def get_euler_derivatives(self, phi, theta, p, q):
        '''
        Converts the measured body rates into the Euler angle derivatives using the estimated pitch and roll angles.
        '''
        # Calculate the Derivatives for the Euler angles in the inertial frame when yaw angle is zero.
        # transform the derivatives in the body frame to inertial frame.
        # 这是将bodyframe上的角度的微分，也就是角速度转换到惯性坐标系的过程。虽然没算，但应该是rotation matrix的逆。
        euler_rot_mat = np.array([[1, np.sin(phi) * np.tan(theta)],
                                  [0, np.cos(phi)]])

        derivatives_in_bodyframe = np.array([p, q])

        euler_dot = np.matmul(euler_rot_mat, derivatives_in_bodyframe)

        return euler_dot

    def linear_acceleration(self, measured_acceleration, phi, theta, psi):
        '''
        Calculates the true accelerations in the inertial frame of reference based
        on the measured values and the estimated roll and pitch angles.
        '''
        # Calculate the true acceleration in body frame by removing the gravity component
        # 把重力加速度的影响去除，因为除去重力加速度的各轴加速度才是真正对车辆或者UAV有影响的参数
        a_body_frame = measured_acceleration - np.matmul(self.rotation_matrix(phi, theta, psi), self.g)

        # Convert the true acceleration back to the inertial frame
        # 把body坐标系的加速度通过旋转矩阵的inverse变换回惯性坐标系里面。
        a_inertial_frame = np.matmul(np.linalg.inv(self.rotation_matrix(phi, theta, psi)), a_body_frame)

        return a_inertial_frame

    def dead_reckoning_orientation(self, p, q, dt):
        '''
        Updates the orientation of the drone for the measured body rates
        '''
        # Update the state vector component of roll and pitch angles
        phi = self.X[4]
        theta = self.X[3]
        # 通过body上测量的两个轴的角速度，通过坐标变换得到惯性坐标系下的roll和pitch
        euler_dot = self.get_euler_derivatives(phi, theta, p, q)
        self.X[3] = self.X[3] + euler_dot[1] * dt  # integrating the roll angle
        self.X[4] = self.X[4] + euler_dot[0] * dt  # integrating the pitch angle

    # 位置就是靠测量的加速度和delta t一点一点的累积。
    def dead_reckoning_position(self, measured_acceleration, dt):
        '''
        Updates the position and the linear velocity in the inertial frame based on the measured accelerations
        '''
        perceived_phi = self.X[4]
        perceived_theta = self.X[3]

        # Convert the body frame acceleration measurements back to the inertial frame measurements
        a = self.linear_acceleration(measured_acceleration, perceived_phi, perceived_theta)

        # Use the velocity components of the state vector to update the position components of the state vector
        # Use the linear acceleration in the inertial frame to update the velocity components of the state vector
        # 跟文章最上面写的式子1，2，3是一致的。x[0-2]是位置, x[5-7]速度变化。
        self.X[0] = self.X[0] + self.X[5] * dt  # x coordianate x= x + \dot{x} * dt
        self.X[1] = self.X[1] + self.X[6] * dt  # y coordianate y= y + \dot{y} * dt
        self.X[2] = self.X[2] + self.X[7] * dt  # z coordianate z= z + \dot{z} * dt
        self.X[5] = self.X[5] + a[0] * dt  # change in velocity along the x is a_x * dt
        self.X[6] = self.X[6] + a[1] * dt  # change in velocity along the y is a_y * dt
        self.X[7] = self.X[7] + a[2] * dt  # change in velocity along the z is a_z * dt

    def dead_reckoning_update_state(self, measured_acceleration, p, q, dt):
        '''
        The function of the advance state updated the position of the UAV
        in the inertial frame and then the drone attitude.
        '''

        # Advance the position
        self.dead_reckoning_position(measured_acceleration, dt)

        # Advance the attitude
        self.dead_reckoning_orientation(p, q, dt)

        return self.X