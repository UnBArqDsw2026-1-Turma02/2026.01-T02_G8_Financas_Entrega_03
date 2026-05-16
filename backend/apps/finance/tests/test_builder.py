"""Testes unitários do Builder e Director do Extrato (Issue #04)."""

from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finance.models import (
    Categoria,
    Pagamento,
    TipoGasto,
    Transacao,
)
from apps.finance.services import (
    Extrato,
    ExtratoDirector,
    ExtratoFinanceiroBuilder,
    FinancasTransacaoService,
)

User = get_user_model()


def _set_data(transacao: Transacao, ano: int, mes: int, dia: int = 15) -> None:
    """Sobrescreve `data` (auto_now_add) para cenários de filtro temporal."""
    Transacao.objects.filter(pk=transacao.pk).update(
        data=datetime(ano, mes, dia, 12, 0, tzinfo=timezone.utc)
    )


class ExtratoBuilderTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="x")
        self.outro = User.objects.create_user(username="bob", password="x")
        self.cat_mercado = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        self.cat_lazer = Categoria.objects.create(
            nome="Lazer",
            descricao="Hobbies",
            cor="#445566",
            usuario=self.user,
        )
        service = FinancasTransacaoService()
        self.entrada = service.criar_transacao(
            tipo="entrada",
            nome="Salário",
            valor=Decimal("5000.00"),
            usuario=self.user,
            fonte="Empresa X",
            recorrencia=True,
        )
        self.saida_mercado = service.criar_transacao(
            tipo="saida",
            nome="Feira semanal",
            valor=Decimal("200.00"),
            usuario=self.user,
            categoria=self.cat_mercado,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.saida_lazer = service.criar_transacao(
            tipo="saida",
            nome="Cinema",
            valor=Decimal("50.00"),
            usuario=self.user,
            categoria=self.cat_lazer,
            pagamento=Pagamento.CREDITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.parc = service.criar_transacao(
            tipo="parcelamento",
            nome="Notebook",
            valor=Decimal("3000.00"),
            usuario=self.user,
            categoria=self.cat_lazer,
            pagamento=Pagamento.CREDITO,
            num_parcelas=10,
        )
        # transação de outro usuário — não deve aparecer
        service.criar_transacao(
            tipo="entrada",
            nome="Renda do Bob",
            valor=Decimal("999.00"),
            usuario=self.outro,
            recorrencia=False,
        )

    def test_build_sem_filtros_retorna_todas_do_usuario(self) -> None:
        extrato = ExtratoFinanceiroBuilder(self.user).build()
        self.assertIsInstance(extrato, Extrato)
        self.assertEqual(len(extrato.transacoes), 4)
        self.assertEqual(extrato.filtros_aplicados, {})
        # saldo = 5000 - 200 - 50 - 300 (valor_parcela) = 4450
        self.assertEqual(extrato.saldo_atual, Decimal("4450.00"))

    def test_filtro_tipo_entrada(self) -> None:
        extrato = ExtratoFinanceiroBuilder(self.user).filtro_tipo("entrada").build()
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.entrada.pk)
        self.assertEqual(extrato.saldo_atual, Decimal("5000.00"))
        self.assertEqual(extrato.filtros_aplicados["tipo"], "entrada")

    def test_filtro_tipo_saida(self) -> None:
        extrato = ExtratoFinanceiroBuilder(self.user).filtro_tipo("SAIDA").build()
        self.assertEqual(len(extrato.transacoes), 2)
        self.assertEqual(extrato.saldo_atual, Decimal("-250.00"))

    def test_filtro_tipo_parcelamento(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user).filtro_tipo("parcelamento").build()
        )
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.parc.pk)

    def test_filtro_tipo_invalido_lanca_erro(self) -> None:
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            ExtratoFinanceiroBuilder(self.user).filtro_tipo("boleto")

    def test_filtro_categoria_inclui_saida_e_parcelamento(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user)
            .filtro_categoria(self.cat_lazer)
            .build()
        )
        # Lazer tem 1 saída + 1 parcelamento; Entradas não têm categoria.
        pks = {t.pk for t in extrato.transacoes}
        self.assertEqual(pks, {self.saida_lazer.pk, self.parc.pk})
        self.assertEqual(
            extrato.filtros_aplicados["categoria"]["nome"], "Lazer"
        )

    def test_filtro_pagamento_pix(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user)
            .filtro_pagamento(Pagamento.PIX)
            .build()
        )
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.saida_mercado.pk)

    def test_filtro_pagamento_aceita_string(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user)
            .filtro_pagamento("CREDITO")
            .build()
        )
        pks = {t.pk for t in extrato.transacoes}
        self.assertEqual(pks, {self.saida_lazer.pk, self.parc.pk})

    def test_filtro_tipo_gasto_so_inclui_saidas(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user)
            .filtro_tipo_gasto(TipoGasto.VARIAVEL)
            .build()
        )
        # Apenas saídas (não inclui parcelamento, embora tenha pagamento CRÉDITO)
        pks = {t.pk for t in extrato.transacoes}
        self.assertEqual(pks, {self.saida_mercado.pk, self.saida_lazer.pk})

    def test_pesquisa_nome_case_insensitive_parcial(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user).pesquisa_nome("noteb").build()
        )
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.parc.pk)

    def test_filtro_ano_mes(self) -> None:
        _set_data(self.entrada, 2026, 4)
        _set_data(self.saida_mercado, 2026, 5)
        _set_data(self.saida_lazer, 2026, 5)
        _set_data(self.parc, 2026, 6)
        extrato = (
            ExtratoFinanceiroBuilder(self.user).filtro_ano_mes(2026, 5).build()
        )
        pks = {t.pk for t in extrato.transacoes}
        self.assertEqual(pks, {self.saida_mercado.pk, self.saida_lazer.pk})
        self.assertEqual(
            extrato.filtros_aplicados["ano_mes"], {"ano": 2026, "mes": 5}
        )

    def test_filtro_ano_mes_rejeita_mes_invalido(self) -> None:
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            ExtratoFinanceiroBuilder(self.user).filtro_ano_mes(2026, 13)

    def test_fluent_interface_encadeia_multiplos_filtros(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user)
            .filtro_tipo("saida")
            .filtro_categoria(self.cat_lazer)
            .filtro_pagamento(Pagamento.CREDITO)
            .filtro_tipo_gasto(TipoGasto.VARIAVEL)
            .build()
        )
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.saida_lazer.pk)
        self.assertEqual(
            set(extrato.filtros_aplicados.keys()),
            {"tipo", "categoria", "pagamento", "tipo_gasto"},
        )

    def test_saldo_zero_quando_nao_ha_transacoes(self) -> None:
        extrato = (
            ExtratoFinanceiroBuilder(self.user).pesquisa_nome("inexistente").build()
        )
        self.assertEqual(extrato.transacoes, [])
        self.assertEqual(extrato.saldo_atual, Decimal("0.00"))

    def test_escopo_isolado_por_usuario(self) -> None:
        extrato = ExtratoFinanceiroBuilder(self.outro).build()
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].nome, "Renda do Bob")


class ExtratoDirectorTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="carol", password="x")
        self.categoria = Categoria.objects.create(
            nome="Transporte",
            descricao="Idas e vindas",
            cor="#778899",
            usuario=self.user,
        )
        service = FinancasTransacaoService()
        self.entrada_abril = service.criar_transacao(
            tipo="entrada",
            nome="Salário",
            valor=Decimal("3000"),
            usuario=self.user,
            recorrencia=True,
        )
        self.saida_maio = service.criar_transacao(
            tipo="saida",
            nome="Uber",
            valor=Decimal("80"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _set_data(self.entrada_abril, 2026, 4)
        _set_data(self.saida_maio, 2026, 5)

    def test_construir_extrato_mensal(self) -> None:
        director = ExtratoDirector(ExtratoFinanceiroBuilder(self.user))
        extrato = director.construir_extrato_mensal(2026, 5)
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.saida_maio.pk)
        self.assertEqual(extrato.saldo_atual, Decimal("-80.00"))

    def test_construir_extrato_por_categoria(self) -> None:
        director = ExtratoDirector(ExtratoFinanceiroBuilder(self.user))
        extrato = director.construir_extrato_por_categoria(self.categoria)
        self.assertEqual(len(extrato.transacoes), 1)
        self.assertEqual(extrato.transacoes[0].pk, self.saida_maio.pk)

    def test_construir_extrato_completo(self) -> None:
        director = ExtratoDirector(ExtratoFinanceiroBuilder(self.user))
        extrato = director.construir_extrato_completo()
        self.assertEqual(len(extrato.transacoes), 2)
        self.assertEqual(extrato.saldo_atual, Decimal("2920.00"))
        self.assertEqual(extrato.filtros_aplicados, {})
