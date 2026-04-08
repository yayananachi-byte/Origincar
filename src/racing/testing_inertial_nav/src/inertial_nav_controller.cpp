#include "inertial_nav_controller.hpp"
#include <tf2/LinearMath/Matrix3x3.h>
#include <algorithm>

namespace testing_inertial_nav
{

// ==================== PID Controller Implementation ====================

PIDController::PIDController(double kp, double ki, double kd, 
                             double output_min, double output_max)
    : kp_(kp), ki_(ki), kd_(kd),
      output_min_(output_min), output_max_(output_max),
      integral_(0.0), prev_error_(0.0), 
      prev_time_(0.0), first_run_(true)
{
}

double PIDController::compute(double error, double dt)
{
    if (dt <= 0.0) return 0.0;
    
    // Proportional term
    double P = kp_ * error;
    
    // Integral term (with anti-windup)
    integral_ += error * dt;
    double I = ki_ * integral_;
    
    // Derivative term
    double derivative = (error - prev_error_) / dt;
    double D = kd_ * derivative;
    
    // Compute total output
    double output = P + I + D;
    
    // Clamp output
    output = std::max(output_min_, std::min(output_max_, output));
    
    // Anti-windup: only integrate if output is not saturated
    if (output != output_min_ && output != output_max_) {
        integral_ += error * dt;
    } else {
        integral_ = 0.0;  // Reset integral when saturated
    }
    
    // Store for next iteration
    prev_error_ = error;
    prev_time_ += dt;
    first_run_ = false;
    
    return output;
}

void PIDController::reset()
{
    integral_ = 0.0;
    prev_error_ = 0.0;
    prev_time_ = 0.0;
    first_run_ = true;
}

// ==================== Inertial Navigation Controller Implementation ====================

InertialNavController::InertialNavController()
    : Node("inertial_nav_controller"),
      origin_initialized_(false),
      origin_x_(0.0), origin_y_(0.0), origin_yaw_(0.0),
      current_x_(0.0), current_y_(0.0), current_yaw_(0.0),
      current_waypoint_idx_(0),
      navigation_complete_(false)
{
    RCLCPP_INFO(this->get_logger(), "======================================");
    RCLCPP_INFO(this->get_logger(), "Inertial Navigation Controller Started");
    RCLCPP_INFO(this->get_logger(), "======================================");
    
    // Declare parameters
    this->declare_parameter<double>("position_tolerance", 0.05);     // 5 cm
    this->declare_parameter<double>("angle_tolerance", 0.05);         // ~2.86 degrees
    this->declare_parameter<double>("max_linear_speed", 0.5);         // m/s
    this->declare_parameter<double>("max_angular_speed", 1.0);        // rad/s
    this->declare_parameter<double>("control_frequency", 20.0);       // Hz
    
    // PID parameters for linear motion
    this->declare_parameter<double>("linear_kp", 0.8);
    this->declare_parameter<double>("linear_ki", 0.0);
    this->declare_parameter<double>("linear_kd", 0.1);
    
    // PID parameters for angular motion
    this->declare_parameter<double>("angular_kp", 2.0);
    this->declare_parameter<double>("angular_ki", 0.0);
    this->declare_parameter<double>("angular_kd", 0.3);
    
    // Get parameters
    this->get_parameter("position_tolerance", position_tolerance_);
    this->get_parameter("angle_tolerance", angle_tolerance_);
    this->get_parameter("max_linear_speed", max_linear_speed_);
    this->get_parameter("max_angular_speed", max_angular_speed_);
    this->get_parameter("control_frequency", control_frequency_);
    
    double lin_kp, lin_ki, lin_kd;
    double ang_kp, ang_ki, ang_kd;
    this->get_parameter("linear_kp", lin_kp);
    this->get_parameter("linear_ki", lin_ki);
    this->get_parameter("linear_kd", lin_kd);
    this->get_parameter("angular_kp", ang_kp);
    this->get_parameter("angular_ki", ang_ki);
    this->get_parameter("angular_kd", ang_kd);
    
    // Initialize PID controllers
    linear_pid_ = std::make_unique<PIDController>(
        lin_kp, lin_ki, lin_kd, 
        -max_linear_speed_, max_linear_speed_
    );
    
    angular_pid_ = std::make_unique<PIDController>(
        ang_kp, ang_ki, ang_kd,
        -max_angular_speed_, max_angular_speed_
    );
    
    // Define waypoints (relative to origin)
    // Format: Waypoint(x, y, yaw)
    // Example: Square path with 1 meter sides
    waypoints_.push_back(Waypoint(1.0, 0.0, 0.0));      // Point 1: Forward 1m
    waypoints_.push_back(Waypoint(1.0, 1.0, M_PI/2));   // Point 2: Left 1m
    waypoints_.push_back(Waypoint(0.0, 1.0, M_PI));     // Point 3: Back 1m
    waypoints_.push_back(Waypoint(0.0, 0.0, -M_PI/2));  // Point 4: Return to origin
    // waypoints_.push_back(Waypoint(0.5, 0.5, 0.0));   // Uncomment to add more points
    
    RCLCPP_INFO(this->get_logger(), "Loaded %zu waypoints", waypoints_.size());
    for (size_t i = 0; i < waypoints_.size(); ++i) {
        RCLCPP_INFO(this->get_logger(), 
                   "  Waypoint %zu: (%.2f, %.2f, %.2f rad)",
                   i+1, waypoints_[i].x, waypoints_[i].y, waypoints_[i].yaw);
    }
    
    // Create subscribers
    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "/odom_combined",  // EKF fused odometry topic
        10,
        std::bind(&InertialNavController::odom_callback, this, std::placeholders::_1)
    );
    
