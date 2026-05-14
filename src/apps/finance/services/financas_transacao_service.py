"""FinancasTransacaoService — ConcreteCreator do Factory Method (Issue #03).

Implementa o factory method `criar_transacao`, decidindo qual subclasse
concreta de `Transacao` instanciar a partir do parâmetro `tipo`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError

from apps.finance.models import Entrada, Parcelamento, Saida, Transacao
from apps.finance.services.orcamento_service import OrcamentoService
from apps.finance.services.transacao_service import TransacaoService

TIPO_ENTRADA = "entrada"
TIPO_SAIDA = "saida"
TIPO_PARCELAMENTO = "parcelamento"

TIPOS_VALIDOS = {TIPO_ENTRADA, TIPO_SAIDA, TIPO_PARCELAMENTO}


class FinancasTransacaoService(TransacaoService):
    def criar_transacao(self, tipo: str, **dados: Any) -> Transacao:
        tipo_normalizado = (tipo or "").strip().lower()
        if tipo_normalizado not in TIPOS_VALIDOS:
            raise ValidationError(
                {"tipo": f"Tipo de transação inválido: '{tipo}'."}
            )

        if tipo_normalizado == TIPO_ENTRADA:
            return self._criar_entrada(**dados)
        if tipo_normalizado == TIPO_SAIDA:
            return self._criar_saida(**dados)
        return self._criar_parcelamento(**dados)

    def _criar_entrada(self, **dados: Any) -> Entrada:
        entrada = Entrada(**dados)
        entrada.full_clean()
        entrada.save()
        OrcamentoService().recalcular_apos_transacao(entrada.usuario)
        return entrada

    def _criar_saida(self, **dados: Any) -> Saida:
        saida = Saida(**dados)
        saida.full_clean()
        saida.save()
        OrcamentoService().recalcular_apos_transacao(saida.usuario)
        return saida

    def _criar_parcelamento(self, **dados: Any) -> Parcelamento:
        dados.pop("valor_parcela", None)

        valor = dados.get("valor")
        num_parcelas = dados.get("num_parcelas")
        if valor is None or not num_parcelas:
            raise ValidationError(
                "Parcelamento requer 'valor' e 'num_parcelas'."
            )

        dados["valor_parcela"] = (
            Decimal(valor) / Decimal(num_parcelas)
        ).quantize(Decimal("0.01"))

        parcelamento = Parcelamento(**dados)
        parcelamento.full_clean()
        parcelamento.save()
        OrcamentoService().recalcular_apos_transacao(parcelamento.usuario)
        return parcelamento
