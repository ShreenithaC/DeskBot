#!/usr/bin/env python3
"""Simple motor test - spins motor once."""

import time

try:
    from adafruit_motorkit import MotorKit
    kit = MotorKit()
    motor = kit.motor2
    
    print("Motor test starting...")
    print("Spinning motor for 1 rotation...")
    
    # Spin motor at full speed for ~1 second (adjust time for your motor)
    motor.throttle = 1.0
    time.sleep(1.0)
    
    # Stop motor
    motor.throttle = 0
    
    print("Done!")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure I2C is enabled:")
    print("  sudo raspi-config")
    print("  -> Interface Options -> I2C -> Enable")