    // Create publishers
    cmd_vel_pub_ = this->create_publisher<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10
    );
    
    // Create control timer
    int period_ms = static_cast<int>(1000.0 / control_frequency_);
    control_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(period_ms),
        std::bind(&InertialNavController::control_loop, this)
    );
    
    last_control_time_ = this->now();
    
    RCLCPP_INFO(this->get_logger(), "Waiting for odometry data...");
    RCLCPP_INFO(this->get_logger(), "Origin will be set on first odometry message");
}

void InertialNavController::odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    // Initialize origin on first message
    if (!origin_initialized_) {
        initialize_origin();
        return;
    }
    
    // Get current pose in odom_combined frame
    current_x_ = msg->pose.pose.position.x;
    current_y_ = msg->pose.pose.position.y;
    
    // Convert quaternion to Euler angles
    tf2::Quaternion q(
        msg->pose.pose.orientation.x,
        msg->pose.pose.orientation.y,
        msg->pose.pose.orientation.z,
        msg->pose.pose.orientation.w
    );
    tf2::Matrix3x3 m(q);
    double roll, pitch, yaw;
    m.getRPY(roll, pitch, yaw);
    current_yaw_ = yaw;
    
    // Debug output (every 1 second)
    static auto last_debug_time = this->now();
    if ((this->now() - last_debug_time).seconds() >= 1.0) {
        double rel_x = current_x_ - origin_x_;
        double rel_y = current_y_ - origin_y_;
        RCLCPP_DEBUG(this->get_logger(),
                    "Position: (%.3f, %.3f) | Yaw: %.3f rad",
                    rel_x, rel_y, current_yaw_ - origin_yaw_);
        last_debug_time = this->now();
    }
}

void InertialNavController::initialize_origin()
{
    origin_x_ = current_x_;
    origin_y_ = current_y_;
    origin_yaw_ = current_yaw_;
    origin_initialized_ = true;
    
    RCLCPP_INFO(this->get_logger(), "======================================");
    RCLCPP_INFO(this->get_logger(), "Origin initialized at:");
    RCLCPP_INFO(this->get_logger(), "  Global: (%.3f, %.3f, %.3f)", 
                origin_x_, origin_y_, origin_yaw_);
    RCLCPP_INFO(this->get_logger(), "  Relative: (0.0, 0.0, 0.0)");
    RCLCPP_INFO(this->get_logger(), "Starting waypoint navigation...");
    RCLCPP_INFO(this->get_logger(), "======================================");
}

