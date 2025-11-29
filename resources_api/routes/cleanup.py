"""
Endpoints para limpieza y mantenimiento de recursos
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..schemas import MessageResponse

router = APIRouter()


@router.post("/orphaned-resources", response_model=MessageResponse)
async def cleanup_orphaned_resources(
    db: Session = Depends(get_db)
):
    """
    Liberar recursos huérfanos (VLANs y VNC ports marcados como usados pero sin slice/VM válido)
    
    Este endpoint:
    - Libera VLANs marcadas como usadas pero con slice_id NULL o apuntando a slices que no existen
    - Libera VNC ports marcados como usados pero con vm_id NULL o apuntando a VMs que no existen
    - Es seguro ejecutarlo periódicamente
    """
    try:
        # Liberar VLANs huérfanas (en uso pero sin slice válido)
        vlans_query = text("""
            UPDATE vlans v
            LEFT JOIN slices s ON v.slice_id = s.slice_id
            SET v.is_used = 0, 
                v.slice_id = NULL, 
                v.reserved_at = NULL, 
                v.reserved_by = NULL
            WHERE v.is_used = 1 
              AND (v.slice_id IS NULL OR s.slice_id IS NULL)
        """)
        vlans_result = db.execute(vlans_query)
        vlans_freed = vlans_result.rowcount
        
        # Liberar VNC ports huérfanos (en uso pero sin VM válida)
        vnc_query = text("""
            UPDATE vnc_ports vp
            LEFT JOIN vms v ON vp.vm_id = v.vm_id
            SET vp.is_used = 0,
                vp.vm_id = NULL,
                vp.slice_id = NULL,
                vp.reserved_at = NULL,
                vp.reserved_by = NULL
            WHERE vp.is_used = 1
              AND (vp.vm_id IS NULL OR v.vm_id IS NULL)
        """)
        vnc_result = db.execute(vnc_query)
        vnc_freed = vnc_result.rowcount
        
        db.commit()
        
        return MessageResponse(
            message="Limpieza de recursos huérfanos completada exitosamente",
            detail={
                "vlans_liberadas": vlans_freed,
                "vnc_ports_liberados": vnc_freed
            }
        )
    except Exception as e:
        db.rollback()
        return MessageResponse(
            message=f"Error durante la limpieza: {str(e)}",
            detail={"error": True}
        )


@router.post("/failed-slices", response_model=MessageResponse)
async def cleanup_failed_slices(
    db: Session = Depends(get_db)
):
    """
    Eliminar slices fallidos y liberar sus recursos
    
    - Libera VLANs asociadas a slices con status 'failed' o 'error'
    - Libera VNC ports de VMs de slices fallidos
    - Elimina VMs de slices fallidos
    - Elimina los slices fallidos
    """
    try:
        # 1. Liberar VNC ports de VMs de slices fallidos
        vnc_query = text("""
            UPDATE vnc_ports vp
            JOIN vms v ON vp.vm_id = v.vm_id
            JOIN slices s ON v.slice_id = s.slice_id
            SET vp.is_used = 0, 
                vp.vm_id = NULL, 
                vp.slice_id = NULL, 
                vp.reserved_at = NULL, 
                vp.reserved_by = NULL
            WHERE s.status IN ('failed', 'error')
        """)
        vnc_result = db.execute(vnc_query)
        vnc_freed = vnc_result.rowcount
        
        # 2. Liberar VLANs de slices fallidos
        vlans_query = text("""
            UPDATE vlans v
            JOIN slices s ON v.slice_id = s.slice_id
            SET v.is_used = 0, 
                v.slice_id = NULL, 
                v.reserved_at = NULL, 
                v.reserved_by = NULL
            WHERE s.status IN ('failed', 'error')
        """)
        vlans_result = db.execute(vlans_query)
        vlans_freed = vlans_result.rowcount
        
        # 3. Contar VMs a eliminar
        vm_count_query = text("""
            SELECT COUNT(*) as count 
            FROM vms v
            JOIN slices s ON v.slice_id = s.slice_id
            WHERE s.status IN ('failed', 'error')
        """)
        vm_count = db.execute(vm_count_query).scalar()
        
        # 4. Eliminar VMs de slices fallidos
        vms_query = text("""
            DELETE v FROM vms v
            JOIN slices s ON v.slice_id = s.slice_id
            WHERE s.status IN ('failed', 'error')
        """)
        db.execute(vms_query)
        
        # 5. Contar slices a eliminar
        slice_count_query = text("""
            SELECT COUNT(*) as count 
            FROM slices 
            WHERE status IN ('failed', 'error')
        """)
        slice_count = db.execute(slice_count_query).scalar()
        
        # 6. Eliminar slices fallidos
        slices_query = text("""
            DELETE FROM slices 
            WHERE status IN ('failed', 'error')
        """)
        db.execute(slices_query)
        
        db.commit()
        
        return MessageResponse(
            message="Limpieza de slices fallidos completada exitosamente",
            detail={
                "slices_eliminados": slice_count,
                "vms_eliminadas": vm_count,
                "vlans_liberadas": vlans_freed,
                "vnc_ports_liberados": vnc_freed
            }
        )
    except Exception as e:
        db.rollback()
        return MessageResponse(
            message=f"Error durante la limpieza: {str(e)}",
            detail={"error": True}
        )


@router.post("/all", response_model=MessageResponse)
async def cleanup_all(
    db: Session = Depends(get_db)
):
    """
    Ejecutar todas las limpiezas: recursos huérfanos + slices fallidos
    
    Este endpoint ejecuta ambas limpiezas en orden:
    1. Limpieza de slices fallidos (más específico)
    2. Limpieza de recursos huérfanos (catch-all)
    """
    # Primero limpiar slices fallidos
    result1 = await cleanup_failed_slices(db)
    
    # Luego limpiar cualquier recurso huérfano restante
    result2 = await cleanup_orphaned_resources(db)
    
    total_detail = {
        "slices_fallidos": result1.detail,
        "recursos_huerfanos": result2.detail
    }
    
    return MessageResponse(
        message="Limpieza completa ejecutada exitosamente",
        detail=total_detail
    )
