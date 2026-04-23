# Gesture Controlled Robotic Arm

## Overview
This project implements real-time control of a robotic arm using hand gestures. A Windows system captures gestures using MediaPipe and sends data via UDP to a ROS2 node on Ubuntu, which controls a simulated Franka FR3 robot in RViz.

---

## System Flow
Camera → MediaPipe → Gesture Data → UDP → ROS2 Node → /joint_states → RViz

---

## Features
- Wrist-based gesture control (left/right and up/down)
- Smooth motion using filtering and calibration
- Real-time communication using UDP
- Gripper control using pinch detection

---

## Technologies Used
- Python  
- OpenCV  
- MediaPipe  
- ROS2 (Humble)  
- RViz  
- UDP Socket Programming  

---

## Robot
- Franka FR3  
- 7 Degrees of Freedom  
- Controlled using `/joint_states`  

---

## Gesture Mapping
- Wrist tilt (left/right) → base rotation  
- Index finger vertical movement → arm up/down  
- Thumb–index distance → gripper open/close  

---

## Files
- `gesture_windows.py` — gesture detection and UDP sender  
- `ros_receiver.py` — ROS2 node for robot control  

---

## Prerequisites

### Windows
- Python 3.10 / 3.11  
- Install dependencies:

pip install opencv-python mediapipe numpy


---

### Ubuntu (ROS2)
- Ubuntu 22.04  
- ROS2 Humble installed  

Install required packages:

sudo apt update
sudo apt install ros-humble-desktop


Source ROS:

source /opt/ros/humble/setup.bash


---

## Setup and Execution

### Step 1: Run Robot in RViz (Ubuntu)

source /opt/ros/humble/setup.bash
ros2 run robot_state_publisher robot_state_publisher fr3.urdf
rviz2


In RViz:
- Add **RobotModel**
- Set Fixed Frame to `base`

---

### Step 2: Run ROS Receiver (Ubuntu)

python3 ros_receiver.py


---

### Step 3: Run Gesture Control (Windows)

python gesture_windows.py


- Press **SPACE** to calibrate  
- Move wrist → control robot  
- Press **Q** to quit  

---

## Key Implementation Details
- Uses **orientation vector (wrist → middle finger)** for control  
- Applies **deadzone and smoothing** to reduce noise  
- Uses **absolute joint mapping** to prevent drift  
- Enforces **joint limits from URDF**  

---
