import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import deque
import threading

class DHTMonitoringDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Monitoring Suhu & Kelembaban - DHT11")
        self.root.geometry("1200x600")
        self.root.configure(bg="#1e3a5f")
        
        # MQTT Configuration
        self.BROKER = "test.mosquitto.org"
        self.TOPIC_TEMP = "sensor/esp32/2/temperature"
        self.TOPIC_HUM = "sensor/esp32/2/humidity"
        self.TOPIC_LED_CONTROL = "sensor/esp32/2/led/control"
        self.TOPIC_LED_STATUS = "sensor/esp32/2/led/status"
        self.CLIENT_ID = "dashboard-monitor-2"
        
        # Data storage
        self.temp_data = deque(maxlen=50)
        self.hum_data = deque(maxlen=50)
        self.time_data = deque(maxlen=50)
        
        # LED Control State
        self.led_enabled = False
        
        # Statistics
        self.temp_sum = 0
        self.hum_sum = 0
        self.data_count = 0
        
        # Setup UI
        self.setup_ui()
        
        # Setup MQTT
        self.setup_mqtt()
        self.update_graphs()
        
    def setup_ui(self):
        """Setup User Interface"""
        # Header Frame
        header_frame = tk.Frame(self.root, bg="white", height=100)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        # Nama dan NIM
        title_label = tk.Label(
            header_frame, 
            text="DASHBOARD MONITORING SUHU & KELEMBABAN",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#1e3a5f"
        )
        title_label.pack(pady=5)
        
        info_label = tk.Label(
            header_frame,
            text="Arbath Abdurrahman | 23106050012",
            font=("Arial", 12),
            bg="white",
            fg="#34495e"
        )
        info_label.pack()
        
        # Main Content Frame
        content_frame = tk.Frame(self.root, bg="#1e3a5f")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left Panel
        left_panel = tk.Frame(content_frame, bg="white", width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)
        
        # Statistics Title
        stats_title = tk.Label(
            left_panel,
            text="📊 STATISTIK",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#1e3a5f"
        )
        stats_title.pack(pady=10)
        
        # Current Values Frame
        current_frame = tk.LabelFrame(
            left_panel,
            text="Nilai Saat Ini",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        current_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.current_temp_label = tk.Label(
            current_frame,
            text="Suhu: -- °C",
            font=("Arial", 12),
            bg="white",
            fg="#e74c3c"
        )
        self.current_temp_label.pack(pady=5)
        
        self.current_hum_label = tk.Label(
            current_frame,
            text="Kelembaban: -- %",
            font=("Arial", 12),
            bg="white",
            fg="#3498db"
        )
        self.current_hum_label.pack(pady=5)
        
        # Average Values Frame
        avg_frame = tk.LabelFrame(
            left_panel,
            text="Nilai Rata-rata",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        avg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.avg_temp_label = tk.Label(
            avg_frame,
            text="Rata-rata Suhu: -- °C",
            font=("Arial", 11),
            bg="white",
            fg="#c0392b"
        )
        self.avg_temp_label.pack(pady=5)
        
        self.avg_hum_label = tk.Label(
            avg_frame,
            text="Rata-rata Kelembaban: -- %",
            font=("Arial", 11),
            bg="white",
            fg="#2980b9"
        )
        self.avg_hum_label.pack(pady=5)
        
        # Connection Status
        self.status_label = tk.Label(
            left_panel,
            text="Status: Disconnected",
            font=("Arial", 10),
            bg="white",
            fg="#e74c3c"
        )
        self.status_label.pack(pady=10)
        
        # LED Control Frame
        control_frame = tk.LabelFrame(
            left_panel,
            text="Kontrol LED Indikator",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.led_button = tk.Button(
            control_frame,
            text="Enable LED",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            command=self.toggle_led,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3
        )
        self.led_button.pack(pady=10, padx=10, fill=tk.X)
        
        self.led_status_label = tk.Label(
            control_frame,
            text="LED: Disabled",
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d"
        )
        self.led_status_label.pack(pady=5)
        
        # Right Panel
        right_panel = tk.Frame(content_frame, bg="#2980b9")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup Matplotlib Figure
        self.fig = Figure(figsize=(10, 8), facecolor="#2980b9")
        
        # Temperature Graph
        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_facecolor("#ecf0f1")
        self.ax1.set_title("Grafik Suhu Real-time", fontsize=12, fontweight="bold", color="white")
        self.ax1.set_xlabel("Waktu", color="white")
        self.ax1.set_ylabel("Suhu (°C)", color="white")
        self.ax1.tick_params(colors="white")
        self.ax1.grid(True, alpha=0.3)
        
        # Humidity Graph
        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_facecolor("#ecf0f1")
        self.ax2.set_title("Grafik Kelembaban Real-time", fontsize=12, fontweight="bold", color="white")
        self.ax2.set_xlabel("Waktu", color="white")
        self.ax2.set_ylabel("Kelembaban (%)", color="white")
        self.ax2.tick_params(colors="white")
        self.ax2.grid(True, alpha=0.3)
        
        self.fig.tight_layout(pad=3.0)
        
        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_mqtt(self):
        """Setup MQTT Connection"""
        self.mqtt_client = mqtt.Client(self.CLIENT_ID)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            self.mqtt_client.connect(self.BROKER, 1883, 60)
            mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever, daemon=True)
            mqtt_thread.start()
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
            self.status_label.config(text=f"Status: Error - {e}", fg="#e74c3c")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat terhubung ke broker"""
        if rc == 0:
            print("Connected to MQTT Broker!")
            self.status_label.config(text="Status: Connected", fg="#27ae60")
            client.subscribe(self.TOPIC_TEMP)
            client.subscribe(self.TOPIC_HUM)
        else:
            print(f"Connection failed with code {rc}")
            self.status_label.config(text=f"Status: Failed (RC: {rc})", fg="#e74c3c")
    
    def on_message(self, client, userdata, msg):
        """Callback saat menerima pesan"""
        try:
            payload = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if msg.topic == self.TOPIC_TEMP:
                temp = payload.get("temperature")
                if temp is not None:
                    self.temp_data.append(temp)
                    self.time_data.append(timestamp)
                    self.temp_sum += temp
                    self.data_count += 1
                    self.current_temp_label.config(text=f"Suhu: {temp:.1f} °C")
                    
            elif msg.topic == self.TOPIC_HUM:
                hum = payload.get("humidity")
                if hum is not None:
                    self.hum_data.append(hum)
                    self.current_hum_label.config(text=f"Kelembaban: {hum:.1f} %")
                    self.hum_sum += hum
                    
            # Update averages
            if self.data_count > 0:
                avg_temp = self.temp_sum / self.data_count
                avg_hum = self.hum_sum / self.data_count
                self.avg_temp_label.config(text=f"Rata-rata Suhu: {avg_temp:.2f} °C")
                self.avg_hum_label.config(text=f"Rata-rata Kelembaban: {avg_hum:.2f} %")
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def toggle_led(self):
        """Toggle LED control"""
        self.led_enabled = not self.led_enabled
        
        if self.led_enabled:
            self.mqtt_client.publish(self.TOPIC_LED_CONTROL, "ON")
            self.led_button.config(text="Disable LED", bg="#e74c3c")
            self.led_status_label.config(text="LED: Enabled", fg="#27ae60")
        else:
            self.mqtt_client.publish(self.TOPIC_LED_CONTROL, "OFF")
            self.led_button.config(text="Enable LED", bg="#27ae60")
            self.led_status_label.config(text="LED: Disabled", fg="#7f8c8d")
    
    def get_temp_color(self, temp):
        """Dapatkan warna berdasarkan suhu"""
        if temp > 30:
            return "#e74c3c"  # Merah
        elif 25 <= temp <= 30:
            return "#f39c12"  # Kuning
        else:
            return "#27ae60"  # Hijau
    
    def update_graphs(self):
        """Update grafik secara real-time"""
        if len(self.temp_data) > 0:
            self.ax1.clear()
            self.ax2.clear()
            
            # Temperature graph dengan warna dinamis
            for i in range(len(self.temp_data)):
                color = self.get_temp_color(self.temp_data[i])
                if i > 0:
                    self.ax1.plot(
                        [i-1, i], 
                        [self.temp_data[i-1], self.temp_data[i]], 
                        color=color, 
                        linewidth=2,
                        marker='o'
                    )
            
            self.ax1.set_facecolor("#ecf0f1")
            self.ax1.set_title("Grafik Suhu Real-time", fontsize=12, fontweight="bold", color="white")
            self.ax1.set_xlabel("Data Point", color="white")
            self.ax1.set_ylabel("Suhu (°C)", color="white")
            self.ax1.tick_params(colors="white")
            self.ax1.grid(True, alpha=0.3)
            
            # Humidity graph
            self.ax2.plot(self.hum_data, color="#3498db", linewidth=2, marker='o')
            self.ax2.set_facecolor("#ecf0f1")
            self.ax2.set_title("Grafik Kelembaban Real-time", fontsize=12, fontweight="bold", color="white")
            self.ax2.set_xlabel("Data Point", color="white")
            self.ax2.set_ylabel("Kelembaban (%)", color="white")
            self.ax2.tick_params(colors="white")
            self.ax2.grid(True, alpha=0.3)
            
            self.fig.tight_layout(pad=3.0)
            self.canvas.draw()

        self.root.after(1000, self.update_graphs)

def main():
    root = tk.Tk()
    app = DHTMonitoringDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()