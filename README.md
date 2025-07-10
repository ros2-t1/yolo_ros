# YOLO ROS 패키지 수정 사항

이 `README.md` 파일은 `yolo_ros` 패키지에 적용된 수정 사항을 요약하며, 주로 압축 이미지 입력 활성화, 추적 디버그 시각화 추가, 그리고 전반적인 견고성 향상에 중점을 둡니다.

## 1. `yolo_bringup/launch/yolov8_compressed.launch.py`

-   **목적**: 압축 이미지 입력을 사용하여 YOLOv8 노드를 실행하고 추적 관련 노드의 활성화를 제어하도록 수정되었습니다.
-   **변경 사항**:
    -   `input_image_topic`의 기본값이 `/camera/rgb/image_raw/compressed`로 변경되어 압축 이미지 스트림을 사용합니다.
    -   `use_tracking` 런치 인수를 `False`의 기본값으로 추가했습니다. 이를 통해 사용자는 이 런치 파일에서 직접 추적 및 시각화를 활성화/비활성화할 수 있습니다.

## 2. `yolo_bringup/launch/yolo.launch.py`

-   **목적**: 다른 런치 파일에 의해 포함되는 핵심 런치 파일입니다. 여기에서의 수정은 다양한 YOLO 관련 노드의 실행을 제어합니다.
-   **변경 사항**:
    -   `use_debug` 런치 인수의 기본값이 `True`에서 `False`로 변경되었습니다. `comp_yolo_node`가 이제 디버그 이미지 발행을 처리하므로, 기본적으로 원래의 `debug_node`를 비활성화합니다.
    -   `tracking_visualizer_node`를 런치 설명에 추가했습니다. 이 노드는 `use_tracking` 인수에 따라 조건부로 실행되도록 설정되어, 추적이 활성화될 때만 실행됩니다.

## 3. `yolo_ros/yolo_ros/comp_yolo_node.py`

-   **목적**: 주요 YOLO 감지 노드입니다. 압축 이미지 입력을 처리하고 디버그 시각화를 발행하도록 수정되었습니다.
-   **변경 사항**:
    -   **입력 이미지 처리**: `cv_bridge.imgmsg_to_cv2` 대신 `cv2.imdecode`를 사용하여 `sensor_msgs/msg/CompressedImage`를 직접 디코딩하도록 변경되었습니다.
    -   **디버그 이미지 출력**:
        -   디버그 이미지 발행을 제어하는 `enable_debug` 매개변수를 추가했습니다.
        -   `cv_bridge`와 디버그 이미지를 위한 새로운 발행자(`_dbg_pub`)를 초기화했습니다.
        -   디버그 이미지 토픽을 `/yolo/dbg_image/compressed`로 변경하고, ROS 이미지 전송 규칙을 따르기 위해 메시지 타입을 `sensor_msgs/msg/CompressedImage`로 변경했습니다.
        -   객체가 감지되지 않을 때 `IndexError`를 방지하기 위해 디버그 이미지 발행 로직을 `results[0].plot()` 대신 `results.plot()`을 사용하도록 업데이트했습니다.
        -   발행 전에 디버그 이미지를 JPEG로 압축하는 기능을 구현했습니다.
    -   **정리**: 노드 정리 중에 `_dbg_pub`가 올바르게 파괴되도록 보장했습니다.

## 4. `yolo_ros/yolo_ros/tracking_node.py`

-   **목적**: YOLO 감지를 기반으로 객체 추적을 처리합니다. 압축 이미지 입력을 받도록 수정되었습니다.
-   **변경 사항**:
    -   **입력 이미지 처리**: 구독하는 이미지 메시지 타입을 `sensor_msgs/msg/Image`에서 `sensor_msgs/msg/CompressedImage`로 변경했습니다.
    -   **이미지 디코딩**: `detections_cb` 콜백을 수정하여 `CompressedImage`를 `cv2.imdecode`를 사용하여 OpenCV 이미지로 디코딩하도록 했습니다.
    -   **이미지 차원**: `AttributeError`를 해결하기 위해 `Boxes` 초기화 시 이미지 차원을 `CompressedImage` 메시지 대신 디코딩된 OpenCV 이미지(`cv_image.shape`)에서 올바르게 가져오도록 업데이트했습니다.

## 5. `yolo_ros/yolo_ros/tracking_visualizer_node.py` (새 파일)

