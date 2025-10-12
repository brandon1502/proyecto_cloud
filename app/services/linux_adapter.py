import time
from sqlalchemy import text

def simulate_slice_creation(db, slice_id: int):
    steps = [
        "Crear namespace",
        "Crear interfaz veth",
        "Conectar al OvS",
        "Asignar VLAN",
        "Levantar DHCP",
        "Finalizar slice"
    ]

    for step in steps:
        db.execute(
            text("INSERT INTO slice_events (slice_id, step_name, status) VALUES (:sid, :step, 'ok')"),
            {"sid": slice_id, "step": step}
        )
        db.commit()
        print(f"[Simulación] Slice {slice_id}: {step}")
        time.sleep(0.5)  # simula el tiempo entre pasos

    # Cambiar estado a 'active' al terminar
    db.execute(
        text("UPDATE slices SET status='active' WHERE slice_id=:sid"),
        {"sid": slice_id}
    )
    db.commit()
    print(f"[Simulación] Slice {slice_id} completado ✅")
