"""Testes unitários dos models do domínio financeiro."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
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

User = get_user_model()


class CategoriaModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="x")

    def test_cria_categoria_valida(self) -> None:
        cat = Categoria.objects.create(
            nome="Alimentação",
            descricao="Compras de mercado e refeições",
            cor="#FF8800",
            usuario=self.user,
        )
        self.assertEqual(str(cat), "Alimentação")
        self.assertIsNotNone(cat.id)

    def test_nome_vazio_invalido(self) -> None:
        cat = Categoria(nome="", descricao="x", cor="#000000", usuario=self.user)
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_descricao_vazia_invalida(self) -> None:
        cat = Categoria(nome="Lazer", descricao="", cor="#000000", usuario=self.user)
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_edita_e_exclui(self) -> None:
        cat = Categoria.objects.create(
            nome="Saúde", descricao="Plano e farmácia", cor="#00AA00", usuario=self.user
        )
        cat.nome = "Saúde e Bem-estar"
        cat.save()
        cat.refresh_from_db()
        self.assertEqual(cat.nome, "Saúde e Bem-estar")
        cat.delete()
        self.assertFalse(Categoria.objects.filter(pk=cat.pk).exists())


class EntradaModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="bob", password="x")

    def test_cria_entrada_valida(self) -> None:
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("5000.00"),
            usuario=self.user,
            fonte="Empresa X",
            recorrencia=True,
        )
        self.assertIsNotNone(entrada.data)
        self.assertEqual(entrada.usuario, self.user)
        # Multi-table inheritance: cria linha em Transacao também.
        self.assertTrue(Transacao.objects.filter(pk=entrada.pk).exists())

    def test_valor_zero_invalido(self) -> None:
        entrada = Entrada(
            nome="X",
            valor=Decimal("0"),
            usuario=self.user,
            recorrencia=False,
        )
        with self.assertRaises(ValidationError):
            entrada.full_clean()

    def test_valor_negativo_invalido_no_banco(self) -> None:
        with self.assertRaises(IntegrityError):
            Entrada.objects.create(
                nome="X",
                valor=Decimal("-1.00"),
                usuario=self.user,
                recorrencia=False,
            )

    def test_nome_vazio_invalido(self) -> None:
        entrada = Entrada(
            nome="",
            valor=Decimal("100"),
            usuario=self.user,
            recorrencia=False,
        )
        with self.assertRaises(ValidationError):
            entrada.full_clean()

    def test_edita_e_exclui(self) -> None:
        entrada = Entrada.objects.create(
            nome="Freela",
            valor=Decimal("800"),
            usuario=self.user,
            recorrencia=False,
        )
        entrada.valor = Decimal("900")
        entrada.save()
        entrada.refresh_from_db()
        self.assertEqual(entrada.valor, Decimal("900.00"))
        entrada.delete()
        self.assertFalse(Entrada.objects.filter(pk=entrada.pk).exists())


class SaidaModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="carol", password="x")
        self.categoria = Categoria.objects.create(
            nome="Mercado", descricao="Compras", cor="#112233", usuario=self.user
        )

    def test_cria_saida_valida(self) -> None:
        saida = Saida.objects.create(
            nome="Feira",
            valor=Decimal("120.50"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.assertEqual(saida.categoria, self.categoria)
        self.assertEqual(saida.pagamento, Pagamento.PIX)

    def test_pagamento_invalido(self) -> None:
        saida = Saida(
            nome="X",
            valor=Decimal("10"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento="BOLETO",
            tipo_gasto=TipoGasto.FIXO,
        )
        with self.assertRaises(ValidationError):
            saida.full_clean()

    def test_edita_e_exclui(self) -> None:
        saida = Saida.objects.create(
            nome="Conta de luz",
            valor=Decimal("200"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.DEBITO,
            tipo_gasto=TipoGasto.FIXO,
        )
        saida.valor = Decimal("210")
        saida.save()
        saida.refresh_from_db()
        self.assertEqual(saida.valor, Decimal("210.00"))
        saida.delete()
        self.assertFalse(Saida.objects.filter(pk=saida.pk).exists())


class ParcelamentoModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="dani", password="x")
        self.categoria = Categoria.objects.create(
            nome="Eletrônicos", descricao="Gadgets", cor="#445566", usuario=self.user
        )

    def test_cria_parcelamento_calcula_valor_parcela(self) -> None:
        parc = Parcelamento.objects.create(
            nome="Notebook",
            valor=Decimal("3000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=10,
        )
        self.assertEqual(parc.valor_parcela, Decimal("300.00"))
        self.assertEqual(parc.parcela_atual, 1)

    def test_valor_parcela_explicito_preservado(self) -> None:
        parc = Parcelamento.objects.create(
            nome="Geladeira",
            valor=Decimal("1000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=3,
            valor_parcela=Decimal("333.34"),
        )
        self.assertEqual(parc.valor_parcela, Decimal("333.34"))

    def test_parcela_atual_maior_que_total_invalido(self) -> None:
        parc = Parcelamento(
            nome="X",
            valor=Decimal("100"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=2,
            parcela_atual=5,
            valor_parcela=Decimal("50.00"),
        )
        with self.assertRaises(ValidationError):
            parc.full_clean()

    def test_edita_e_exclui(self) -> None:
        parc = Parcelamento.objects.create(
            nome="TV",
            valor=Decimal("2400"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=12,
        )
        parc.parcela_atual = 2
        parc.save()
        parc.refresh_from_db()
        self.assertEqual(parc.parcela_atual, 2)
        parc.delete()
        self.assertFalse(Parcelamento.objects.filter(pk=parc.pk).exists())
