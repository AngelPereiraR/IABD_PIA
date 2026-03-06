import builtins
import importlib
import sys


_original_import = builtins.__import__
_patch_in_progress = False


def _patch_transformers_llama_flash_attention() -> None:
    global _patch_in_progress

    if _patch_in_progress:
        return

    try:
        modeling_llama = sys.modules.get("transformers.models.llama.modeling_llama")
        if modeling_llama is None:
            _patch_in_progress = True
            modeling_llama = importlib.import_module("transformers.models.llama.modeling_llama")
    except Exception:
        return
    finally:
        _patch_in_progress = False

    if getattr(modeling_llama.LlamaAttention, "_copilot_compat_shim", False) and hasattr(
        modeling_llama, "LlamaFlashAttention2"
    ):
        return

    try:
        import torch
    except Exception:
        return

    BaseLlamaAttention = getattr(
        modeling_llama,
        "_copilot_original_LlamaAttention",
        modeling_llama.LlamaAttention,
    )
    LlamaRotaryEmbedding = modeling_llama.LlamaRotaryEmbedding

    class CompatibleLlamaAttention(BaseLlamaAttention):
        _copilot_compat_shim = True

        def __init__(self, config, layer_idx):
            super().__init__(config=config, layer_idx=layer_idx)
            self.rotary_emb = LlamaRotaryEmbedding(config)

        def forward(
            self,
            hidden_states,
            *args,
            **kwargs,
        ):
            if args and isinstance(args[0], tuple):
                return super().forward(hidden_states, *args, **kwargs)

            attention_mask = kwargs.pop("attention_mask", args[0] if args else None)
            position_ids = kwargs.pop("position_ids", None)
            past_key_value = kwargs.pop("past_key_value", None)
            output_attentions = kwargs.pop("output_attentions", False)
            kwargs.pop("use_cache", None)
            position_embeddings = kwargs.pop("position_embeddings", None)
            cache_position = kwargs.pop("cache_position", None)

            if position_embeddings is None:
                if position_ids is None:
                    seq_len = hidden_states.shape[1]
                    start = 0
                    if past_key_value is not None and getattr(self, "layer_idx", None) is not None:
                        start = past_key_value.get_usable_length(seq_len, self.layer_idx)
                    position_ids = torch.arange(
                        start,
                        start + seq_len,
                        device=hidden_states.device,
                    ).unsqueeze(0)

                if position_ids.dim() == 1:
                    position_ids = position_ids.unsqueeze(0)

                position_embeddings = self.rotary_emb(hidden_states, position_ids)

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

            return attn_output, attn_weights, past_key_value

    class LlamaFlashAttention2(CompatibleLlamaAttention):
        pass

    modeling_llama._copilot_original_LlamaAttention = BaseLlamaAttention
    modeling_llama.LlamaAttention = CompatibleLlamaAttention
    modeling_llama.LlamaFlashAttention2 = LlamaFlashAttention2


def _patch_transformers_cache_compat() -> None:
    try:
        from transformers.cache_utils import DynamicCache
    except Exception:
        return

    if hasattr(DynamicCache, "get_max_length"):
        return

    def get_max_length(self):
        return self.get_max_cache_shape()

    DynamicCache.get_max_length = get_max_length


def _patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)

    if name == "transformers.models.llama.modeling_llama" or name.startswith(
        "transformers.models.llama"
    ):
        _patch_transformers_llama_flash_attention()

    return module


if builtins.__import__ is not _patched_import:
    builtins.__import__ = _patched_import

_patch_transformers_llama_flash_attention()
_patch_transformers_cache_compat()