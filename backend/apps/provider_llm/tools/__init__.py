"""Tools de IA (Issue #17).

Cada tool é uma função Python que reutiliza um service existente do domínio
financeiro para executar uma operação via *function calling*. Os schemas JSON
estão em `schemas.py` e o mapeamento nome → função fica no `ToolRegistry`.
"""

from apps.provider_llm.tools.registry import ToolRegistry
from apps.provider_llm.tools.schemas import TOOL_SCHEMAS

__all__ = ["ToolRegistry", "TOOL_SCHEMAS"]
