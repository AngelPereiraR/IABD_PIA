"""validate_ocr.py

FASE 4 — Validacion OCR completo con las mejores configuraciones del grid search.

Para cada configuracion seleccionada y cada motor OCR:
  1. Ejecuta deteccion de regions (detect_columns.detect_columns)
    2. Ejecuta OCR sobre cada region detectada (EasyOCR/Tesseract/Paddle/DeepSeek)
  3. Recopila metricas: caracteres, palabras, columnas, duplicados, tiempo
  4. Genera informe comparativo

Modos de uso:
    # Automatico (default usa 4 OCR: easyocr,tesseract,paddle,deepseek)
    # Requiere pasar ruta de Tesseract y modelo DeepSeek:
    py -3.11 validate_ocr.py --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

    # Automatico solo con OCR que no requieren argumentos extra (sin tesseract/deepseek)
    py -3.11 validate_ocr.py --ocr-engines easyocr,paddle

    # Automatico usando Tesseract + DeepSeek (requiere rutas explicitas en Windows)
    py -3.11 validate_ocr.py --ocr-engines tesseract,deepseek --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Top-N configuraciones globales:
  py -3.11 validate_ocr.py --top 5

    # Top-N con DeepSeek:
    py -3.11 validate_ocr.py --top 5 --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Configuraciones manuales (sin necesitar Phase 3):
  py -3.11 validate_ocr.py --configs '[
      {"method":"paddleocr","nms_iou":0.5,"merge_distance":10},
      {"method":"docling","nms_iou":0.5,"merge_distance":10},
      {"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":15},
      {"method":"yolo11","conf":0.1,"nms_iou":0.5,"merge_distance":10},
      {"method":"opencv","merge_distance":10}
  ]'

    # Configuraciones manuales con Tesseract:
    py -3.11 validate_ocr.py --configs '[{"method":"docling","nms_iou":0.5,"merge_distance":10}]' --ocr-engines tesseract --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

  # Solo un metodo concreto:
  py -3.11 validate_ocr.py --method paddleocr

    # Solo un metodo concreto con DeepSeek:
    py -3.11 validate_ocr.py --method docling --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Reanudar ejecucion interrumpida:
  py -3.11 validate_ocr.py --resume

    # Reanudar con Tesseract + DeepSeek:
    py -3.11 validate_ocr.py --resume --ocr-engines tesseract,deepseek --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

    # DeepSeek (prompt agresivo para texto borroso / baja calidad)
    py -3.11 validate_ocr.py --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR" --deepseek-prompt "<image>\nPerform robust OCR on this noisy or blurred document region. Recover as much readable text as possible while preserving reading order and line breaks. Output plain text only."

    # DeepSeek (prompt conservador anti-alucinacion)
    py -3.11 validate_ocr.py --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR" --deepseek-prompt "<image>\nExtract only clearly readable text from this document region. Do not guess, infer, or complete missing words. If text is unreadable, omit it. Preserve reading order and line breaks. Output plain text only."

  # Ver solo resultados sin reejecutar:
  py -3.11 validate_ocr.py --report-only
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import json
import sys
import time
import tempfile
import types
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Evita chequeos de conectividad de Paddle al iniciar modelos.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# ---------------------------------------------------------------------------
# Dependencias opcionales con feedback claro
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[WARN] pandas no instalado; el modo automatico no estara disponible.")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    print("[WARN] easyocr no instalado: pip install easyocr")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("[WARN] pytesseract no instalado: pip install pytesseract")

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE_OCR = True
except ImportError:
    HAS_PADDLE_OCR = False
    print("[WARN] paddleocr no instalado: pip install paddleocr")

try:
    import torch
    import transformers as hf_transformers
    from transformers import AutoModel, AutoTokenizer
    HAS_DEEPSEEK_DEPS = True
except ImportError:
    HAS_DEEPSEEK_DEPS = False
    print("[WARN] transformers/torch no instalados; DeepSeek no disponible")

# Añadir directorio actual al path para importar detect_columns como modulo
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

try:
    import detect_columns as dc
    HAS_DC = True
except ImportError as _e:
    HAS_DC = False
    print(f"[ERROR] No se pudo importar detect_columns: {_e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Rutas y constantes
# ---------------------------------------------------------------------------
IMGS_DIR = _HERE / "imgs"
RANKING_CSV = _HERE / "experiment_ranking.csv"
RESULTS_DIR = _HERE / "validation_results"
REPORT_JSON = _HERE / "ocr_validation_report.json"
REPORT_TXT = _HERE / "ocr_validation_report.txt"
REPORT_CSV = _HERE / "ocr_validation_report.csv"
DEEPSEEK_DEFAULT_MODEL_DIR = _HERE / "models" / "DeepSeek-OCR"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Pesos de la formula de scoring OCR (ajustables)
CHARS_WEIGHT = 1.0       # por caracter extraido
WORDS_WEIGHT = 5.0       # bonus por palabra detectada
DUP_PENALTY = 50.0       # penalizacion por duplicado en deteccion
MISSED_PENALTY = 20.0    # penalizacion por imagen sin regiones detectadas

SUPPORTED_ENGINES = ["easyocr", "tesseract", "paddle", "deepseek"]


class DeepSeekFatalError(RuntimeError):
    """Error fatal de DeepSeek que invalida continuar con ese motor."""


def _version_tuple(v: str) -> Tuple[int, int, int]:
    """Convierte 'x.y.z' a tupla comparable tolerando sufijos."""
    parts = []
    for p in v.split(".")[:3]:
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def _is_transformers_compatible_for_deepseek() -> bool:
    """DeepSeek-OCR falla con transformers demasiado nuevos (ej. 4.57.x)."""
    if not HAS_DEEPSEEK_DEPS:
        return False
    current = _version_tuple(hf_transformers.__version__)
    return _version_tuple("4.51.1") <= current < _version_tuple("4.56.0")


def _ensure_llama_flashattention2_symbol() -> None:
    """Crea alias de compatibilidad si la clase ya no existe en transformers nuevos.

    Algunos repos con trust_remote_code importan `LlamaFlashAttention2` directamente.
    En versiones recientes de transformers esa clase puede no existir. En vez de
    alias directo (incompatible por cambios de firma), se inyecta un shim que
    adapta la API antigua a `LlamaAttention` moderna.
    """
    if not HAS_DEEPSEEK_DEPS:
        return
    try:
        from transformers.models.llama import modeling_llama as llama_mod

        if (not hasattr(llama_mod, "LlamaFlashAttention2")) and hasattr(llama_mod, "LlamaAttention"):
            class _LlamaFlashAttention2Compat(llama_mod.LlamaAttention):
                """Shim de compatibilidad para código que espera LlamaFlashAttention2.

                DeepSeek (trust_remote_code) invoca la firma legacy:
                  forward(hidden_states, attention_mask, position_ids, past_key_value, ...)
                mientras que `LlamaAttention` moderna requiere `position_embeddings`.
                """

                def forward(
                    self,
                    hidden_states: torch.Tensor,
                    attention_mask: Optional[torch.Tensor] = None,
                    position_ids: Optional[torch.LongTensor] = None,
                    past_key_value: Optional[Any] = None,
                    output_attentions: bool = False,
                    use_cache: bool = False,
                    **kwargs: Any,
                ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Any]]:
                    cache_position = kwargs.pop("cache_position", None)
                    position_embeddings = kwargs.pop("position_embeddings", None)

                    if position_embeddings is None:
                        if position_ids is None:
                            seq_len = hidden_states.shape[1]
                            position_ids = torch.arange(
                                seq_len, device=hidden_states.device, dtype=torch.long
                            ).unsqueeze(0)
                        if hasattr(self, "rotary_emb"):
                            try:
                                position_embeddings = self.rotary_emb(hidden_states, position_ids)
                            except TypeError:
                                position_embeddings = self.rotary_emb(
                                    hidden_states, position_ids=position_ids
                                )

                    attn_output, attn_weights = super().forward(
                        hidden_states=hidden_states,
                        position_embeddings=position_embeddings,
                        attention_mask=attention_mask,
                        past_key_value=past_key_value,
                        cache_position=cache_position,
                        **kwargs,
                    )

                    if not output_attentions:
                        attn_weights = None

                    present_key_value = past_key_value if use_cache else None
                    return attn_output, attn_weights, present_key_value

            llama_mod.LlamaFlashAttention2 = _LlamaFlashAttention2Compat
    except Exception:
        # Si falla este parche, se gestionará en el bloque de carga del modelo.
        pass


def _ensure_llama_attention_forward_compat() -> None:
    """Hace compatible LlamaAttention.forward con llamadas legacy.

    En transformers recientes, `LlamaAttention.forward` exige `position_embeddings`.
    Algunos modelos con trust_remote_code (incluyendo DeepSeek OCR) siguen
    llamando con la firma antigua basada en `position_ids`.
    """
    if not HAS_DEEPSEEK_DEPS:
        return
    try:
        from transformers.models.llama import modeling_llama as llama_mod
        if not hasattr(llama_mod, "LlamaAttention"):
            return

        original_forward = llama_mod.LlamaAttention.forward
        if getattr(original_forward, "_ocr_compat_patched", False):
            return

        def patched_forward(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Si ya se pasa position_embeddings explícito, no tocar.
            if kwargs.get("position_embeddings", None) is not None:
                return original_forward(self, *args, **kwargs)

            # Resolver hidden_states tanto por kwargs como por args posicionales.
            hidden_states = kwargs.get("hidden_states", None)
            if hidden_states is None and args:
                hidden_states = args[0]

            # Resolver position_ids (si no vienen, crear secuencia 0..L-1).
            position_ids = kwargs.get("position_ids", None)
            if position_ids is None and isinstance(hidden_states, torch.Tensor):
                seq_len = hidden_states.shape[1]
                position_ids = torch.arange(
                    seq_len, dtype=torch.long, device=hidden_states.device
                ).unsqueeze(0)

            # Construir position_embeddings con rotary emb cuando sea posible.
            if isinstance(hidden_states, torch.Tensor) and position_ids is not None and hasattr(self, "rotary_emb"):
                try:
                    kwargs["position_embeddings"] = self.rotary_emb(hidden_states, position_ids)
                except TypeError:
                    kwargs["position_embeddings"] = self.rotary_emb(
                        hidden_states, position_ids=position_ids
                    )

            # El API nuevo no acepta position_ids explícito.
            kwargs.pop("position_ids", None)
            return original_forward(self, *args, **kwargs)

        patched_forward._ocr_compat_patched = True  # type: ignore[attr-defined]
        llama_mod.LlamaAttention.forward = patched_forward
    except Exception:
        # No bloquear ejecución si el parche no aplica en este entorno.
        pass


def _ensure_dynamic_cache_seen_tokens() -> None:
    """Parche de compatibilidad para modelos que esperan DynamicCache.seen_tokens.

    Algunas combinaciones de trust_remote_code + transformers recientes usan
    internamente `DynamicCache` sin exponer `seen_tokens`, lo que provoca:
      'DynamicCache' object has no attribute 'seen_tokens'
    Este parche añade una propiedad compatible en caliente.
    """
    if not HAS_DEEPSEEK_DEPS:
        return
    try:
        from transformers.cache_utils import DynamicCache  # type: ignore

        # seen_tokens (compat con código que usa contadores de decodificación)
        if not hasattr(DynamicCache, "seen_tokens"):
            def _get_seen_tokens(self: Any) -> int:
                # Compatibilidad con variantes internas de transformers
                if hasattr(self, "_seen_tokens"):
                    return int(getattr(self, "_seen_tokens") or 0)
                if hasattr(self, "get_seq_length"):
                    try:
                        return int(self.get_seq_length())
                    except Exception:
                        return 0
                return 0

            def _set_seen_tokens(self: Any, value: Any) -> None:
                setattr(self, "_seen_tokens", int(value) if value is not None else 0)

            DynamicCache.seen_tokens = property(_get_seen_tokens, _set_seen_tokens)  # type: ignore[attr-defined]

        # get_max_length (compat con código legacy de cache API)
        if not hasattr(DynamicCache, "get_max_length"):
            def _get_max_length(self: Any) -> Optional[int]:
                for attr in ("max_cache_len", "max_length", "_max_length"):
                    val = getattr(self, attr, None)
                    if isinstance(val, int):
                        return val
                return None

            DynamicCache.get_max_length = _get_max_length  # type: ignore[attr-defined]

        # get_usable_length (algunos modelos llaman esta API legacy)
        if not hasattr(DynamicCache, "get_usable_length"):
            def _get_usable_length(self: Any, *args: Any, **kwargs: Any) -> int:
                try:
                    return int(self.get_seq_length())  # type: ignore[misc]
                except Exception:
                    return 0

            DynamicCache.get_usable_length = _get_usable_length  # type: ignore[attr-defined]
    except Exception:
        # Si no se puede parchear, se continuará y se reportará al inicializar/inferir.
        pass


def _patch_generation_warnings(model: Any, tokenizer: Any) -> None:
    """Reduce warnings comunes de generate() en modelos trust_remote_code.

    - Asegura pad_token_id/eos_token_id en config y kwargs.
    - Inyecta attention_mask cuando falta y hay input_ids.
    - Elimina temperature si do_sample=False para evitar warning de flags.
    """
    if not HAS_DEEPSEEK_DEPS:
        return

    # Configurar tokens por defecto para generación
    try:
        if getattr(tokenizer, "pad_token_id", None) is None and getattr(tokenizer, "eos_token_id", None) is not None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
    except Exception:
        pass


def _ensure_masked_scatter_compat() -> None:
    """Parche defensivo para mismatch +/-1 fila en masked_scatter_ de DeepSeek.

    Se limita al patrón observado en DeepSeek-OCR donde `images_in_this_batch`
    difiere en una fila respecto al número de placeholders visuales.
    """
    if not HAS_DEEPSEEK_DEPS:
        return
    try:
        original_masked_scatter = torch.Tensor.masked_scatter_
        if getattr(original_masked_scatter, "_ocr_compat_patched", False):
            return

        max_delta_rows = 64

        def patched_masked_scatter(self: torch.Tensor, mask: torch.Tensor, source: torch.Tensor) -> torch.Tensor:
            # Normalizar desajuste leve de longitud en máscara visual (off-by-one).
            if (
                isinstance(mask, torch.Tensor)
                and mask.dim() == 2
                and mask.shape[1] == 1
                and self.dim() == 2
            ):
                m_rows = int(mask.shape[0])
                t_rows = int(self.shape[0])
                d_rows = t_rows - m_rows
                if 0 < d_rows <= max_delta_rows:
                    pad = torch.zeros((d_rows, 1), dtype=mask.dtype, device=mask.device)
                    mask = torch.cat([mask, pad], dim=0)
                elif 0 > d_rows >= -max_delta_rows:
                    mask = mask[:t_rows, :]

            try:
                return original_masked_scatter(self, mask, source)
            except RuntimeError as exc:
                msg = str(exc)
                if "expanded size of the tensor" not in msg:
                    raise

                if not (
                    isinstance(source, torch.Tensor)
                    and self.dim() == 2
                    and source.dim() == 2
                    and self.shape[1] == source.shape[1]
                    and mask.dim() == 2
                    and mask.shape[1] == 1
                ):
                    raise

                # Reintento: corregir máscara si aún no coincide exactamente.
                if mask.shape[0] != self.shape[0]:
                    m_rows = int(mask.shape[0])
                    t_rows = int(self.shape[0])
                    d_rows = t_rows - m_rows
                    if 0 < d_rows <= max_delta_rows:
                        pad = torch.zeros((d_rows, 1), dtype=mask.dtype, device=mask.device)
                        mask = torch.cat([mask, pad], dim=0)
                    elif 0 > d_rows >= -max_delta_rows:
                        mask = mask[:t_rows, :]
                    else:
                        raise

                true_rows = int(mask.squeeze(-1).sum().item())
                src_rows = int(source.shape[0])
                delta = true_rows - src_rows
                if abs(delta) > max_delta_rows:
                    raise

                if delta > 0:
                    # Si falta 1 fila, repetir la última para mantener continuidad.
                    pad = source[-1:, :].expand(delta, -1)
                    source = torch.cat([source, pad], dim=0)
                elif delta < 0:
                    source = source[:true_rows, :]

                return original_masked_scatter(self, mask, source)

        patched_masked_scatter._ocr_compat_patched = True  # type: ignore[attr-defined]
        torch.Tensor.masked_scatter_ = patched_masked_scatter  # type: ignore[assignment]
    except Exception:
        pass


def _patch_deepseek_attention_instances(model: Any) -> int:
    """Parchea instancias de LlamaAttention en el modelo DeepSeek cargado.

    Objetivo:
      - Aceptar llamadas legacy con `position_ids` (sin `position_embeddings`).
      - Devolver 3 valores (output, attn_weights, present_kv) como espera
        el decoder de DeepSeek trust_remote_code.
    """
    if not HAS_DEEPSEEK_DEPS:
        return 0

    patched = 0
    for module in model.modules():
        if module.__class__.__name__ != "LlamaAttention":
            continue

        original_forward = module.forward
        if getattr(original_forward, "_ocr_deepseek_instance_patched", False):
            continue

        def _patched_forward(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Compatibilidad con llamada legacy de DeepSeek.
            hidden_states = kwargs.get("hidden_states", None)
            if hidden_states is None and args:
                hidden_states = args[0]

            attention_mask = kwargs.get("attention_mask", None)
            # Forzar modo sin cache para evitar desajustes de longitud entre
            # API legacy y API nueva de atención en transformers recientes.
            past_key_value = None
            use_cache = False
            output_attentions = bool(kwargs.get("output_attentions", False))
            cache_position = None

            position_embeddings = kwargs.get("position_embeddings", None)
            position_ids = kwargs.get("position_ids", None)
            if position_embeddings is None and isinstance(hidden_states, torch.Tensor):
                if position_ids is None:
                    seq_len = hidden_states.shape[1]
                    position_ids = torch.arange(
                        seq_len, dtype=torch.long, device=hidden_states.device
                    ).unsqueeze(0)
                if hasattr(self, "rotary_emb"):
                    try:
                        position_embeddings = self.rotary_emb(hidden_states, position_ids)
                    except TypeError:
                        position_embeddings = self.rotary_emb(
                            hidden_states, position_ids=position_ids
                        )

                # Fallback para variantes de LlamaAttention sin `self.rotary_emb`.
                if position_embeddings is None:
                    try:
                        from transformers.models.llama import modeling_llama as llama_mod

                        rotary = getattr(self, "_ocr_rotary_emb", None)
                        if rotary is None:
                            cfg = getattr(self, "config", None)
                            if cfg is not None:
                                rotary = llama_mod.LlamaRotaryEmbedding(cfg)
                                rotary = rotary.to(device=hidden_states.device)
                                setattr(self, "_ocr_rotary_emb", rotary)

                        if rotary is not None:
                            try:
                                position_embeddings = rotary(hidden_states, position_ids)
                            except TypeError:
                                position_embeddings = rotary(
                                    hidden_states, position_ids=position_ids
                                )
                    except Exception:
                        position_embeddings = None

            if position_embeddings is None:
                raise RuntimeError(
                    "No se pudo construir position_embeddings para LlamaAttention compat"
                )

            out, attn = original_forward(
                hidden_states=hidden_states,
                position_embeddings=position_embeddings,
                attention_mask=attention_mask,
                past_key_value=past_key_value,
                cache_position=cache_position,
            )

            if not output_attentions:
                attn = None
            present_kv = None
            return out, attn, present_kv

        _patched_forward._ocr_deepseek_instance_patched = True  # type: ignore[attr-defined]
        module.forward = types.MethodType(_patched_forward, module)
        patched += 1

    return patched

    pad_id = getattr(tokenizer, "pad_token_id", None)
    eos_id = getattr(tokenizer, "eos_token_id", None)

    try:
        if hasattr(model, "generation_config") and model.generation_config is not None:
            if getattr(model.generation_config, "pad_token_id", None) is None and pad_id is not None:
                model.generation_config.pad_token_id = pad_id
            if getattr(model.generation_config, "eos_token_id", None) is None and eos_id is not None:
                model.generation_config.eos_token_id = eos_id
    except Exception:
        pass

    # Envolver generate para normalizar kwargs y evitar warnings repetitivos.
    try:
        original_generate = model.generate
        if getattr(original_generate, "_ocr_warning_patched", False):
            return

        def patched_generate(*args: Any, **kwargs: Any) -> Any:
            do_sample = bool(kwargs.get("do_sample", False))
            if ("temperature" in kwargs) and (not do_sample):
                kwargs.pop("temperature", None)

            if kwargs.get("pad_token_id", None) is None:
                if pad_id is not None:
                    kwargs["pad_token_id"] = pad_id
                elif eos_id is not None:
                    kwargs["pad_token_id"] = eos_id

            if kwargs.get("attention_mask", None) is None:
                input_ids = kwargs.get("input_ids", None)
                if input_ids is None and args:
                    first = args[0]
                    if isinstance(first, torch.Tensor):
                        input_ids = first
                if isinstance(input_ids, torch.Tensor):
                    kwargs["attention_mask"] = torch.ones_like(input_ids)

            return original_generate(*args, **kwargs)

        patched_generate._ocr_warning_patched = True  # type: ignore[attr-defined]
        model.generate = patched_generate
    except Exception:
        pass


def _load_deepseek_model_with_fallback(model_dir: Path) -> Tuple[Any, Any, str]:
    """Carga DeepSeek intentando flash-attn y, si falla, vuelve a eager.

    Returns:
        tokenizer, model, attn_impl_utilizada
    """
    _ensure_llama_flashattention2_symbol()
    _ensure_llama_attention_forward_compat()
    _ensure_dynamic_cache_seen_tokens()
    _ensure_masked_scatter_compat()

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)

    has_flash_attn = importlib.util.find_spec("flash_attn") is not None

    try:
        if has_flash_attn:
            model = AutoModel.from_pretrained(
                str(model_dir),
                trust_remote_code=True,
                use_safetensors=True,
                _attn_implementation="flash_attention_2",
            )
            attn_impl = "flash_attention_2"
        else:
            # Igual que pruebas-deepseek.py: fallback por defecto sin forzar eager
            model = AutoModel.from_pretrained(
                str(model_dir),
                trust_remote_code=True,
                use_safetensors=True,
            )
            attn_impl = "default"
        model = model.eval().cuda().to(torch.bfloat16)
        patched_count = _patch_deepseek_attention_instances(model)
        if patched_count > 0:
            print(f"[i] DeepSeek compat: parcheadas {patched_count} capas LlamaAttention")
        _patch_generation_warnings(model, tokenizer)
        return tokenizer, model, attn_impl
    except Exception:
        # Segundo intento forzando eager para no depender de flash-attn.
        model = AutoModel.from_pretrained(
            str(model_dir),
            trust_remote_code=True,
            use_safetensors=True,
            _attn_implementation="eager",
        )
        model = model.eval().cuda().to(torch.bfloat16)
        patched_count = _patch_deepseek_attention_instances(model)
        if patched_count > 0:
            print(f"[i] DeepSeek compat: parcheadas {patched_count} capas LlamaAttention")
        _patch_generation_warnings(model, tokenizer)
        return tokenizer, model, "eager"


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Numero de palabras con al menos 2 caracteres alfabeticos."""
    return sum(1 for w in text.split() if sum(c.isalpha() for c in w) >= 2)


