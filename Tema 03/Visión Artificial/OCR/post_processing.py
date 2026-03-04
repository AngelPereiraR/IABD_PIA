"""
post_processing.py

Módulo de post-procesamiento para detecciones de layout.
Proporciona funciones para:
- Non-Maximum Suppression (NMS) para eliminar duplicados
- Fusión de cajas cercanas
- Filtrado de ruido basado en área y aspect ratio

Uso:
    from post_processing import process_detections
    
    processed_boxes = process_detections(
        boxes, scores,
        nms_iou=0.5,
        merge_distance=10,
        min_area=100
    )
"""
from typing import List, Tuple, Optional
import numpy as np


def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Calcula Intersection over Union (IoU) entre dos cajas.
    
    Args:
        box1: (x1, y1, x2, y2) primera caja
        box2: (x1, y1, x2, y2) segunda caja
    
    Returns:
        float: IoU value entre 0 y 1
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Calcular área de intersección
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # Calcular área de unión
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def apply_nms(boxes: List[Tuple], scores: List[float], iou_threshold: float = 0.5) -> List[int]:
    """
    Non-Maximum Suppression para eliminar detecciones duplicadas.
    
    Args:
        boxes: List[(x1, y1, x2, y2, ...)] - coordenadas de las cajas
        scores: List[float] - confianza de cada detección
        iou_threshold: float - umbral IoU para considerar duplicado (default: 0.5)
    
    Returns:
        List[int]: Índices de las cajas a mantener
    """
    if len(boxes) == 0:
        return []
    
    # Convertir a arrays numpy para eficiencia
    boxes_array = np.array([b[:4] for b in boxes])  # Solo coordenadas x1,y1,x2,y2
    scores_array = np.array(scores)
    
    # Ordenar por score descendente
    order = scores_array.argsort()[::-1]
    
    keep = []
    
    while len(order) > 0:
        # Tomar el de mayor score
        idx = order[0]
        keep.append(idx)
        
        if len(order) == 1:
            break
        
        # Calcular IoU con el resto
        current_box = boxes_array[idx]
        remaining_boxes = boxes_array[order[1:]]
        
        ious = np.array([calculate_iou(current_box, other_box) for other_box in remaining_boxes])
        
        # Mantener solo los que tienen IoU < threshold
        mask = ious < iou_threshold
        order = order[1:][mask]
    
    return keep


def merge_close_boxes(boxes: List[Tuple], distance_threshold: int = 10, axis: str = 'both') -> List[Tuple]:
    """
    Fusiona cajas cercanas que probablemente sean la misma región.
    
    Args:
        boxes: List[(x1, y1, x2, y2, ...)] - cajas a fusionar
        distance_threshold: int - distancia mínima en píxeles para fusionar (default: 10)
        axis: str - 'vertical', 'horizontal', 'both' (default: 'both')
    
    Returns:
        List[Tuple]: Cajas fusionadas manteniendo formato original
    """
    if len(boxes) == 0:
        return []
    
    # Copiar lista para no modificar original
    result = list(boxes)
    merged = True
    
    while merged:
        merged = False
        i = 0
        
        while i < len(result):
            j = i + 1
            
            while j < len(result):
                box1 = result[i]
                box2 = result[j]
                
                x1_1, y1_1, x2_1, y2_1 = box1[:4]
                x1_2, y1_2, x2_2, y2_2 = box2[:4]
                
                should_merge = False
                
                # Calcular distancias
                if axis in ['horizontal', 'both']:
                    # Distancia horizontal
                    h_dist = min(abs(x2_1 - x1_2), abs(x2_2 - x1_1))
                    # Verificar si hay overlap vertical
                    v_overlap = not (y2_1 < y1_2 or y2_2 < y1_1)
                    
                    if h_dist <= distance_threshold and v_overlap:
                        should_merge = True
                
                if axis in ['vertical', 'both']:
                    # Distancia vertical
                    v_dist = min(abs(y2_1 - y1_2), abs(y2_2 - y1_1))
                    # Verificar si hay overlap horizontal
                    h_overlap = not (x2_1 < x1_2 or x2_2 < x1_1)
                    
                    if v_dist <= distance_threshold and h_overlap:
                        should_merge = True
                
                if should_merge:
                    # Fusionar cajas: tomar el bounding box que englobe ambas
                    merged_x1 = min(x1_1, x1_2)
                    merged_y1 = min(y1_1, y1_2)
                    merged_x2 = max(x2_1, x2_2)
                    merged_y2 = max(y2_1, y2_2)
                    
                    # Crear nueva caja fusionada (mantener campos extra del box1)
                    if len(box1) > 4:
                        new_box = (merged_x1, merged_y1, merged_x2, merged_y2) + box1[4:]
                    else:
                        new_box = (merged_x1, merged_y1, merged_x2, merged_y2)
                    
                    # Reemplazar box1 con fusión y eliminar box2
                    result[i] = new_box
                    result.pop(j)
                    merged = True
                    # No incrementar j, seguir comparando con nueva fusión
                else:
                    j += 1
            
            i += 1
    
    return result


