import asyncio
import sys
import websockets
import krpc
import telemetry_pb2
from payload_builder import build_telemetry_payload

connected_clients = set()

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
    while True:
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
            sys.exit(1)

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

if __name__ == "__main__": 
    asyncio.run(start_bridge())