-   **목적**: 추적 결과를 디버그 이미지에 시각화하기 위해 새로 생성된 노드입니다.
-   **기능**:
    -   `/yolo/dbg_image/compressed` (comp_yolo_node의 디버그 이미지)와 `/yolo/tracking` (tracking_node의 추적 결과) 토픽을 구독합니다.
    -   `message_filters.ApproximateTimeSynchronizer`를 사용하여 이 두 토픽을 동기화합니다.
    -   콜백에서 압축된 이미지를 디코딩하고, `DetectionArray`에서 가져온 바운딩 박스와 추적 ID를 이미지 위에 그립니다.
    -   시각화된 이미지를 `sensor_msgs/msg/CompressedImage` 타입으로 `/yolo/tracking_dbg_image/compressed`에 발행합니다.

## 6. `yolo_ros/setup.py`

-   **목적**: Python 패키지 및 실행 파일이 빌드되고 설치되는 방식을 정의합니다.
-   **변경 사항**:
    -   `console_scripts` 진입점에 `tracking_visualizer_node = yolo_ros.tracking_visualizer_node:main`을 추가하여 새로운 시각화 노드를 실행 가능하게 만들었습니다.

---

## 리소스 사용량 모니터링

YOLO ROS 노드가 PC에 가하는 계산 부하를 이해하려면 CPU, RAM 및 GPU 사용량을 모니터링할 수 있습니다.

### 1. CPU 및 RAM 사용량 (`htop` 또는 `top`)

`htop`은 `top`보다 더 사용자 친화적이고 시각적인 인터페이스를 제공합니다. 설치되어 있지 않다면 `sudo apt install htop`으로 설치할 수 있습니다.

**단계:**
1.  YOLO ROS 런치 파일을 시작합니다:
    ```bash
    ros2 launch yolo_bringup yolov8_compressed.launch.py
    ```
2.  새 터미널을 열고 `htop`을 실행합니다:
    ```bash
    htop
    ```
3.  `htop`에서 `F4` (필터)를 누르고 `python` 또는 `ros`를 입력하여 관련 프로세스만 필터링할 수 있습니다.
4.  **관찰할 주요 지표:**
    *   **%CPU**: 프로세스가 소비하는 CPU 시간의 백분율입니다. 높은 백분율(예: 단일 코어의 경우 >80%, 멀티 코어 프로세스의 경우 >100%)은 높은 CPU 사용량을 나타냅니다.
    *   **RES (Resident Set Size)**: 프로세스가 현재 사용 중인 실제 물리적 RAM(MiB 또는 GiB 단위)입니다. RAM 사용량에 대한 가장 중요한 지표입니다.
    *   **%MEM**: 프로세스가 사용하는 전체 시스템 RAM의 백분율입니다.

### 2. GPU 사용량 (`nvidia-smi`)

NVIDIA GPU를 사용하고 있다면 `nvidia-smi`는 성능 모니터링을 위한 표준 도구입니다.

**단계:**
1.  YOLO ROS 런치 파일을 시작합니다:
    ```bash
    ros2 launch yolo_bringup yolov8_compressed.launch.py
    ```
2.  다른 새 터미널을 열고 새로 고침 간격과 함께 `nvidia-smi`를 실행합니다:
    ```bash
    watch -n 0.5 nvidia-smi
    ```
    (이것은 0.5초마다 출력을 새로 고칩니다.)
3.  **관찰할 주요 지표:**
    *   **GPU-Util**: GPU의 처리 장치가 활발하게 작동하는 시간의 백분율입니다. 높은 값(예: >70%)은 GPU가 계산에 많이 활용되고 있음을 나타냅니다.
    *   **Memory-Usage**: `XXXXMiB / YYYYMiB` 형식으로 표시되며, `XXXXMiB`는 현재 사용 중인 GPU 메모리이고, `YYYYMiB`는 사용 가능한 총 GPU 메모리입니다.
    *   **Processes 섹션**: 하단에는 현재 GPU를 사용하는 프로세스 목록과 해당 GPU 메모리 소비량이 표시됩니다. 여기서 `python3` 또는 `ros` 관련 프로세스를 찾아보세요.

YOLO 노드가 실행되는 동안 이러한 지표를 관찰함으로써 시스템의 CPU, RAM 및 GPU 리소스에 가하는 부하를 측정할 수 있습니다.
