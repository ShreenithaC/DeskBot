# Face Tracking for Raspberry Pi

A simple face tracking script using OpenCV that detects faces from a USB webcam.

## Setup

### 1. Install system dependencies (required for OpenCV on Raspberry Pi)

```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv libatlas-base-dev
```

### 2. Install Python packages

```bash
cd ~/face_tracking
pip3 install -r requirements.txt
```

**Note:** On Raspberry Pi OS, you might need to use `--break-system-packages` flag or create a virtual environment:

```bash
# Option A: Use system packages (recommended for Pi)
pip3 install -r requirements.txt --break-system-packages

# Option B: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the face tracker:

```bash
python3 face_tracker.py
```

### Controls
- Press **'q'** to quit the application

### What it does
- Draws green rectangles around detected faces
- Shows a red dot at the center of each face
- Displays the offset from the frame center (useful for servo control)
- Shows face count on screen
- Prints tracking coordinates to the console

## Troubleshooting

### Camera not detected
- Try changing `camera_index` in the script to `1` or `2`
- Check if camera is recognized: `ls /dev/video*`
- Test camera: `v4l2-ctl --list-devices`

### Performance issues
- Reduce resolution in the script (320x240)
- Increase `scaleFactor` to 1.2 or 1.3
- Increase `minNeighbors` to reduce false positives

### No display (headless mode)
If running via SSH without a display, the `cv2.imshow()` won't work. 
You can modify the script to only print coordinates to console.
