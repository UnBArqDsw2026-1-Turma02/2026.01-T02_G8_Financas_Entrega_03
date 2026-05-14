"""Testes unitários do Factory Method (Issue #03)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.finance.models import (
    Categoria,
    Entrada,
    Pagamento,
    Parcelamento,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services import FinancasTransacaoService, TransacaoService

User = get_user_model()


class FactoryMethodTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="eve", password="x")
        self.categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        self.service: TransacaoService = FinancasTransacaoService()

    def test_factory_cria_entrada(self) -> None:
        transacao = self.service.criar_transacao(
            tipo="entrada",
            nome="Salário",
            valor=Decimal("5000.00"),
            usuario=self.user,
            fonte="Empresa X",
            recorrencia=True,
        )
        self.assertIsInstance(transacao, Entrada)
        self.assertIsInstance(transacao, Transacao)
        self.assertEqual(transacao.fonte, "Empresa X")

    def test_factory_cria_saida(self) -> None:
        transacao = self.service.criar_transacao(
            tipo="saida",
            nome="Feira",
            valor=Decimal("120.50"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.assertIsInstance(transacao, Saida)
        self.assertEqual(transacao.categoria, self.categoria)

    def test_factory_cria_parcelamento_calcula_valor_parcela(self) -> None:
        transacao = self.service.criar_transacao(
            tipo="parcelamento",
            nome="Notebook",
            valor=Decimal("3000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=10,
        )
        self.assertIsInstance(transacao, Parcelamento)
        self.assertEqual(transacao.valor_parcela, Decimal("300.00"))
        self.assertEqual(transacao.parcela_atual, 1)

    def test_factory_ignora_valor_parcela_do_cliente(self) -> None:
        transacao = self.service.criar_transacao(
            tipo="parcelamento",
            nome="Geladeira",
            valor=Decimal("1000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=4,
            valor_parcela=Decimal("999.99"),
        )
        self.assertEqual(transacao.valor_parcela, Decimal("250.00"))

    def test_factory_parcelamento_sem_num_parcelas_falha(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.criar_transacao(
                tipo="parcelamento",
                nome="X",
                valor=Decimal("100"),
                usuario=self.user,
                categoria=self.categoria,
                pagamento=Pagamento.CREDITO,
            )

    def test_factory_normaliza_tipo_case_insensitive(self) -> None:
        transacao = self.service.criar_transacao(
            tipo="  Entrada  ",
            nome="Bônus",
            valor=Decimal("500"),
            usuario=self.user,
            recorrencia=False,
        )
        self.assertIsInstance(transacao, Entrada)

    def test_factory_tipo_invalido_lanca_erro(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.criar_transacao(
                tipo="boleto",
                nome="X",
                valor=Decimal("10"),
                usuario=self.user,
            )

    def test_factory_valor_invalido_propaga_validacao(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.criar_transacao(
                tipo="entrada",
                nome="X",
                valor=Decimal("0"),
                usuario=self.user,
                recorrencia=False,
            )

    def test_cliente_depende_apenas_da_abstracao(self) -> None:
        # Cliente recebe uma `Transacao` genérica e o tipo estático é o
        # abstrato `TransacaoService` — comprova o desacoplamento.
        service: TransacaoService = FinancasTransacaoService()
        transacao = service.criar_transacao(
            tipo="entrada",
            nome="Aluguel recebido",
            valor=Decimal("1200"),
            usuario=self.user,
            recorrencia=True,
        )
        self.assertIsInstance(transacao, Transacao)


class TransacaoServiceCRUDTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="frank", password="x")
        self.service: TransacaoService = FinancasTransacaoService()
        self.entrada = self.service.criar_transacao(
            tipo="entrada",
            nome="Salário",
            valor=Decimal("3000"),
            usuario=self.user,
            recorrencia=True,
        )

    def test_listar_filtra_por_usuario(self) -> None:
        outro = User.objects.create_user(username="other", password="x")
        self.service.criar_transacao(
            tipo="entrada",
            nome="Outra",
            valor=Decimal("100"),
            usuario=outro,
            recorrencia=False,
        )
        transacoes = list(self.service.listar_transacoes(self.user))
        self.assertEqual(len(transacoes), 1)
        self.assertEqual(transacoes[0].pk, self.entrada.pk)

    def test_editar_atualiza_campos_validos(self) -> None:
        editada = self.service.editar_transacao(
            self.entrada.pk, valor=Decimal("3500")
        )
        self.assertEqual(editada.valor, Decimal("3500"))

    def test_editar_propaga_validacao(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.editar_transacao(self.entrada.pk, valor=Decimal("0"))

    def test_excluir_remove_transacao(self) -> None:
        self.service.excluir_transacao(self.entrada.pk)
        self.assertFalse(Transacao.objects.filter(pk=self.entrada.pk).exists())


class AnteciparParcelaTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="gigi", password="x")
        self.categoria = Categoria.objects.create(
            nome="Eletrônicos",
            descricao="Gadgets",
            cor="#445566",
            usuario=self.user,
        )
        service: TransacaoService = FinancasTransacaoService()
        self.parc: Parcelamento = service.criar_transacao(  # type: ignore[assignment]
            tipo="parcelamento",
            nome="TV",
            valor=Decimal("1200"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=3,
        )

    def test_pode_editar_apenas_na_primeira_parcela(self) -> None:
        self.assertTrue(self.parc.pode_editar())
        self.parc.antecipar_parcela()
        self.assertFalse(self.parc.pode_editar())

    def test_antecipar_incrementa_parcela_atual(self) -> None:
        self.parc.antecipar_parcela()
        self.parc.refresh_from_db()
        self.assertEqual(self.parc.parcela_atual, 2)

    def test_antecipar_alem_do_total_lanca_erro(self) -> None:
        self.parc.antecipar_parcela()
        self.parc.antecipar_parcela()
        with self.assertRaises(ValidationError):
            self.parc.antecipar_parcela()
