# Copyright (C) 2023 Miguel Ángel González Santamarta
# Copyright (C) 2025 Gemini

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import rclpy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import TransitionCallbackReturn
from rclpy.lifecycle import LifecycleState

import cv2
import numpy as np
import message_filters
from cv_bridge import CvBridge

from sensor_msgs.msg import CompressedImage
from yolo_msgs.msg import DetectionArray


class TrackingVisualizerNode(LifecycleNode):

    def __init__(self) -> None:
        super().__init__("tracking_visualizer_node")

        # params
        self.declare_parameter("image_reliability", QoSReliabilityPolicy.BEST_EFFORT)

        self.cv_bridge = CvBridge()

    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Configuring...")

        self.image_reliability = (
            self.get_parameter("image_reliability").get_parameter_value().integer_value
        )

        self._pub = self.create_lifecycle_publisher(
            CompressedImage, "tracking_dbg_image/compressed", 10
        )

        super().on_configure(state)
        self.get_logger().info(f"[{self.get_name()}] Configured")

        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Activating...")

        image_qos_profile = QoSProfile(
            reliability=self.image_reliability,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )

        # subs
        image_sub = message_filters.Subscriber(
            self, CompressedImage, "dbg_image/compressed", qos_profile=image_qos_profile
        )
        detections_sub = message_filters.Subscriber(
            self, DetectionArray, "tracking", qos_profile=10
        )

        self._synchronizer = message_filters.ApproximateTimeSynchronizer(
            (image_sub, detections_sub), 10, 0.5
        )
        self._synchronizer.registerCallback(self.tracking_cb)

        super().on_activate(state)
        self.get_logger().info(f"[{self.get_name()}] Activated")

        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Deactivating...")

        # Destroy subscribers (assuming they are stored as attributes)
        # self.destroy_subscription(image_sub.sub) # Need to store them as attributes
        # self.destroy_subscription(detections_sub.sub)

        del self._synchronizer
        self._synchronizer = None

        super().on_deactivate(state)
        self.get_logger().info(f"[{self.get_name()}] Deactivated")

        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Cleaning up...")

        self.destroy_publisher(self._pub)

        super().on_cleanup(state)
        self.get_logger().info(f"[{self.get_name()}] Cleaned up")

        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Shutting down...")
        super().on_cleanup(state)
        self.get_logger().info(f"[{self.get_name()}] Shutted down")
        return TransitionCallbackReturn.SUCCESS

    def tracking_cb(self, img_msg: CompressedImage, detections_msg: DetectionArray) -> None:

        # Decompress the image
        cv_image = cv2.imdecode(np.frombuffer(img_msg.data, np.uint8), cv2.IMREAD_COLOR)

        # Draw bounding boxes and IDs
        for detection in detections_msg.detections:
            bbox = detection.bbox
            track_id = detection.id

            # Convert relative coordinates to absolute pixel coordinates
            x_center = int(bbox.center.position.x)
            y_center = int(bbox.center.position.y)
            width = int(bbox.size.x)
            height = int(bbox.size.y)

            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)

            # Draw rectangle
            color = (0, 255, 0) # Green color
            thickness = 2
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), color, thickness)

            # Put text (ID)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_thickness = 2
            text_color = (0, 0, 255) # Red color for text
            cv2.putText(cv_image, str(track_id), (x1, y1 - 10), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

        # Publish the visualized image
        dbg_msg = CompressedImage()
        dbg_msg.header = img_msg.header
        dbg_msg.format = "jpeg"
        dbg_msg.data = np.array(cv2.imencode(".jpg", cv_image)[1]).tobytes()
        self._pub.publish(dbg_msg)


def main():
    rclpy.init()
    node = TrackingVisualizerNode()
    node.trigger_configure()
    node.trigger_activate()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