def clean_ocr_text(text: str) -> str:
    """Elimina lineas vacias y espacios extra."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OCR sobre regiones
# ---------------------------------------------------------------------------

def run_easyocr_on_regions(
    img_bgr: np.ndarray,
    boxes: List,          # List[ColumnBox] de detect_columns
    reader: "easyocr.Reader",
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con EasyOCR.

    Returns dict con:
        total_chars, total_words, per_region (list de dicts con texto/chars/words)
    """
    per_region = []
    total_chars = 0
    total_words = 0

    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
        # Clip a los limites de la imagen
        h, w = img_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
            continue

        region = img_bgr[y1:y2, x1:x2]

        try:
            results = reader.readtext(region, detail=0, paragraph=True)
            text = clean_ocr_text(" ".join(results))
        except Exception as exc:
            text = ""
            print(f"    [WARN] EasyOCR fallo en region {i}: {exc}")

        chars = len(text.replace(" ", "").replace("\n", ""))
        words = count_words(text)
        total_chars += chars
        total_words += words
        per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def run_tesseract_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con Tesseract."""
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
        h, w = img_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
            continue

        region = img_bgr[y1:y2, x1:x2]
        try:
            text = pytesseract.image_to_string(region, lang="spa+eng")
            text = clean_ocr_text(text)
        except Exception as exc:
            text = ""
            print(f"    [WARN] Tesseract fallo en region {i}: {exc}")

        chars = len(text.replace(" ", "").replace("\n", ""))
        words = count_words(text)
        total_chars += chars
        total_words += words
        per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def run_paddle_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
    paddle_reader: "PaddleOCR",
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con PaddleOCR."""
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    with tempfile.TemporaryDirectory(prefix="ocr_paddle_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        for i, box in enumerate(boxes, start=1):
            x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
            h, w = img_bgr.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
                continue

            region = img_bgr[y1:y2, x1:x2]
            region_file = tmp_path / f"region_{i}.png"
            cv2.imwrite(str(region_file), region)

            text = ""
            try:
                pred = paddle_reader.predict(str(region_file))
                if pred and isinstance(pred, list) and len(pred) > 0:
                    rec_texts = pred[0].get("rec_texts", [])
                    text = clean_ocr_text("\n".join(rec_texts))
            except Exception as exc:
                print(f"    [WARN] PaddleOCR fallo en region {i}: {exc}")

            chars = len(text.replace(" ", "").replace("\n", ""))
            words = count_words(text)
            total_chars += chars
            total_words += words
            per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def _deepseek_result_to_text(result: Any) -> str:
    """Intenta extraer texto OCR de distintos formatos devueltos por DeepSeek."""
    if result is None:
        return ""
    if isinstance(result, str):
        return clean_ocr_text(result)
    if isinstance(result, dict):
        for key in ("text", "result", "output", "markdown"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return clean_ocr_text(val)
        return clean_ocr_text(json.dumps(result, ensure_ascii=False))
    if isinstance(result, list):
        parts = [_deepseek_result_to_text(x) for x in result]
        return clean_ocr_text("\n".join([p for p in parts if p]))
    return clean_ocr_text(str(result))


def _prepare_region_for_deepseek(region_bgr: np.ndarray, min_side: int = 640) -> np.ndarray:
    """Acolcha el recorte a cuadrado para estabilizar el preprocesado visual.

    DeepSeek-OCR puede desalinear tokens visuales en recortes extremos
    (muy estrechos/altos). Este padding reduce casos de mismatch 299/300.
    """
    h, w = region_bgr.shape[:2]
    side = max(h, w, int(min_side))
    # Alinear a múltiplos de 32 para evitar artefactos de discretización.
    side = int(np.ceil(side / 32.0) * 32)

    canvas = np.full((side, side, 3), 255, dtype=region_bgr.dtype)
    y = (side - h) // 2
    x = (side - w) // 2
    canvas[y:y + h, x:x + w] = region_bgr
    return canvas


def run_deepseek_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
    deepseek_model: Any,
    deepseek_tokenizer: Any,
    prompt: str,
    base_size: int = 1024,
    image_size: int = 1024,
    crop_mode: bool = False,
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con DeepSeek OCR local."""
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    with tempfile.TemporaryDirectory(prefix="ocr_deepseek_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        canonical_prompt = "<image>\n<|grounding|>Convert the document to markdown."

        for i, box in enumerate(boxes, start=1):
            x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
            h, w = img_bgr.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
                continue

            region = img_bgr[y1:y2, x1:x2]
            region = _prepare_region_for_deepseek(region, min_side=max(image_size, 640))
            region_file = tmp_path / f"region_{i}.png"
            cv2.imwrite(str(region_file), region)

            text = ""
            try:
                result = deepseek_model.infer(
                    deepseek_tokenizer,
                    prompt=prompt,
                    image_file=str(region_file),
                    output_path=str(tmp_path / f"out_{i}"),
                    base_size=base_size,
                    image_size=image_size,
                    crop_mode=crop_mode,
                    save_results=False,
                    test_compress=False,
                )
                text = _deepseek_result_to_text(result)
            except Exception as exc:
                msg = str(exc)
                # Workaround para bug interno: `param_img` queda sin inicializar
                # con ciertas resoluciones no soportadas por el encoder.
                if "param_img" in msg and (base_size, image_size, crop_mode) != (1024, 1024, False):
                    try:
                        result = deepseek_model.infer(
                            deepseek_tokenizer,
                            prompt=prompt,
                            image_file=str(region_file),
                            output_path=str(tmp_path / f"out_{i}_fallback"),
                            base_size=1024,
                            image_size=1024,
                            crop_mode=False,
                            save_results=False,
                            test_compress=False,
                        )
                        text = _deepseek_result_to_text(result)
                        print(
                            f"    [INFO] DeepSeek region {i}: fallback 1024x1024 aplicado por error param_img"
                        )
                    except Exception as retry_exc:
                        print(f"    [WARN] DeepSeek fallo en region {i}: {retry_exc}")
                else:
                    # Fallback para desajustes de longitud visual/token (299/300, 598/299, etc.)
                    # observados en ciertas combinaciones de prompt/API de transformers.
                    shape_mismatch = (
                        "expanded size of the tensor" in msg
                        or "size of tensor" in msg
                        or "must match the existing size" in msg
                    )
                    if shape_mismatch:
                        try:
                            result = deepseek_model.infer(
                                deepseek_tokenizer,
                                prompt=canonical_prompt,
                                image_file=str(region_file),
                                output_path=str(tmp_path / f"out_{i}_shape_retry"),
                                base_size=1024,
                                image_size=640,
                                crop_mode=True,
                                save_results=False,
                                test_compress=False,
                                eval_mode=True,
                            )
                            text = _deepseek_result_to_text(result)
                            print(
                                f"    [INFO] DeepSeek region {i}: retry shape-mismatch con prompt/crop oficial"
                            )
                        except Exception as retry_exc:
                            retry_msg = str(retry_exc)
                            print(f"    [WARN] DeepSeek fallo en region {i}: {retry_exc}")
                            if (
                                "expanded size of the tensor" in retry_msg
                                or "must match the existing size" in retry_msg
                                or "size of tensor" in retry_msg
                            ):
                                raise DeepSeekFatalError(retry_msg)
                    else:
                        print(f"    [WARN] DeepSeek fallo en region {i}: {exc}")

            chars = len(text.replace(" ", "").replace("\n", ""))
            words = count_words(text)
            total_chars += chars
            total_words += words
            per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


# ---------------------------------------------------------------------------
# Deteccion de regiones (wrapper sobre detect_columns)
# ---------------------------------------------------------------------------

def run_detection(
    img_bgr: np.ndarray,
    image_path: str,
    cfg: Dict[str, Any],
) -> Tuple[List, int, float]:
    """Ejecuta deteccion de regiones para una configuracion.

    Returns:
        boxes        — lista de ColumnBox
        duplicates   — numero de duplicados detectados por NMS
        elapsed_ms   — tiempo transcurrido en milisegundos
    """
    method = cfg["method"]
    conf = cfg.get("conf", 0.25)
    nms_iou = cfg.get("nms_iou", 0.5)
    merge_distance = cfg.get("merge_distance", 10)
    min_area = cfg.get("min_area", 100)
    yolo11_conf = cfg.get("yolo11_conf", conf)  # mismo conf para yolo11
    yolo11_size = cfg.get("yolo11_size", "nano")

    t0 = time.perf_counter()
    try:
        _, boxes = dc.detect_columns(
            img_bgr,
            method=method,
            debug=False,
            doclayout_conf=conf,
            doclayout_all_classes=False,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=True,
            enable_merge=True,
            enable_filter=True,
            model_path=None,
            image_path=image_path,
            yolo11_conf=yolo11_conf,
            yolo11_size=yolo11_size,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Estimar duplicados: cuantas cajas eliminaria un NMS mas estricto
        duplicates = _estimate_duplicates(boxes)
        return boxes, duplicates, elapsed_ms

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"    [ERROR] Deteccion fallo: {exc}")
        return [], 0, elapsed_ms


def _estimate_duplicates(boxes: List) -> int:
    """Cuenta pares de cajas con IoU > 0.3 (posibles duplicados residuales)."""
    from post_processing import calculate_iou  # disponible en el proyecto
    count = 0
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            b1 = (boxes[i].x1, boxes[i].y1, boxes[i].x2, boxes[i].y2)
            b2 = (boxes[j].x1, boxes[j].y1, boxes[j].x2, boxes[j].y2)
            if calculate_iou(b1, b2) > 0.3:
                count += 1
    return count


# ---------------------------------------------------------------------------
# Carga de configuraciones
# ---------------------------------------------------------------------------

def load_top_configs_from_ranking(
    csv_path: Path,
    top_n: int = 3,
    method_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lee experiment_ranking.csv y devuelve las top_n configuraciones.

    Si method_filter se especifica, devuelve las top_n de ese metodo.
    Si no, devuelve las top_n globales (una por metodo diferente si es posible).
    """
    if not HAS_PANDAS:
        sys.exit("[ERROR] pandas requerido para leer el ranking. Instala con: pip install pandas")
    if not csv_path.exists():
        sys.exit(
            f"[ERROR] No se encontro {csv_path}\n"
            "        Ejecuta primero: py -3.11 analyze_experiments.py"
        )

    df = pd.read_csv(csv_path)

    if method_filter:
        df = df[df["method"] == method_filter]
        if df.empty:
            sys.exit(f"[ERROR] No hay resultados para el metodo '{method_filter}' en el ranking.")

    # Ordenar por score descendente
    df = df.sort_values("score", ascending=False).head(top_n)

    configs = []
    for _, row in df.iterrows():
        cfg: Dict[str, Any] = {
            "method": row["method"],
            "merge_distance": int(row["merge_distance"]),
        }
        # nms_iou es NaN para opencv (sin nms configurable)
        nms_val = row.get("nms_iou")
        if pd.notna(nms_val):
            cfg["nms_iou"] = float(nms_val)
        conf_val = row.get("conf")
        if pd.notna(conf_val):
            cfg["conf"] = float(conf_val)
        configs.append(cfg)

    return configs


def build_config_label(cfg: Dict[str, Any]) -> str:
    """Genera un identificador legible para una configuracion."""
    parts = [cfg["method"]]
    if "conf" in cfg:
        parts.append(f"conf{cfg['conf']:.2f}")
    if "nms_iou" in cfg:          # opencv no tiene nms_iou
        parts.append(f"nms{cfg['nms_iou']:.2f}")
    parts.append(f"mg{cfg['merge_distance']}")
    return "_".join(parts)


# ---------------------------------------------------------------------------
# Ejecucion de una configuracion sobre todas las imagenes
# ---------------------------------------------------------------------------

def run_config(
    cfg: Dict[str, Any],
    image_paths: List[Path],
    ocr_engines: List[str],
    engine_ctx: Dict[str, Any],
    output_dir: Path,
    resume: bool = False,
) -> List[Dict[str, Any]]:
    """Ejecuta deteccion una vez por imagen y OCR para uno o varios motores.

    Optimizacion clave:
      - La deteccion de layout se calcula solo una vez por imagen/config.
      - El resultado (boxes, dups, det_ms) se reutiliza para todos los OCR pendientes.
    """
    label = build_config_label(cfg)
    config_dir = output_dir / label
    config_dir.mkdir(parents=True, exist_ok=True)

    # Estado por motor OCR (fichero + resultados parciales para resume)
    per_engine: Dict[str, Dict[str, Any]] = {}
    for ocr_engine in ocr_engines:
        results_file = config_dir / f"results_{ocr_engine}.json"
        existing: Dict[str, Any] = {}
        if resume and results_file.exists():
            with open(results_file, encoding="utf-8") as f:
                existing = json.load(f)
            already_done = set(existing.get("per_image", {}).keys())
            print(f"    [resume] {ocr_engine}: {len(already_done)} imagenes ya procesadas, saltando.")
        else:
            already_done = set()

        per_engine[ocr_engine] = {
            "results_file": results_file,
            "per_image": existing.get("per_image", {}),
            "already_done": already_done,
        }

    for img_path in image_paths:
        img_name = img_path.name

        # Procesar solo motores que aun no tengan esta imagen (modo resume parcial)
        pending_engines = [
            eng for eng in ocr_engines
            if img_name not in per_engine[eng]["already_done"]
        ]
        if not pending_engines:
            continue

        print(f"    {img_name} ...", end="", flush=True)
        img_bgr = dc.load_image(str(img_path))

        # --- Deteccion ---
        boxes, duplicates, det_ms = run_detection(img_bgr, str(img_path), cfg)
        num_boxes = len(boxes)

        print(f" boxes={num_boxes}, dups={duplicates}, det={det_ms:.0f}ms")

        for ocr_engine in pending_engines:
            # --- OCR ---
            can_run_engine = (
                (ocr_engine == "easyocr" and "easyocr" in engine_ctx)
                or (ocr_engine == "tesseract")
                or (ocr_engine == "paddle" and "paddle" in engine_ctx)
                or (
                    ocr_engine == "deepseek"
                    and "deepseek_model" in engine_ctx
                    and "deepseek_tokenizer" in engine_ctx
                    and not bool(engine_ctx.get("deepseek_disabled", False))
                )
            )

            if num_boxes > 0 and can_run_engine:
                ocr_start = time.perf_counter()
                if ocr_engine == "easyocr":
                    ocr_data = run_easyocr_on_regions(img_bgr, boxes, engine_ctx["easyocr"])
                elif ocr_engine == "tesseract":
                    ocr_data = run_tesseract_on_regions(img_bgr, boxes)
                elif ocr_engine == "paddle":
                    ocr_data = run_paddle_on_regions(img_bgr, boxes, engine_ctx["paddle"])
                elif ocr_engine == "deepseek":
                    try:
                        ocr_data = run_deepseek_on_regions(
                            img_bgr,
                            boxes,
                            engine_ctx["deepseek_model"],
                            engine_ctx["deepseek_tokenizer"],
                            engine_ctx.get(
                                "deepseek_prompt",
                                (
                                    "<image>\n"
                                    "Extract all readable text from this document region. "
                                    "Keep original reading order and line breaks. "
                                    "Output plain text only, without markdown, explanations, "
                                    "or extra symbols. Languages may include Spanish and English."
                                ),
                            ),
                            base_size=int(engine_ctx.get("deepseek_base_size", 1024)),
                            image_size=int(engine_ctx.get("deepseek_image_size", 1024)),
                            crop_mode=bool(engine_ctx.get("deepseek_crop_mode", False)),
                        )
                    except DeepSeekFatalError as fatal_exc:
                        engine_ctx["deepseek_disabled"] = True
                        print(
                            "    [WARN] DeepSeek desactivado para el resto de la ejecución "
                            f"por error fatal interno: {fatal_exc}"
                        )
                        ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                else:
                    ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                ocr_ms = (time.perf_counter() - ocr_start) * 1000
            else:
                ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                ocr_ms = 0.0

            per_image = per_engine[ocr_engine]["per_image"]
            per_image[img_name] = {
                "num_boxes": num_boxes,
                "duplicates": duplicates,
                "det_ms": round(det_ms, 1),
                "ocr_ms": round(ocr_ms, 1),
                "total_chars": ocr_data["total_chars"],
                "total_words": ocr_data["total_words"],
                "per_region": ocr_data["per_region"],
            }

            total_ms = det_ms + ocr_ms
            print(
                f"      [{ocr_engine}] chars={ocr_data['total_chars']}, "
                f"words={ocr_data['total_words']}, time={total_ms:.0f}ms"
            )

            # Guardado incremental por motor
            _save_config_results(
                per_engine[ocr_engine]["results_file"],
                cfg,
                label,
                per_image,
            )

    # --- Calcular agregados finales por motor ---
    summaries: List[Dict[str, Any]] = []
    for ocr_engine in ocr_engines:
        per_image = per_engine[ocr_engine]["per_image"]

        n_imgs = len(per_image)
        total_chars = sum(v["total_chars"] for v in per_image.values())
        total_words = sum(v["total_words"] for v in per_image.values())
        total_dups = sum(v["duplicates"] for v in per_image.values())
        mean_boxes = sum(v["num_boxes"] for v in per_image.values()) / max(n_imgs, 1)
        mean_det_ms = sum(v["det_ms"] for v in per_image.values()) / max(n_imgs, 1)
        mean_ocr_ms = sum(v["ocr_ms"] for v in per_image.values()) / max(n_imgs, 1)
        imgs_no_boxes = sum(1 for v in per_image.values() if v["num_boxes"] == 0)

        # Formula de scoring OCR
        ocr_score = (
            total_chars * CHARS_WEIGHT
            + total_words * WORDS_WEIGHT
            - total_dups * DUP_PENALTY
            - imgs_no_boxes * MISSED_PENALTY
        )

        summary = {
            "config": cfg,
            "label": label,
            "ocr_engine": ocr_engine,
            "n_images": n_imgs,
            "total_chars": total_chars,
            "total_words": total_words,
            "total_duplicates": total_dups,
            "mean_boxes": round(mean_boxes, 2),
            "imgs_no_boxes": imgs_no_boxes,
            "mean_det_ms": round(mean_det_ms, 1),
            "mean_ocr_ms": round(mean_ocr_ms, 1),
            "ocr_score": round(ocr_score, 2),
            "per_image": per_image,
        }

        _save_config_results(
            per_engine[ocr_engine]["results_file"],
            cfg,
            label,
            per_image,
            summary,
        )
        summaries.append(summary)

    return summaries


def _save_config_results(
    path: Path,
    cfg: Dict,
    label: str,
    per_image: Dict,
    summary: Optional[Dict] = None,
) -> None:
    """Guardado incremental a disco."""
    data = {"config": cfg, "label": label, "per_image": per_image}
    if summary:
        data.update({k: v for k, v in summary.items() if k != "per_image"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Generacion de informes
# ---------------------------------------------------------------------------

def generate_reports(summaries: List[Dict[str, Any]]) -> None:
    """Genera ocr_validation_report.json / .txt / .csv"""

    if not summaries:
        print("[WARN] No hay resultados para generar informe.")
        return

    # --- JSON completo ---
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        # No incluir per_image en el JSON de alto nivel para que sea legible
        compact = [{k: v for k, v in s.items() if k != "per_image"} for s in summaries]
        json.dump(compact, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Informe JSON: {REPORT_JSON}")

    # --- CSV ---
    rows = []
    for s in summaries:
        cfg = s["config"]
        rows.append({
            "label": s["label"],
            "ocr_engine": s.get("ocr_engine", "easyocr"),
            "method": cfg["method"],
            "conf": cfg.get("conf", ""),
            "nms_iou": cfg.get("nms_iou", ""),
            "merge_distance": cfg["merge_distance"],
            "total_chars": s["total_chars"],
            "total_words": s["total_words"],
            "total_duplicates": s["total_duplicates"],
            "mean_boxes": s["mean_boxes"],
            "imgs_no_boxes": s["imgs_no_boxes"],
            "mean_det_ms": s["mean_det_ms"],
            "mean_ocr_ms": s["mean_ocr_ms"],
            "ocr_score": s["ocr_score"],
        })

    if HAS_PANDAS:
        df = pd.DataFrame(rows).sort_values("ocr_score", ascending=False)
        df.to_csv(REPORT_CSV, index=False, encoding="utf-8")
        print(f"[OK] Informe CSV: {REPORT_CSV}")
    else:
        # Escribir CSV manual
        import csv
        with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"[OK] Informe CSV: {REPORT_CSV}")

    # --- TXT legible ---
    _write_txt_report(summaries)
    print(f"[OK] Informe TXT: {REPORT_TXT}")


def _write_txt_report(summaries: List[Dict[str, Any]]) -> None:
    """Escribe un informe TXT tabulado con la comparacion."""
    # Ordenar por ocr_score descendente
    ranked = sorted(summaries, key=lambda s: s["ocr_score"], reverse=True)

    lines = []
    lines.append("=" * 100)
    lines.append("FASE 4 — VALIDACION OCR COMPLETO: COMPARACION DE CONFIGURACIONES")
    lines.append("=" * 100)
    lines.append("")

    # Tabla resumen
    col_w = [42, 10, 8, 8, 8, 8, 8, 10, 10]
    headers = [
        "Configuracion", "OCR", "Chars", "Palabras", "Dups", "Bxs/img",
        "NoBx", "Det(ms)", "OCR(ms)", "SCORE"
    ]
    sep = "  ".join("-" * w for w in col_w)
    header_row = "  ".join(h.ljust(col_w[i]) for i, h in enumerate(headers))

    lines.append(header_row)
    lines.append(sep)

    for rank, s in enumerate(ranked, start=1):
        row = [
            f"#{rank} {s['label']}"[:col_w[0]].ljust(col_w[0]),
            s.get("ocr_engine", "easyocr")[:col_w[1]].ljust(col_w[1]),
            str(s["total_chars"]).rjust(col_w[2]),
            str(s["total_words"]).rjust(col_w[3]),
            str(s["total_duplicates"]).rjust(col_w[4]),
            f"{s['mean_boxes']:.1f}".rjust(col_w[5]),
            str(s["imgs_no_boxes"]).rjust(col_w[6]),
            f"{s['mean_det_ms']:.0f}".rjust(col_w[7]),
            f"{s['mean_ocr_ms']:.0f}".rjust(col_w[8]),
            f"{s['ocr_score']:.1f}".rjust(col_w[9]),
        ]
        lines.append("  ".join(row))

    lines.append(sep)
    lines.append("")

    # Detalle por configuracion ganadora
    winner = ranked[0]
    lines.append("=" * 60)
    lines.append(f"GANADOR: {winner['label']}")
    lines.append("=" * 60)
    lines.append(f"  Metodo          : {winner['config']['method']}")
    lines.append(f"  OCR engine      : {winner.get('ocr_engine', 'easyocr')}")
    if "conf" in winner["config"]:
        lines.append(f"  Confianza       : {winner['config']['conf']}")
    lines.append(f"  NMS IoU         : {winner['config'].get('nms_iou', 'N/A')}")
    lines.append(f"  Merge distance  : {winner['config']['merge_distance']} px")
    lines.append(f"  Total caracteres: {winner['total_chars']}")
    lines.append(f"  Total palabras  : {winner['total_words']}")
    lines.append(f"  Duplicados tot. : {winner['total_duplicates']}")
    lines.append(f"  Imgs sin detec. : {winner['imgs_no_boxes']}")
    lines.append(f"  Tiempo det. med.: {winner['mean_det_ms']:.0f} ms/imagen")
    lines.append(f"  Tiempo OCR med. : {winner['mean_ocr_ms']:.0f} ms/imagen")
    lines.append(f"  Score OCR       : {winner['ocr_score']:.1f}")
    lines.append("")

    # Detalle por imagen del ganador
    lines.append("Detalle por imagen (ganador):")
    lines.append("-" * 60)
    per_img_hdr = f"  {'Imagen':<20} {'Boxes':>5} {'Dups':>4} {'Chars':>7} {'Words':>6}"
    lines.append(per_img_hdr)
    for img_name, img_data in sorted(winner["per_image"].items()):
        lines.append(
            f"  {img_name:<20} {img_data['num_boxes']:>5} {img_data['duplicates']:>4} "
            f"{img_data['total_chars']:>7} {img_data['total_words']:>6}"
        )
    lines.append("")

    # Formula de scoring
    lines.append("Formula de scoring OCR:")
    lines.append(
        f"  score = chars*{CHARS_WEIGHT} + words*{WORDS_WEIGHT} "
        f"- duplicados*{DUP_PENALTY} - imgs_sin_deteccion*{MISSED_PENALTY}"
    )
    lines.append("")

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FASE 4 — Validacion OCR con las mejores configuraciones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--top", type=int, default=3, metavar="N",
        help="Numero de configuraciones a validar desde el ranking (default: 3)"
    )
    parser.add_argument(
        "--method", type=str, default=None,
        choices=["opencv", "doclayout", "yolo11", "paddleocr", "docling"],
        help="Filtrar por metodo al leer el ranking"
    )
    parser.add_argument(
        "--configs", type=str, default=None, metavar="JSON",
        help="Lista de configuraciones en JSON (modo manual, no necesita Phase 3)"
    )
    parser.add_argument(
        "--images-dir", type=Path, default=IMGS_DIR,
        help=f"Directorio de imagenes (default: {IMGS_DIR})"
    )
    parser.add_argument(
        "--ranking-csv", type=Path, default=RANKING_CSV,
        help=f"CSV de ranking generado por analyze_experiments.py (default: {RANKING_CSV})"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=RESULTS_DIR,
        help=f"Directorio de salida (default: {RESULTS_DIR})"
    )
    parser.add_argument(
        "--no-ocr", action="store_true",
        help="Solo ejecutar deteccion, sin OCR (mas rapido para debug)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Reanudar ejecucion anterior (salta imagenes ya procesadas)"
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="Generar informe leyendo resultados existentes sin reejecutar"
    )
    parser.add_argument(
        "--langs", type=str, default="es,en",
        help="Idiomas para EasyOCR separados por coma (default: es,en)"
    )
    parser.add_argument(
        "--ocr-engines", type=str, default="easyocr,tesseract,paddle,deepseek",
        help="Motores OCR a usar separados por coma (easyocr,tesseract,paddle,deepseek)"
    )
    parser.add_argument(
        "--deepseek-model-path", type=str, default=str(DEEPSEEK_DEFAULT_MODEL_DIR),
        help=(
            "Ruta local del modelo DeepSeek-OCR "
            f"(default: {DEEPSEEK_DEFAULT_MODEL_DIR}; sobreescribe si quieres otra ruta)"
        )
    )
    parser.add_argument(
        "--deepseek-prompt",
        type=str,
        default=(
            "<image>\n"
            "Extract all readable text from this document region. "
            "Keep original reading order and line breaks. "
            "Output plain text only, without markdown, explanations, "
            "or extra symbols. Languages may include Spanish and English."
        ),
        help="Prompt para inferencia DeepSeek por region"
    )
    parser.add_argument(
        "--deepseek-base-size", type=int, default=1024,
        help="Base size de DeepSeek por region (default: 1024; evita bug param_img)"
    )
    parser.add_argument(
        "--deepseek-image-size", type=int, default=1024,
        help="Image size de DeepSeek por region (default: 1024; evita bug param_img)"
    )
    parser.add_argument(
        "--deepseek-crop-mode", action="store_true",
        help="Activar crop_mode de DeepSeek (default: desactivado)"
    )
    parser.add_argument(
        "--tesseract-cmd", type=str, default=None,
        help="Ruta a tesseract.exe (opcional, para Windows)"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # --- Modo report-only ---
    if args.report_only:
        summaries = _load_existing_summaries(args.output_dir)
        if not summaries:
            sys.exit(
                "[ERROR] No se encontraron resultados en validation_results/\n"
                "        Ejecuta primero sin --report-only"
            )
        generate_reports(summaries)
        _print_ranking_table(summaries)
        return

    # --- Buscar imagenes ---
    images_dir = args.images_dir
    if not images_dir.exists():
        sys.exit(f"[ERROR] Directorio de imagenes no encontrado: {images_dir}")

    image_paths = sorted(
        p for p in images_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        sys.exit(f"[ERROR] No se encontraron imagenes en: {images_dir}")

    print(f"[i] Imagenes encontradas: {len(image_paths)} en {images_dir}")

    # --- Cargar configuraciones ---
    if args.configs:
        try:
            configs = json.loads(args.configs)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERROR] --configs no es JSON valido: {e}")
        print(f"[i] Modo manual: {len(configs)} configuraciones especificadas")
    else:
        configs = load_top_configs_from_ranking(
            args.ranking_csv, top_n=args.top, method_filter=args.method
        )
        print(f"[i] Top-{args.top} configuraciones del ranking:")

    for cfg in configs:
        print(f"    {build_config_label(cfg)}")
    print()

    # --- Resolver motores OCR solicitados ---
    requested_engines = [e.strip().lower() for e in args.ocr_engines.split(",") if e.strip()]
    invalid = [e for e in requested_engines if e not in SUPPORTED_ENGINES]
    if invalid:
        sys.exit(f"[ERROR] Motores OCR no validos: {invalid}. Validos: {SUPPORTED_ENGINES}")

    if args.no_ocr:
        active_engines: List[str] = []
        print("[WARN] --no-ocr activo: se ejecutara solo deteccion.")
    else:
        active_engines = []
        engine_ctx: Dict[str, Any] = {}

        # EasyOCR
        if "easyocr" in requested_engines:
            if HAS_EASYOCR:
                langs = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
                print(f"[i] Inicializando EasyOCR (idiomas: {langs})...")
                t0 = time.perf_counter()
                engine_ctx["easyocr"] = easyocr.Reader(langs, gpu=False, verbose=False)
                print(f"[OK] EasyOCR listo en {(time.perf_counter()-t0)*1000:.0f}ms")
                active_engines.append("easyocr")
            else:
                print("[WARN] easyocr solicitado pero no disponible; se omite.")

        # Tesseract
        if "tesseract" in requested_engines:
            if HAS_TESSERACT:
                if args.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd
                active_engines.append("tesseract")
                print("[OK] Tesseract disponible")
            else:
                print("[WARN] tesseract solicitado pero pytesseract no disponible; se omite.")

        # PaddleOCR
        if "paddle" in requested_engines:
            if HAS_PADDLE_OCR:
                print("[i] Inicializando PaddleOCR...")
                t0 = time.perf_counter()
                engine_ctx["paddle"] = PaddleOCR(lang="es", use_textline_orientation=False)
                print(f"[OK] PaddleOCR listo en {(time.perf_counter()-t0)*1000:.0f}ms")
                active_engines.append("paddle")
            else:
                print("[WARN] paddle solicitado pero paddleocr no disponible; se omite.")

        # DeepSeek local
        if "deepseek" in requested_engines:
            deepseek_ready = False
            deepseek_model_path = Path(args.deepseek_model_path)
            if HAS_DEEPSEEK_DEPS:
                if not torch.cuda.is_available():
                    print("[WARN] deepseek solicitado pero CUDA no disponible; se omite.")
                elif not deepseek_model_path.exists():
                    print(
                        "[WARN] Modelo DeepSeek no encontrado en "
                        f"'{deepseek_model_path}'. Ejecuta install.bat o usa --deepseek-model-path."
                    )
                else:
                    print("[i] Inicializando DeepSeek OCR local...")
                    t0 = time.perf_counter()
                    try:
                        tokenizer, model, attn_impl = _load_deepseek_model_with_fallback(deepseek_model_path)
                        engine_ctx["deepseek_model"] = model
                        engine_ctx["deepseek_tokenizer"] = tokenizer
                        engine_ctx["deepseek_prompt"] = args.deepseek_prompt
                        engine_ctx["deepseek_base_size"] = int(args.deepseek_base_size)
                        engine_ctx["deepseek_image_size"] = int(args.deepseek_image_size)
                        engine_ctx["deepseek_crop_mode"] = bool(args.deepseek_crop_mode)
                        print(
                            f"[OK] DeepSeek listo en {(time.perf_counter()-t0)*1000:.0f}ms "
                            f"(attn={attn_impl}, base={args.deepseek_base_size}, "
                            f"img={args.deepseek_image_size}, crop={args.deepseek_crop_mode})"
                        )
                        deepseek_ready = True
                    except Exception as exc:
                        msg = str(exc)
                        if "LlamaFlashAttention2" in msg:
                            msg += (
                                " | Sugerencia: instala transformers compatible y/o usa fallback eager. "
                                "Ejemplo: pip install \"transformers>=4.51.1,<4.56.0\""
                            )
                        print(
                            "[WARN] No se pudo inicializar DeepSeek; se omite este motor. "
                            f"Detalle: {msg}"
                        )
            else:
                print("[WARN] deepseek solicitado pero faltan dependencias (torch/transformers); se omite.")
            if deepseek_ready:
                active_engines.append("deepseek")

        if not active_engines:
            print("[WARN] Ningun motor OCR disponible; se ejecutara solo deteccion.")
            engine_ctx = {}

        print(f"[i] Motores OCR activos: {active_engines if active_engines else ['none']}\n")

    # --- Ejecutar cada configuracion ---
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []

    for i, cfg in enumerate(configs, start=1):
        label = build_config_label(cfg)
        print(f"[{i}/{len(configs)}] {label}")

        engines_to_run = active_engines if not args.no_ocr else ["none"]
        print(f"    [OCR: {', '.join(engines_to_run)}]")

        if engines_to_run == ["none"]:
            cfg_summaries = run_config(
                cfg,
                image_paths,
                ["none"],
                {},
                args.output_dir,
                resume=args.resume,
            )
        else:
            cfg_summaries = run_config(
                cfg,
                image_paths,
                engines_to_run,
                engine_ctx,
                args.output_dir,
                resume=args.resume,
            )

        for summary in cfg_summaries:
            summaries.append(summary)
            print(
                f"      -> [{summary.get('ocr_engine', 'none')}] "
                f"chars={summary['total_chars']}, words={summary['total_words']}, "
                f"dups={summary['total_duplicates']}, score={summary['ocr_score']:.1f}"
            )
        print()

    # --- Informes ---
    generate_reports(summaries)
    _print_ranking_table(summaries)


def _load_existing_summaries(output_dir: Path) -> List[Dict[str, Any]]:
    """Carga los resultados existentes de cada subdirectorio de validation_results."""
    summaries = []
    if not output_dir.exists():
        return summaries
    for config_dir in sorted(output_dir.iterdir()):
        if not config_dir.is_dir():
            continue
        for results_file in sorted(config_dir.glob("results*.json")):
            with open(results_file, encoding="utf-8") as f:
                data = json.load(f)
            if "per_image" in data and "ocr_score" in data:
                if "ocr_engine" not in data:
                    data["ocr_engine"] = "easyocr"
                summaries.append(data)
    return summaries


def _print_ranking_table(summaries: List[Dict[str, Any]]) -> None:
    """Imprime tabla resumen en consola."""
    ranked = sorted(summaries, key=lambda s: s["ocr_score"], reverse=True)

    print()
    print("=" * 90)
    print("RANKING FINAL — VALIDACION OCR")
    print("=" * 90)
    print(f"  {'#':<3} {'Configuracion':<36} {'OCR':<10} {'Chars':>7} {'Words':>6} {'Dups':>5} {'Score':>9}")
    print(f"  {'-'*3} {'-'*36} {'-'*10} {'-'*7} {'-'*6} {'-'*5} {'-'*9}")
    for rank, s in enumerate(ranked, start=1):
        marker = " <-- GANADOR" if rank == 1 else ""
        print(
            f"  {rank:<3} {s['label']:<36} {s.get('ocr_engine', 'easyocr'):<10} {s['total_chars']:>7} "
            f"{s['total_words']:>6} {s['total_duplicates']:>5} {s['ocr_score']:>9.1f}{marker}"
        )
    print("=" * 90)
    print()
    print(f"Informes guardados en:")
    print(f"  {REPORT_TXT}")
    print(f"  {REPORT_CSV}")
    print(f"  {REPORT_JSON}")


if __name__ == "__main__":
    main()
