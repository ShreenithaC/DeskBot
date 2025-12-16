"""
Motor control module for face tracking.
Controls DC motors via Adafruit MotorKit.
"""

# Motor control settings
DEAD_ZONE = 50  # Pixels from center where motor won't move
MOTOR_SPEED = 1.0  # Motor speed (0.0 to 1.0)

# Initialize motors
try:
    from adafruit_motorkit import MotorKit
    kit = MotorKit()
    motor1 = kit.motor1  # M1 - horizontal (left/right)
    motor2 = kit.motor2  # M2 - vertical (up/down)
    MOTOR_AVAILABLE = True
    print("Motors initialized on M1 and M2")
except Exception as e:
    print(f"Motors not available: {e}")
    MOTOR_AVAILABLE = False
    motor1 = None
    motor2 = None


def control_motors(offset_x, offset_y):
    """Control motors based on face offset from center."""
    if not MOTOR_AVAILABLE:
        return
    
    # Horizontal control (M1)
    if motor1 is not None:
        if offset_x > DEAD_ZONE:
            # Face is to the right, turn motor to follow
            motor1.throttle = -MOTOR_SPEED
        elif offset_x < -DEAD_ZONE:
            # Face is to the left, turn motor to follow
            motor1.throttle = MOTOR_SPEED
        else:
            motor1.throttle = 0
    
    # Vertical control (M2)
    if motor2 is not None:
        if offset_y > DEAD_ZONE:
            # Face is too low, turn motor to follow
            motor2.throttle = MOTOR_SPEED
        elif offset_y < -DEAD_ZONE:
            # Face is too high, turn motor to follow
            motor2.throttle = -MOTOR_SPEED
        else:
            motor2.throttle = 0


def stop_motors():
    """Stop both motors."""
    if MOTOR_AVAILABLE:
        if motor1 is not None:
            motor1.throttle = 0
        if motor2 is not None:
            motor2.throttle = 0
        print("Motors stopped")
