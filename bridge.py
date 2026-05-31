import asyncio
import sys
import websockets
import krpc
import telemetry_pb2
from payload_builder import build_telemetry_payload
import tkinter as tk
from tkinter import ttk, messagebox
import threading

connected_clients = set()
bridge_running = False
krpc_client = None
websocket_server = None
broadcast_task = None

ip = '127.0.0.1'
port = 50000

kappi_ip = '0.0.0.0'
kappi_port = 27415

def connect_krpc():
    print("2. Intentando conectar a kRPC...")
    print("Conectando a KSP vía kRPC...")
    try:
        client = krpc.connect(
            name='KSP-Bridge',
            address=ip,
            rpc_port=port,
            stream_port=50001
        )
        print(f"Conectado a kRPC en {ip}:{port}")
        return client
    except Exception as err:
        print(f"Fallo al intentar conectarse: {err}")
        sys.exit(1)

async def broadcast_telemetry(krpc_client):
    while bridge_running:
        await asyncio.sleep(0.1)
        print("Running Async Interval")

        if not connected_clients:
            continue

        try:
            scene = krpc_client.krpc.current_game_scene
            if scene != krpc_client.krpc.GameScene.flight:
                continue

            vessel = krpc_client.space_center.active_vessel
            if not vessel:
                continue

            payload = build_telemetry_payload(vessel, krpc_client)

            message = telemetry_pb2.KspTelemetry(**payload)
            buffer = message.SerializeToString()

            websockets.broadcast(connected_clients, buffer)

        except Exception as error:
            print(f"Error al parsear telemetría: {error}")
            for ws in list(connected_clients):
                await ws.close()
            break

async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"+Cliente, conectados: {len(connected_clients)}")
    
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"-Cliente, conectados: {len(connected_clients)}")

async def start_bridge():
    try:
        print("1. Cargando Proto...")

        krpc_client = connect_krpc()
        print("¡Conexión con KSP establecida!")

        server = await websockets.serve(ws_handler, kappi_ip, kappi_port)
        
        print("4. Servidor WebSocket levantado.")
        print(f"Bridge abierto en ws://{kappi_ip}:{kappi_port}")

        asyncio.create_task(broadcast_telemetry(krpc_client))

        await asyncio.Future()

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

async def start_async_bridge():
    global websocket_server, broadcast_task
    
    try:
        print("4. Servidor WebSocket levantado.")
        print(f"Bridge abierto en ws://{kappi_ip}:{kappi_port}")

        websocket_server = await websockets.serve(ws_handler, kappi_ip, kappi_port)
        
        broadcast_task = asyncio.create_task(broadcast_telemetry(krpc_client))
        
        while bridge_running:
            await asyncio.sleep(1)
        
        websocket_server.close()
        await websocket_server.wait_closed()
        
        for ws in list(connected_clients):
            await ws.close()

    except Exception as e:
        print(f"\n[ERROR]: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("KSP Bridge Control")
    root.resizable(False, False)
    root.geometry("200x360")
    
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    title_label = ttk.Label(main_frame, text="KSP Bridge Control", font=("Arial", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=10)
    
    config_frame = ttk.LabelFrame(main_frame, text="kRPC Configuration", padding="10")
    config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
    
    ttk.Label(config_frame, text="IP:").grid(row=0, column=0, sticky=tk.W)
    krpc_ip_entry = ttk.Entry(config_frame, width=20)
    krpc_ip_entry.insert(0, ip)
    krpc_ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
    
    ttk.Label(config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
    krpc_port_entry = ttk.Entry(config_frame, width=20)
    krpc_port_entry.insert(0, str(port))
    krpc_port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
    
    ws_frame = ttk.LabelFrame(main_frame, text="WebSocket Configuration", padding="10")
    ws_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
    
    ttk.Label(ws_frame, text="IP:").grid(row=0, column=0, sticky=tk.W)
    ws_ip_entry = ttk.Entry(ws_frame, width=20)
    ws_ip_entry.insert(0, kappi_ip)
    ws_ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
    
    ttk.Label(ws_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
    ws_port_entry = ttk.Entry(ws_frame, width=20)
    ws_port_entry.insert(0, str(kappi_port))
    ws_port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
    
    status_label = ttk.Label(main_frame, text="Status: Stopped", foreground="red", font=("Arial", 10, "bold"))
    status_label.grid(row=3, column=0, columnspan=2, pady=10)
    
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=4, column=0, columnspan=2, pady=10)
    
    def start_bridge_gui():
        global bridge_running, krpc_client, websocket_server, broadcast_task, ip, port, kappi_ip, kappi_port
        
        try:
            ip = krpc_ip_entry.get()
            port = int(krpc_port_entry.get())
            kappi_ip = ws_ip_entry.get()
            kappi_port = int(ws_port_entry.get())
            
            krpc_ip_entry.config(state='disabled')
            krpc_port_entry.config(state='disabled')
            ws_ip_entry.config(state='disabled')
            ws_port_entry.config(state='disabled')
            start_btn.config(state='disabled')
            
            status_label.config(text="Status: Connecting...", foreground="orange")
            root.update()
            
            def run_bridge():
                global bridge_running, krpc_client, websocket_server, broadcast_task
                
                try:
                    print("1. Cargando Proto...")
                    krpc_client = connect_krpc()
                    print("¡Conexión con KSP establecida!")
                    
                    asyncio.run(start_async_bridge())
                except Exception as e:
                    print(f"\n[ERROR]: {e}")
                    bridge_running = False
                    status_label.config(text="Status: Error", foreground="red")
                    krpc_ip_entry.config(state='normal')
                    krpc_port_entry.config(state='normal')
                    ws_ip_entry.config(state='normal')
                    ws_port_entry.config(state='normal')
                    start_btn.config(state='normal')
                    stop_btn.config(state='disabled')
                    messagebox.showerror("Error", f"Error al iniciar el bridge: {e}")
            
            bridge_running = True
            bridge_thread = threading.Thread(target=run_bridge, daemon=True)
            bridge_thread.start()
            
            status_label.config(text="Status: Running", foreground="green")
            stop_btn.config(state='normal')
            
        except ValueError:
            messagebox.showerror("Error", "Puerto debe ser un número válido")
    
    def stop_bridge_gui():
        global bridge_running
        bridge_running = False
        status_label.config(text="Status: Stopping...", foreground="orange")
        root.update()
        
        krpc_ip_entry.config(state='normal')
        krpc_port_entry.config(state='normal')
        ws_ip_entry.config(state='normal')
        ws_port_entry.config(state='normal')
        start_btn.config(state='normal')
        stop_btn.config(state='disabled')
        
        status_label.config(text="Status: Stopped", foreground="red")
    
    start_btn = ttk.Button(button_frame, text="Start Bridge", command=start_bridge_gui)
    start_btn.grid(row=0, column=0, padx=5)
    
    stop_btn = ttk.Button(button_frame, text="Stop Bridge", command=stop_bridge_gui, state='disabled')
    stop_btn.grid(row=0, column=1, padx=5)
    
    root.mainloop()