bool InertialNavController::navigate_to_waypoint(const Waypoint& waypoint)
{
    // Calculate relative position to origin
    double rel_current_x = current_x_ - origin_x_;
    double rel_current_y = current_y_ - origin_y_;
    double rel_current_yaw = normalize_angle(current_yaw_ - origin_yaw_);
    
    // Calculate errors
    double dx = waypoint.x - rel_current_x;
    double dy = waypoint.y - rel_current_y;
    double distance = calculate_distance(0, 0, dx, dy);
    
    // Calculate target angle to waypoint
    double target_angle = std::atan2(dy, dx);
    double angle_error = normalize_angle(target_angle - rel_current_yaw);
    
    // Check if we've reached the waypoint
    if (distance < position_tolerance_) {
        // Check orientation if specified
        if (waypoint.yaw != 0.0) {
            double yaw_error = normalize_angle(waypoint.yaw - rel_current_yaw);
            if (std::abs(yaw_error) > angle_tolerance_) {
                // Rotate to target orientation
                double angular_cmd = angular_pid_->compute(yaw_error, 0.05);
                
                geometry_msgs::msg::Twist twist;
                twist.linear.x = 0.0;
                twist.angular.z = angular_cmd;
                cmd_vel_pub_->publish(twist);
                
                RCLCPP_INFO_THROTTLE(this->get_logger(), 
                                   *(this->get_clock()), 500,
                                   "Rotating to target yaw: error=%.3f rad", 
                                   yaw_error);
                return false;
            }
        }
        
        RCLCPP_INFO(this->get_logger(), 
                   "✓ Reached waypoint (%.2f, %.2f)", 
                   waypoint.x, waypoint.y);
        return true;
    }
    
    // Calculate time delta
    rclcpp::Time now = this->now();
    double dt = (now - last_control_time_).seconds();
    last_control_time_ = now;
    
    // PID control for linear motion
    double linear_cmd = linear_pid_->compute(distance, dt);
    
    // PID control for angular motion (heading towards waypoint)
    double angular_cmd = angular_pid_->compute(angle_error, dt);
    
    // Scale linear speed based on angle error (slow down when turning)
    double angle_factor = std::max(0.0, 1.0 - std::abs(angle_error) / M_PI);
    linear_cmd *= angle_factor;
    
    // Publish command
    geometry_msgs::msg::Twist twist;
    twist.linear.x = linear_cmd;
    twist.angular.z = angular_cmd;
    cmd_vel_pub_->publish(twist);
    
    // Debug output
    RCLCPP_INFO_THROTTLE(this->get_logger(), *(this->get_clock()), 500,
                        "Navigating to (%.2f, %.2f) | Dist: %.3f m | Angle err: %.3f rad",
                        waypoint.x, waypoint.y, distance, angle_error);
    
    return false;
}

void InertialNavController::control_loop()
{
    if (!origin_initialized_) {
        return;
    }
    
    if (navigation_complete_) {
        stop_robot();
        return;
    }
    
    // Navigate to current waypoint
    if (current_waypoint_idx_ < static_cast<int>(waypoints_.size())) {
        bool reached = navigate_to_waypoint(waypoints_[current_waypoint_idx_]);
        
        if (reached) {
            // Stop briefly at waypoint
            stop_robot();
            rclcpp::sleep_for(std::chrono::milliseconds(500));
            
            // Move to next waypoint
            current_waypoint_idx_++;
            
            // Reset PID controllers for new waypoint
            linear_pid_->reset();
            angular_pid_->reset();
            
            if (current_waypoint_idx_ >= static_cast<int>(waypoints_.size())) {
                RCLCPP_INFO(this->get_logger(), "======================================");
                RCLCPP_INFO(this->get_logger(), "✓ All waypoints completed!");
                RCLCPP_INFO(this->get_logger(), "======================================");
                navigation_complete_ = true;
            } else {
                RCLCPP_INFO(this->get_logger(), 
                           ">>> Moving to waypoint %d/%zu",
                           current_waypoint_idx_ + 1, waypoints_.size());
            }
        }
    }
}

void InertialNavController::stop_robot()
{
    geometry_msgs::msg::Twist twist;
    twist.linear.x = 0.0;
    twist.angular.z = 0.0;
    cmd_vel_pub_->publish(twist);
}

double InertialNavController::normalize_angle(double angle)
{
    while (angle > M_PI) angle -= 2 * M_PI;
    while (angle < -M_PI) angle += 2 * M_PI;
    return angle;
}

double InertialNavController::calculate_distance(double x1, double y1, double x2, double y2)
{
    return std::sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
}

double InertialNavController::calculate_angle_diff(double current_yaw, double target_yaw)
{
    double diff = target_yaw - current_yaw;
    return normalize_angle(diff);
}

} // namespace testing_inertial_nav

// Main function
int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<testing_inertial_nav::InertialNavController>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