def filter_noise_boxes(boxes: List[Tuple], 
                       min_area: int = 100, 
                       min_aspect_ratio: float = 0.1, 
                       max_aspect_ratio: float = 50) -> List[Tuple]:
    """
    Filtra cajas que probablemente sean ruido basándose en área y aspect ratio.
    
    Args:
        boxes: List[(x1, y1, x2, y2, ...)] - cajas a filtrar
        min_area: int - área mínima en píxeles cuadrados (default: 100)
        min_aspect_ratio: float - ratio mínimo ancho/alto (default: 0.1)
        max_aspect_ratio: float - ratio máximo ancho/alto (default: 50)
    
    Returns:
        List[Tuple]: Cajas filtradas
    """
    if len(boxes) == 0:
        return []
    
    filtered = []
    
    for box in boxes:
        x1, y1, x2, y2 = box[:4]
        
        # Calcular área
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        # Filtrar por área mínima
        if area < min_area:
            continue
        
        # Calcular aspect ratio (evitar división por cero)
        if height == 0:
            continue
        
        aspect_ratio = width / height
        
        # Filtrar por aspect ratio
        if aspect_ratio < min_aspect_ratio or aspect_ratio > max_aspect_ratio:
            continue
        
        filtered.append(box)
    
    return filtered


def process_detections(boxes: List[Tuple], 
                       scores: List[float],
                       nms_iou: float = 0.5,
                       merge_distance: int = 10,
                       min_area: int = 100,
                       min_aspect_ratio: float = 0.1,
                       max_aspect_ratio: float = 50,
                       enable_nms: bool = True,
                       enable_merge: bool = True,
                       enable_filter: bool = True,
                       debug: bool = False) -> List[Tuple]:
    """
    Pipeline completo de post-procesamiento para detecciones de layout.
    
    Args:
        boxes: List[(x1, y1, x2, y2, ...)] - detecciones raw del modelo
        scores: List[float] - confidences paralelas a boxes
        nms_iou: float - threshold para NMS (default: 0.5)
        merge_distance: int - distancia para merging (default: 10)
        min_area: int - área mínima para filtrado (default: 100)
        min_aspect_ratio: float - aspect ratio mínimo (default: 0.1)
        max_aspect_ratio: float - aspect ratio máximo (default: 50)
        enable_nms: bool - activar/desactivar NMS (default: True)
        enable_merge: bool - activar/desactivar merging (default: True)
        enable_filter: bool - activar/desactivar filtrado (default: True)
        debug: bool - imprimir información de debug (default: False)
    
    Returns:
        List[Tuple]: Cajas procesadas listas para OCR
    """
    if len(boxes) == 0:
        return []
    
    result = list(boxes)
    result_scores = list(scores)
    
    if debug:
        print(f"\n=== POST-PROCESSING PIPELINE ===")
        print(f"Input: {len(result)} boxes")
    
    # Paso 1: Non-Maximum Suppression
    if enable_nms and len(result) > 0:
        indices = apply_nms(result, result_scores, nms_iou)
        result = [result[i] for i in indices]
        result_scores = [result_scores[i] for i in indices]
        
        if debug:
            print(f"After NMS (iou={nms_iou}): {len(result)} boxes")
    
    # Paso 2: Fusión de cajas cercanas
    if enable_merge and len(result) > 0:
        before_merge = len(result)
        result = merge_close_boxes(result, merge_distance)
        
        if debug:
            print(f"After merging (dist={merge_distance}): {len(result)} boxes ({before_merge - len(result)} merged)")
    
    # Paso 3: Filtrado de ruido
    if enable_filter and len(result) > 0:
        before_filter = len(result)
        result = filter_noise_boxes(result, min_area, min_aspect_ratio, max_aspect_ratio)
        
        if debug:
            print(f"After filtering (min_area={min_area}): {len(result)} boxes ({before_filter - len(result)} removed)")
    
    if debug:
        print(f"Final output: {len(result)} boxes")
        print("=" * 35 + "\n")
    
    return result
