# Gesture Controlled Robotic Arm

## Overview
This project implements real-time control of a robotic arm using hand gestures. MediaPipe on Windows captures gestures and sends data via UDP to a ROS2 node on Ubuntu, which controls a simulated Franka FR3 robot in RViz.

## System Flow
Camera → MediaPipe → Gesture Data → UDP → ROS2 Node → /joint_states → RViz

## Technologies Used
- Python  
- OpenCV  
- MediaPipe  
- ROS2 (Humble)  
- RViz  
- UDP Socket Programming  

## Robot
- Franka FR3  
- 7 Degrees of Freedom  
- Controlled using JointState  

## Gesture Control
- Wrist tilt (left/right) → base movement  
- Index finger movement (up/down) → arm movement  
- Finger distance(thumb and index) → gripper control
- Move palm back and forwards → arm movement

## Files
- gesture_windows.py – gesture detection  
- ros_receiver.py – ROS2 node  

## How to Run

### Ubuntu
terminal 1:
source /opt/ros/humble/setup.bash
ros2 run robot_state_publisher robot_state_publisher fr3.urdf
terminal 2:
rviz2
terminal 3:
python3 ros_receiver.py


### Windows

python gesture_windows.py


## Key Points
- Uses joint-space control (no kinematics)  
- Real-time communication using UDP  
- Stable control using calibration and filtering  

## Conclusion
This project demonstrates real-time human-robot interaction using gesture control.
