#!/usr/bin/env python3
import serial
import time
import threading
from flask import Flask, render_template, jsonify, request
import rclpy
from rclpy.node import Node

app = Flask(__name__)

class CNCNode(Node):
    def __init__(self):
        super().__init__('cnc_web_server')
        self.ser = None
        self.step = 1
        self.work_zero = {'X': 0, 'Y': 0, 'Z': 0}
        self.saved_home = {'X': 0, 'Y': 0, 'Z': 0}
        self.machine_limit = {'X': 300, 'Y': 180, 'Z': 45}
        self.get_logger().info('CNC Node Started')
        
    def connect(self):
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            time.sleep(2)
            self.send("$X")
            self.send("G91")
            self.get_logger().info('Connected to CNC')
            return True
        except Exception as e:
            self.get_logger().error(f'Connection failed: {e}')
            return False
    
    def send(self, cmd):
        if self.ser:
            self.ser.write((cmd + "\n").encode())
            self.get_logger().debug(f'Sent: {cmd}')
    
    def jog(self, axis, direction):
        self.send(f"G0 {axis}{direction * self.step}")
    
    def spindle(self, state):
        self.send("M3 S1000" if state == "on" else "M5")
    
    def set_step(self, step):
        self.step = step
    
    def home(self):
        """Return to machine zero (limit switches)"""
        self.send("G28 X0 Y0 Z0")
    
    def set_work_zero(self):
        """Set current position as work zero (G92)"""
        self.send("G92 X0 Y0 Z0")
        self.work_zero = {'X': 0, 'Y': 0, 'Z': 0}
        self.get_logger().info('Work zero set at current position')
    
    def return_to_work_zero(self):
        """Return to work zero position"""
        self.send("G90")
        self.send("G0 X0 Y0 Z0")
        self.send("G91")
        self.get_logger().info('Returning to work zero')
    
    def save_home_position(self):
        """Save current position as home position"""
        self.send("G92.1")
        self.send("G92 X0 Y0 Z0")
        self.saved_home = {'X': 0, 'Y': 0, 'Z': 0}
        self.get_logger().info('Home position saved')
        return True
    
    def return_to_saved_home(self):
        """Return to saved home position"""
        self.send("G90")
        self.send("G0 X0 Y0 Z0")
        self.send("G91")
        self.get_logger().info('Returning to saved home')
    
    def soft_reset(self):
        """Soft reset controller"""
        self.send("$X")
        self.send("G91")
        self.get_logger().info('Soft reset completed')
    
    def calibrate_axis(self, axis, max_position):
        """Set machine limit for specific axis"""
        if axis in self.machine_limit:
            self.machine_limit[axis] = max_position
            self.get_logger().info(f'Calibrated {axis} limit to {max_position}mm')
            return True
        return False
    
    def emergency_stop(self):
        self.send("M112")
        self.get_logger().warn('EMERGENCY STOP triggered')

# Inisialisasi ROS2
rclpy.init(args=None)
cnc_node = CNCNode()
cnc_node.connect()

# Jalankan ROS2 di thread terpisah
def ros_spin():
    rclpy.spin(cnc_node)

thread = threading.Thread(target=ros_spin)
thread.start()

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/jog', methods=['POST'])
def api_jog():
    data = request.json
    cnc_node.jog(data['axis'], data['direction'])
    return jsonify({"status": "ok"})

@app.route('/api/spindle', methods=['POST'])
def api_spindle():
    data = request.json
    cnc_node.spindle(data['state'])
    return jsonify({"status": "ok"})

@app.route('/api/step', methods=['POST'])
def api_step():
    data = request.json
    cnc_node.set_step(data['step'])
    return jsonify({"status": "ok"})

@app.route('/api/home', methods=['POST'])
def api_home():
    cnc_node.home()
    return jsonify({"status": "ok"})

@app.route('/api/set_work_zero', methods=['POST'])
def api_set_work_zero():
    cnc_node.set_work_zero()
    return jsonify({"status": "ok"})

@app.route('/api/return_to_work_zero', methods=['POST'])
def api_return_to_work_zero():
    cnc_node.return_to_work_zero()
    return jsonify({"status": "ok"})

@app.route('/api/save_home', methods=['POST'])
def api_save_home():
    cnc_node.save_home_position()
    return jsonify({"status": "ok"})

@app.route('/api/return_home', methods=['POST'])
def api_return_home():
    cnc_node.return_to_saved_home()
    return jsonify({"status": "ok"})

@app.route('/api/soft_reset', methods=['POST'])
def api_soft_reset():
    cnc_node.soft_reset()
    return jsonify({"status": "ok"})

@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    data = request.json
    success = cnc_node.calibrate_axis(data['axis'], data['max_position'])
    return jsonify({"status": "ok" if success else "failed"})

@app.route('/api/emergency', methods=['POST'])
def api_emergency():
    cnc_node.emergency_stop()
    return jsonify({"status": "ok"})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        "status": "connected", 
        "step": cnc_node.step,
        "work_zero": cnc_node.work_zero,
        "machine_limit": cnc_node.machine_limit,
        "saved_home": cnc_node.saved_home
    })

def main():
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        cnc_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()