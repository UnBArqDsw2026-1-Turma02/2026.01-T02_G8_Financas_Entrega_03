"""DashboardService — agregações para o Dashboard (Issue #14).

Implementa as três visões do Theme 4 do backlog:

- **Visão geral**: totais de entradas, saídas fixas, saídas variáveis e saldo.
- **Gastos por categoria**: agrupa as saídas do período por categoria, com
  percentual de participação no total gasto.
- **Tendência diária**: série temporal com o total de saídas por dia no mês.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Categoria, Entrada, Parcelamento, Saida, TipoGasto

CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class VisaoGeral:
    total_entradas: Decimal
    total_saidas_fixas: Decimal
    total_saidas_variaveis: Decimal
    saldo_disponivel: Decimal


@dataclass(frozen=True)
class CategoriaAgregada:
    id: str
    nome: str
    cor: str
    total: Decimal
    percentual: Decimal


@dataclass(frozen=True)
class DiaAgregado:
    data: date
    total_gasto: Decimal


class DashboardService:
    """Encapsula as agregações usadas pelos endpoints de Dashboard."""

    def obter_visao_geral(
        self, usuario, ano: int | None = None, mes: int | None = None
    ) -> VisaoGeral:
        ano, mes = self._resolver_ano_mes(ano, mes)

        total_entradas = self._soma(
            Entrada.ativas_no_mes(usuario, ano, mes)
        )
        total_saidas_fixas_saidas = self._soma(
            Saida.objects.filter(
                usuario=usuario,
                tipo_gasto=TipoGasto.FIXO,
                data__year=ano,
                data__month=mes,
            )
        )
        total_parcelamentos = Decimal(
            Parcelamento.ativos_no_mes(usuario, ano, mes).aggregate(
                s=Sum("valor_parcela")
            )["s"]
            or ZERO
        ).quantize(CENTAVO)
        total_saidas_fixas = total_saidas_fixas_saidas + total_parcelamentos
        total_saidas_variaveis = self._soma(
            Saida.objects.filter(
                usuario=usuario,
                tipo_gasto=TipoGasto.VARIAVEL,
                data__year=ano,
                data__month=mes,
            )
        )
        saldo = (
            total_entradas - total_saidas_fixas - total_saidas_variaveis
        ).quantize(CENTAVO)

        return VisaoGeral(
            total_entradas=total_entradas,
            total_saidas_fixas=total_saidas_fixas,
            total_saidas_variaveis=total_saidas_variaveis,
            saldo_disponivel=saldo,
        )

    def obter_gastos_por_categoria(
        self, usuario, ano: int | None = None, mes: int | None = None
    ) -> list[CategoriaAgregada]:
        ano, mes = self._resolver_ano_mes(ano, mes)

        agregados_saidas = (
            Saida.objects.filter(
                usuario=usuario, data__year=ano, data__month=mes
            )
            .values("categoria_id")
            .annotate(total=Sum("valor"))
        )
        totais_por_id: dict = {}
        for item in agregados_saidas:
            totais_por_id[item["categoria_id"]] = item["total"] or ZERO

        # Parcelamentos entram pelo valor da parcela do mês (mesma regra do
        # `obter_visao_geral`: só os ativos na janela [início, início+N-1]).
        agregados_parcelas = (
            Parcelamento.ativos_no_mes(usuario, ano, mes)
            .values("categoria_id")
            .annotate(total=Sum("valor_parcela"))
        )
        for item in agregados_parcelas:
            cat_id = item["categoria_id"]
            totais_por_id[cat_id] = (
                totais_por_id.get(cat_id, ZERO) + (item["total"] or ZERO)
            )

        total_geral = sum(totais_por_id.values(), ZERO)

        categorias = Categoria.objects.filter(
            pk__in=totais_por_id.keys(), usuario=usuario
        )

        resultado: list[CategoriaAgregada] = []
        for categoria in categorias:
            total = Decimal(totais_por_id[categoria.pk]).quantize(CENTAVO)
            percentual = (
                (total / total_geral * Decimal("100")).quantize(CENTAVO)
                if total_geral > ZERO
                else ZERO
            )
            resultado.append(
                CategoriaAgregada(
                    id=str(categoria.pk),
                    nome=categoria.nome,
                    cor=categoria.cor,
                    total=total,
                    percentual=percentual,
                )
            )

        resultado.sort(key=lambda c: c.total, reverse=True)
        return resultado

    def obter_tendencia_diaria(
        self, usuario, ano: int | None = None, mes: int | None = None
    ) -> list[DiaAgregado]:
        ano, mes = self._resolver_ano_mes(ano, mes)
        dias_mes = calendar.monthrange(ano, mes)[1]

        agregados = (
            Saida.objects.filter(
                usuario=usuario, data__year=ano, data__month=mes
            )
            .values("data__day")
            .annotate(total=Sum("valor"))
        )
        por_dia = {
            item["data__day"]: (item["total"] or ZERO) for item in agregados
        }

        serie: list[DiaAgregado] = []
        for dia in range(1, dias_mes + 1):
            total = Decimal(por_dia.get(dia, ZERO)).quantize(CENTAVO)
            serie.append(DiaAgregado(data=date(ano, mes, dia), total_gasto=total))
        return serie

    @staticmethod
    def _resolver_ano_mes(
        ano: int | None, mes: int | None
    ) -> tuple[int, int]:
        hoje = timezone.localdate()
        return (ano or hoje.year, mes or hoje.month)

    @staticmethod
    def _soma(queryset) -> Decimal:
        total = queryset.aggregate(s=Sum("valor"))["s"] or ZERO
        return Decimal(total).quantize(CENTAVO)
