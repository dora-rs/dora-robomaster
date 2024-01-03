import cv2
import pyarrow as pa
from dora import Node

node = Node()
# TCP stream URL (replace with your stream URL)
TCP_STREAM_URL = "tcp://192.168.2.1:40921"
# Global variables, change it to adapt your needs
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Create a VideoCapture object using the TCP stream URL
cap = cv2.VideoCapture(TCP_STREAM_URL)

# Check if the VideoCapture object opened successfully
assert cap.isOpened(), "Error: Could not open video capture."

while True:
    # Read a frame from the stream
    ret, frame = cap.read()

    if not ret:
        break  # Break the loop when no more frames are available
    frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))

    node.send_output("image", pa.array(frame.ravel()))


# Release the VideoCapture object and any OpenCV windows
cap.release()
cv2.destroyAllWindows()
