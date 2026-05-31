import asyncio
import sys
import websockets
import krpc
import telemetry_pb2
from payload_builder import build_telemetry_payload

connected_clients = set()

def conectar_krpc():
    print("2. Intentando conectar a kRPC...")
    print("Conectando a KSP vía kRPC...")
    try:
        client = krpc.connect(
            name='KSP-Bridge',
            address='127.0.0.1',
            rpc_port=50000,
            stream_port=50001
        )
        print("¡Conexión establecida!")
        return client
    except Exception as err:
        print(f"Fallo total en la conexión: {err}")
        sys.exit(1)

async def broadcast_telemetry(krpc_client):
    """Equivalente al setInterval de 500ms de Node"""
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
            print(f"Error leyendo telemetría de KSP: {error}")
            for ws in list(connected_clients):
                await ws.close()
            sys.exit(1)

async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"¡Nuevo cliente conectado! Clientes totales: {len(connected_clients)}")
    
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"Cliente desconectado. Clientes totales: {len(connected_clients)}")

async def iniciar_bridge():
    try:
        print("1. Cargando Proto...")

        krpc_client = conectar_krpc()
        print("¡Conexión con KSP establecida!")

        server = await websockets.serve(ws_handler, "0.0.0.0", 27415)
        
        print("4. Servidor WebSocket levantado.")
        print("Bridge escuchando en el puerto 8080...")

        asyncio.create_task(broadcast_telemetry(krpc_client))

        await asyncio.Future()

    except Exception as e:
        print(f"\n[ERROR CRÍTICO]: {e}")
        print("Revisa que KSP esté abierto y el servidor kRPC en 'Running'.")
        sys.exit(1)

if __name__ == "__main__": 
    asyncio.run(iniciar_bridge())