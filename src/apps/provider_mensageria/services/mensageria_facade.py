"""Facade de mensageria — GoF Estrutural (Issue #16).

Encapsula os 4 subsistemas envolvidos no fluxo de mensageria do Telegram
(`AuthService`, `ProviderLLM`, `OpenAIAdapter`/`OpenAiClient` e
`ToolExecutor`/`ToolRegistry`) atrás de um único método público —
``processar_mensagem(telegram_user_id, texto) -> str``.

O webhook não conhece nenhum dos subsistemas: depende apenas desta classe,
o que reduz o acoplamento descrito nos diagramas de Sequência e Atividades.
"""

from __future__ import annotations

import re
from typing import Callable

from apps.provider_llm.adapters.openai_adapter import OpenAIAdapter
from apps.provider_llm.clients.openai_client import OpenAiClient
from apps.provider_llm.services.provider_llm import ProviderLLM
from apps.provider_llm.services.tool_executor import ToolExecutor
from apps.provider_llm.tools.registry import ToolRegistry
from apps.provider_mensageria.services.auth_service import AuthService
from apps.provider_mensageria.services.conversation_store import ConversationStore


class MensageriaFacade:
    """Ponto único de entrada para mensagens recebidas pelo webhook do Telegram."""

    MSG_NAO_AUTENTICADO = (
        "Olá! Sua conta do Telegram ainda não está vinculada à sua conta no "
        "Finanças. Acesse o app e vincule seu Telegram para conversar comigo."
    )

    SYSTEM_PROMPT = (
        "Você é o assistente do app Finanças, conversando em português "
        "brasileiro com um usuário do Telegram. Ao chamar tools, use ponto "
        "como separador decimal e no máximo duas casas decimais, sem pedir "
        "confirmação ao usuário sobre o formato do número."
    )

    _RE_NUMERO_PTBR = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d{3})+|\d+),(\d{1,2})(?!\d)")

    def __init__(
        self,
        provider_llm: ProviderLLM | None = None,
        auth_service: AuthService | None = None,
        registry_factory: Callable[..., ToolRegistry] | None = None,
        executor_factory: Callable[[ToolRegistry], ToolExecutor] | None = None,
        conversation_store: ConversationStore | None = None,
    ) -> None:
        self._provider = provider_llm or self._default_provider()
        self._auth = auth_service or AuthService()
        self._registry_factory = registry_factory or ToolRegistry
        self._executor_factory = executor_factory or ToolExecutor
        self._store = conversation_store or ConversationStore()

    @staticmethod
    def _default_provider() -> ProviderLLM:
        client = OpenAiClient()
        adapter = OpenAIAdapter(client)
        return ProviderLLM(llm=adapter)

    def processar_mensagem(self, telegram_user_id: str, texto: str) -> str:
        """Orquestra o fluxo: auth → preparar tools → LLM → tools → resposta."""
        usuario = self._auth.validar_user(telegram_user_id)
        if usuario is None:
            return self.MSG_NAO_AUTENTICADO

        texto_normalizado = self._normalizar_numeros(texto)
        registry = self._registry_factory(usuario=usuario)
        executor = self._executor_factory(registry)
        historico = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self._store.carregar(telegram_user_id),
        ]
        resposta = self._provider.conversar(
            mensagem=texto_normalizado,
            tools=registry.schemas(),
            tool_executor=executor,
            historico=historico,
        )
        conteudo = resposta.conteudo or ""
        if conteudo:
            self._store.adicionar_turno(telegram_user_id, texto, conteudo)
        return conteudo

    @classmethod
    def _normalizar_numeros(cls, texto: str) -> str:
        """Converte números pt-BR (\"1.234,56\") para o formato esperado pelo LLM."""
        def _troca(match: re.Match[str]) -> str:
            inteiro = match.group(1).replace(".", "")
            return f"{inteiro}.{match.group(2)}"

        return cls._RE_NUMERO_PTBR.sub(_troca, texto)
