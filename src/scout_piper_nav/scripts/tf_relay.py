import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage

class Relay(Node):
    def __init__(self):
        super().__init__("tf_relay")
        self.pub = self.create_publisher(TFMessage, "/tf", 10)
        self.sub = self.create_subscription(TFMessage, "/mini_piper/tf", self.cb, 10)

    def cb(self, msg):
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = Relay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
