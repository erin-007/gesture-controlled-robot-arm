import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import socket

UDP_HOST = "0.0.0.0"
UDP_PORT = 5005
SMOOTH   = 0.3
TIMER_PERIOD = 0.033

# Exact limits from your fr3.urdf
LIMITS = [
    (-2.7437,  2.7437),   # joint1 - base yaw
    (-1.7837,  1.7837),   # joint2 - shoulder
    (-2.9007,  2.9007),   # joint3 - elbow roll
    (-3.0421, -0.1518),   # joint4 - elbow bend (always negative!)
    (-2.8065,  2.8065),   # joint5 - wrist yaw
    ( 0.5445,  4.5169),   # joint6 - wrist (always positive!)
    (-3.0159,  3.0159),   # joint7 - wrist roll
]

class GestureReceiver(Node):

    JOINT_NAMES = [
        "fr3_joint1",
        "fr3_joint2",
        "fr3_joint3",
        "fr3_joint4",
        "fr3_joint5",
        "fr3_joint6",
        "fr3_joint7",
        "fr3_finger_joint1",
        "fr3_finger_joint2",
    ]

    # Safe resting pose within actual URDF limits
    REST = [
        0.0,    # joint1  range: -2.74 to +2.74
        -0.5,   # joint2  range: -1.78 to +1.78
        0.0,    # joint3  range: -2.90 to +2.90
        -1.8,   # joint4  range: -3.04 to -0.15  (must stay negative)
        0.0,    # joint5  range: -2.80 to +2.80
        1.5,    # joint6  range:  0.54 to  4.51  (must stay positive)
        0.0,    # joint7  range: -3.01 to +3.01
        0.04,   # finger1
        0.04,   # finger2
    ]

    def __init__(self):
        super().__init__("gesture_receiver")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_HOST, UDP_PORT))
        self.sock.setblocking(False)

        self._target  = list(self.REST)
        self._current = list(self.REST)

        self.create_timer(TIMER_PERIOD, self._update)
        self.get_logger().info(f"Listening on UDP port {UDP_PORT}")

    def _update(self):
        raw_x, raw_y, grip = 0.0, 0.0, 1.0
        got_packet = False

        try:
            while True:
                data, _ = self.sock.recvfrom(256)
                parts = data.decode().split(",")
                if len(parts) == 3:
                    raw_x = float(parts[0])
                    raw_y = float(parts[1])
                    grip  = float(parts[2])
                    got_packet = True
        except BlockingIOError:
            pass
        except (ValueError, UnicodeDecodeError) as e:
            self.get_logger().warn(f"Bad packet: {e}")

        if got_packet:
            lo, hi = LIMITS[0]
            self._target[0] = _clamp(raw_x * 2.0, lo, hi)          # joint1: base left/right

            lo, hi = LIMITS[1]
            self._target[1] = _clamp(-0.5 + raw_y * -1.2, lo, hi)  # joint2: shoulder up/down

            lo, hi = LIMITS[2]
            self._target[2] = _clamp(raw_x * 0.4, lo, hi)          # joint3: coupled to joint1

            lo, hi = LIMITS[3]
            self._target[3] = _clamp(-1.8 + raw_y * -0.8, lo, hi)  # joint4: elbow tracks shoulder

            lo, hi = LIMITS[4]
            self._target[4] = _clamp(raw_x * 0.3, lo, hi)          # joint5: slight wrist follow

            # joint6: fixed at mid of its range (0.54 to 4.51)
            self._target[5] = 1.5

            # joint7: fixed
            self._target[6] = 0.0

            # gripper
            finger = 0.04 if grip > 0.5 else 0.0
            self._target[7] = finger
            self._target[8] = finger

        for i in range(len(self._current)):
            self._current[i] = (
                SMOOTH * self._current[i]
                + (1.0 - SMOOTH) * self._target[i]
            )

        self._publish()

    def _publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name     = self.JOINT_NAMES
        msg.position = [float(v) for v in self._current]
        msg.velocity = []
        msg.effort   = []
        self.pub.publish(msg)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def main(args=None):
    rclpy.init(args=args)
    node = GestureReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
