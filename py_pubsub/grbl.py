import serial
import time
import tkinter as tk
import sys

class GRBLController:
    def __init__(self):
        self.ser = None
        self.step = 1
        self.jogging = False
        
    def connect(self, port='/dev/ttyUSB0', baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate)
            time.sleep(2)
            self.send("$X")
            self.send("G91")
            return True
        except serial.SerialException as e:
            print(f"Error: Cannot open {port}")
            print("Check: USB connected? Forwarded to WSL?")
            return False
    
    def send(self, cmd):
        if self.ser:
            self.ser.write((cmd + "\n").encode())
    
    def jog(self, axis, direction):
        if self.jogging:
            self.send(f"G0 {axis}{direction*self.step}")
            self.root.after(100, lambda: self.jog(axis, direction))
    
    def start_jog(self, axis, direction):
        self.jogging = True
        self.jog(axis, direction)
    
    def stop_jog(self, event=None):
        self.jogging = False
    
    def spindle(self):
        self.send("M3 S1000")
    
    def change_step(self):
        if self.step == 0.1:
            self.step = 1
        elif self.step == 1:
            self.step = 5
        elif self.step == 5:
            self.step = 10
        else:
            self.step = 0.1
        self.step_label.config(text=f"STEP: {self.step}mm")
    
    def run_gui(self):
        self.root = tk.Tk()
        self.root.title("GRBL Controller")
        
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        
        self.step_label = tk.Label(self.root, text="STEP: 1mm")
        self.step_label.pack()
        
        # Buttons
        btn_y_plus = tk.Button(frame, text="Y+", width=8, height=2)
        btn_y_plus.grid(row=0, column=1)
        
        btn_x_minus = tk.Button(frame, text="X-", width=8, height=2)
        btn_x_minus.grid(row=1, column=0)
        
        btn_x_plus = tk.Button(frame, text="X+", width=8, height=2)
        btn_x_plus.grid(row=1, column=2)
        
        btn_y_minus = tk.Button(frame, text="Y-", width=8, height=2)
        btn_y_minus.grid(row=2, column=1)
        
        btn_z_plus = tk.Button(frame, text="Z+", width=8, height=2)
        btn_z_plus.grid(row=0, column=3)
        
        btn_z_minus = tk.Button(frame, text="Z-", width=8, height=2)
        btn_z_minus.grid(row=2, column=3)
        
        tk.Button(frame, text="Spindle", width=8, height=2, command=self.spindle).grid(row=1, column=3)
        tk.Button(frame, text="Step", width=8, height=2, command=self.change_step).grid(row=3, column=1)
        
        # Bind events
        btn_x_plus.bind("<ButtonPress-1>", lambda e: self.start_jog("X", 1))
        btn_x_plus.bind("<ButtonRelease-1>", self.stop_jog)
        btn_x_minus.bind("<ButtonPress-1>", lambda e: self.start_jog("X", -1))
        btn_x_minus.bind("<ButtonRelease-1>", self.stop_jog)
        btn_y_plus.bind("<ButtonPress-1>", lambda e: self.start_jog("Y", 1))
        btn_y_plus.bind("<ButtonRelease-1>", self.stop_jog)
        btn_y_minus.bind("<ButtonPress-1>", lambda e: self.start_jog("Y", -1))
        btn_y_minus.bind("<ButtonRelease-1>", self.stop_jog)
        btn_z_plus.bind("<ButtonPress-1>", lambda e: self.start_jog("Z", 1))
        btn_z_plus.bind("<ButtonRelease-1>", self.stop_jog)
        btn_z_minus.bind("<ButtonPress-1>", lambda e: self.start_jog("Z", -1))
        btn_z_minus.bind("<ButtonRelease-1>", self.stop_jog)
        
        self.root.mainloop()

def main(args=None):
    cnc = GRBLController()
    if cnc.connect():
        cnc.run_gui()
    else:
        return 1

if __name__ == "__main__":
    main()