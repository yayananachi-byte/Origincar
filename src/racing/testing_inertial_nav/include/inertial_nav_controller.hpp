#ifndef INERTIAL_NAV_CONTROLLER_HPP
#define INERTIAL_NAV_CONTROLLER_HPP

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

#include <vector>
#include <cmath>
#include <string>

namespace testing_inertial_nav
{

// Waypoint structure
struct Waypoint {
    double x;
    double y;
    double yaw;  // Optional: target orientation in radians
    
    Waypoint(double x_, double y_, double yaw_ = 0.0) 
        : x(x_), y(y_), yaw(yaw_) {}
};

// PID Controller class
class PIDController {
public:
    PIDController(double kp, double ki, double kd, 
                  double output_min, double output_max);
    
    double compute(double error, double dt);
    void reset();
    
private:
    double kp_, ki_, kd_;
    double output_min_, output_max_;
    double integral_;
    double prev_error_;
    double prev_time_;
    bool first_run_;
};

// Main Inertial Navigation Controller
class InertialNavController : public rclcpp::Node
{
public:
    InertialNavController();
    ~InertialNavController() = default;

private:
    // Callbacks
    void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg);
    void control_loop();
    
    // Navigation functions
    void initialize_origin();
    bool navigate_to_waypoint(const Waypoint& waypoint);
    void stop_robot();
    
    // Utility functions
    double normalize_angle(double angle);
    double calculate_distance(double x1, double y1, double x2, double y2);
    double calculate_angle_diff(double current_yaw, double target_yaw);
    
    // ROS2 interfaces
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::TimerBase::SharedPtr control_timer_;
    
    // State variables
    bool origin_initialized_;
    double origin_x_;
    double origin_y_;
    double origin_yaw_;
    
    double current_x_;
    double current_y_;
    double current_yaw_;
    
    // Waypoint navigation
    std::vector<Waypoint> waypoints_;
    int current_waypoint_idx_;
    bool navigation_complete_;
    
    // PID controllers
    std::unique_ptr<PIDController> linear_pid_;
    std::unique_ptr<PIDController> angular_pid_;
    
    // Parameters
    double position_tolerance_;     // meters
    double angle_tolerance_;        // radians
    double max_linear_speed_;       // m/s
    double max_angular_speed_;      // rad/s
    double control_frequency_;      // Hz
    
    // Timing
    rclcpp::Time last_control_time_;
};

} // namespace testing_inertial_nav

#endif // INERTIAL_NAV_CONTROLLER_HPP
