"""Facade de mensageria — GoF Estrutural (Issue #16).

Encapsula os 4 subsistemas envolvidos no fluxo de mensageria do Telegram
(`AuthService`, `ProviderLLM`, `OpenAIAdapter`/`OpenAiClient` e
`ToolExecutor`/`ToolRegistry`) atrás de um único método público —
``processar_mensagem(telegram_user_id, texto) -> str``.

O webhook não conhece nenhum dos subsistemas: depende apenas desta classe,
o que reduz o acoplamento descrito nos diagramas de Sequência e Atividades.
"""

from __future__ import annotations

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

        registry = self._registry_factory(usuario=usuario)
        executor = self._executor_factory(registry)
        historico = self._store.carregar(telegram_user_id)
        resposta = self._provider.conversar(
            mensagem=texto,
            tools=registry.schemas(),
            tool_executor=executor,
            historico=historico,
        )
        conteudo = resposta.conteudo or ""
        if conteudo:
            self._store.adicionar_turno(telegram_user_id, texto, conteudo)
        return conteudo
