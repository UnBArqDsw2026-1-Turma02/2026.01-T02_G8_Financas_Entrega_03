"""Testes das Tools de IA (Issue #17).

Cada tool é exercitada através do `ToolRegistry`, garantindo que:
- o registro contém os 14 nomes esperados;
- os schemas seguem o formato `chat.completions.tools` da OpenAI;
- as tools delegam para os services corretos e devolvem dicionários
  serializáveis para o LLM.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finance.models import (
    Categoria,
    Entrada,
    Pagamento,
    Parcelamento,
    Saida,
    TipoGasto,
)
from apps.provider_llm.domain import ToolCall
from apps.provider_llm.tools import ToolRegistry, TOOL_SCHEMAS

User = get_user_model()


def _call(_nome: str, **args) -> ToolCall:
    return ToolCall(id=f"call_{_nome}", nome=_nome, argumentos=args)


class ToolSchemasTests(TestCase):
    def test_quatorze_tools_registradas(self) -> None:
        nomes = {s["function"]["name"] for s in TOOL_SCHEMAS}
        self.assertEqual(len(TOOL_SCHEMAS), 14)
        esperados = {
            "criar_entrada",
            "criar_saida",
            "criar_parcelamento",
            "editar_entrada",
            "editar_saida",
            "editar_parcelamento",
            "excluir_entrada",
            "excluir_saida",
            "excluir_parcelamento",
            "simular_gasto",
            "listar_extrato",
            "listar_entradas",
            "listar_saidas",
            "listar_parcelamentos",
        }
        self.assertEqual(nomes, esperados)

    def test_schemas_formato_openai(self) -> None:
        for schema in TOOL_SCHEMAS:
            self.assertEqual(schema["type"], "function")
            self.assertIn("name", schema["function"])
            self.assertIn("description", schema["function"])
            parametros = schema["function"]["parameters"]
            self.assertEqual(parametros["type"], "object")
            self.assertIn("properties", parametros)
            self.assertIn("required", parametros)


class ToolRegistryDispatchTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="ana", password="x")
        self.categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        self.registry = ToolRegistry(self.user)

    def test_schemas_filtra_pelas_tools_disponiveis(self) -> None:
        self.assertEqual(len(self.registry.schemas()), 14)
        custom = ToolRegistry(
            self.user, tools={"criar_entrada": __import__("apps.provider_llm.tools.functions", fromlist=["criar_entrada"]).criar_entrada}
        )
        nomes = [s["function"]["name"] for s in custom.schemas()]
        self.assertEqual(nomes, ["criar_entrada"])

    def test_executar_tool_inexistente_devolve_erro(self) -> None:
        resultado = self.registry.executar(_call("nao_existe"))
        self.assertFalse(resultado["ok"])
        self.assertIn("desconhecida", resultado["erro"])

    def test_excecao_de_service_vira_erro_textual(self) -> None:
        resultado = self.registry.executar(
            _call("criar_entrada", nome="", valor=0)
        )
        self.assertFalse(resultado["ok"])
        self.assertIn("erro", resultado)


class ToolsCriacaoTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="bob", password="x")
        self.categoria = Categoria.objects.create(
            nome="Aluguel",
            descricao="Moradia",
            cor="#abcdef",
            usuario=self.user,
        )
        self.registry = ToolRegistry(self.user)

    def test_criar_entrada(self) -> None:
        resultado = self.registry.executar(
            _call(
                "criar_entrada",
                nome="Salário",
                valor=3000,
                fonte="Trabalho",
                recorrencia=True,
            )
        )
        self.assertTrue(resultado["ok"])
        self.assertEqual(Entrada.objects.filter(usuario=self.user).count(), 1)
        entrada = Entrada.objects.get()
        self.assertEqual(entrada.fonte, "Trabalho")
        self.assertTrue(entrada.recorrencia)

    def test_criar_saida_por_categoria_id(self) -> None:
        resultado = self.registry.executar(
            _call(
                "criar_saida",
                nome="Aluguel",
                valor=1500,
                categoria_id=str(self.categoria.id),
                pagamento=Pagamento.PIX.value,
                tipo_gasto=TipoGasto.FIXO.value,
            )
        )
        self.assertTrue(resultado["ok"])
        saida = Saida.objects.get()
        self.assertEqual(saida.categoria, self.categoria)
        self.assertEqual(saida.pagamento, Pagamento.PIX.value)

    def test_criar_saida_por_categoria_nome(self) -> None:
        resultado = self.registry.executar(
            _call(
                "criar_saida",
                nome="Mercado",
                valor=200,
                categoria_nome="aluguel",  # case insensitive
                pagamento=Pagamento.DEBITO.value,
                tipo_gasto=TipoGasto.VARIAVEL.value,
            )
        )
        self.assertTrue(resultado["ok"])
        self.assertEqual(Saida.objects.get().categoria, self.categoria)

    def test_criar_saida_sem_categoria_falha(self) -> None:
        resultado = self.registry.executar(
            _call(
                "criar_saida",
                nome="X",
                valor=10,
                pagamento=Pagamento.PIX.value,
                tipo_gasto=TipoGasto.VARIAVEL.value,
            )
        )
        self.assertFalse(resultado["ok"])

    def test_criar_parcelamento_calcula_valor_parcela(self) -> None:
        resultado = self.registry.executar(
            _call(
                "criar_parcelamento",
                nome="Geladeira",
                valor=1200,
                num_parcelas=4,
                categoria_id=str(self.categoria.id),
                pagamento=Pagamento.CREDITO.value,
            )
        )
        self.assertTrue(resultado["ok"])
        parcelamento = Parcelamento.objects.get()
        self.assertEqual(parcelamento.valor_parcela, Decimal("300.00"))


class ToolsEdicaoExclusaoTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="cleo", password="x")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Diversão",
            cor="#ff0000",
            usuario=self.user,
        )
        self.entrada = Entrada.objects.create(
            usuario=self.user, nome="Bolsa", valor=Decimal("1000")
        )
        self.saida = Saida.objects.create(
            usuario=self.user,
            nome="Cinema",
            valor=Decimal("50"),
            categoria=self.categoria,
            pagamento=Pagamento.PIX.value,
            tipo_gasto=TipoGasto.VARIAVEL.value,
        )
        self.parcelamento = Parcelamento.objects.create(
            usuario=self.user,
            nome="Notebook",
            valor=Decimal("2000"),
            num_parcelas=4,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO.value,
        )
        self.registry = ToolRegistry(self.user)

    def test_editar_entrada(self) -> None:
        resultado = self.registry.executar(
            _call(
                "editar_entrada",
                id=str(self.entrada.id),
                nome="Mesada",
                valor=1200,
            )
        )
        self.assertTrue(resultado["ok"])
        self.entrada.refresh_from_db()
        self.assertEqual(self.entrada.nome, "Mesada")
        self.assertEqual(self.entrada.valor, Decimal("1200"))

    def test_editar_saida(self) -> None:
        nova = Categoria.objects.create(
            nome="Saúde", descricao="Médico", cor="#00ff00", usuario=self.user
        )
        resultado = self.registry.executar(
            _call(
                "editar_saida",
                id=str(self.saida.id),
                valor=80,
                categoria_id=str(nova.id),
            )
        )
        self.assertTrue(resultado["ok"])
        self.saida.refresh_from_db()
        self.assertEqual(self.saida.valor, Decimal("80"))
        self.assertEqual(self.saida.categoria, nova)

    def test_editar_parcelamento_primeira_parcela(self) -> None:
        resultado = self.registry.executar(
            _call(
                "editar_parcelamento",
                id=str(self.parcelamento.id),
                nome="Notebook Dell",
            )
        )
        self.assertTrue(resultado["ok"])
        self.parcelamento.refresh_from_db()
        self.assertEqual(self.parcelamento.nome, "Notebook Dell")

    def test_editar_parcelamento_bloqueia_apos_primeira_parcela(self) -> None:
        self.parcelamento.parcela_atual = 2
        self.parcelamento.save()
        resultado = self.registry.executar(
            _call(
                "editar_parcelamento",
                id=str(self.parcelamento.id),
                nome="Tentativa proibida",
            )
        )
        self.assertFalse(resultado["ok"])

    def test_excluir_entrada(self) -> None:
        resultado = self.registry.executar(
            _call("excluir_entrada", id=str(self.entrada.id))
        )
        self.assertTrue(resultado["ok"])
        self.assertFalse(Entrada.objects.filter(pk=self.entrada.id).exists())

    def test_excluir_saida(self) -> None:
        resultado = self.registry.executar(
            _call("excluir_saida", id=str(self.saida.id))
        )
        self.assertTrue(resultado["ok"])
        self.assertFalse(Saida.objects.filter(pk=self.saida.id).exists())

    def test_excluir_parcelamento(self) -> None:
        resultado = self.registry.executar(
            _call("excluir_parcelamento", id=str(self.parcelamento.id))
        )
        self.assertTrue(resultado["ok"])
        self.assertFalse(
            Parcelamento.objects.filter(pk=self.parcelamento.id).exists()
        )


class ToolsListagemSimulacaoTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="dora", password="x")
        self.outro = User.objects.create_user(username="ed", password="x")
        self.categoria = Categoria.objects.create(
            nome="Mercado", descricao="Comida", cor="#abcdef", usuario=self.user
        )
        Entrada.objects.create(
            usuario=self.user, nome="Salário", valor=Decimal("5000")
        )
        Entrada.objects.create(
            usuario=self.outro, nome="Outro", valor=Decimal("9999")
        )
        Saida.objects.create(
            usuario=self.user,
            nome="Feira",
            valor=Decimal("100"),
            categoria=self.categoria,
            pagamento=Pagamento.PIX.value,
            tipo_gasto=TipoGasto.VARIAVEL.value,
        )
        Parcelamento.objects.create(
            usuario=self.user,
            nome="TV",
            valor=Decimal("1200"),
            num_parcelas=3,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO.value,
        )
        self.registry = ToolRegistry(self.user)

    def test_listar_entradas_isola_usuario(self) -> None:
        resultado = self.registry.executar(_call("listar_entradas"))
        self.assertEqual(len(resultado["entradas"]), 1)
        self.assertEqual(resultado["entradas"][0]["nome"], "Salário")

    def test_listar_saidas(self) -> None:
        resultado = self.registry.executar(_call("listar_saidas"))
        self.assertEqual(len(resultado["saidas"]), 1)

    def test_listar_parcelamentos(self) -> None:
        resultado = self.registry.executar(_call("listar_parcelamentos"))
        self.assertEqual(len(resultado["parcelamentos"]), 1)
        self.assertEqual(resultado["parcelamentos"][0]["valor_parcela"], "400.00")

    def test_listar_extrato_filtra_por_tipo(self) -> None:
        resultado = self.registry.executar(
            _call("listar_extrato", tipo="saida")
        )
        tipos = {t["tipo"] for t in resultado["transacoes"]}
        self.assertEqual(tipos, {"saida"})

    def test_listar_extrato_pesquisa_nome(self) -> None:
        resultado = self.registry.executar(
            _call("listar_extrato", pesquisa_nome="Salário")
        )
        self.assertEqual(len(resultado["transacoes"]), 1)
        self.assertEqual(resultado["transacoes"][0]["nome"], "Salário")

    def test_simular_gasto_avista(self) -> None:
        resultado = self.registry.executar(
            _call("simular_gasto", valor=200)
        )
        self.assertIn("orcamento_mensal_atual", resultado)
        self.assertIn("novo_orcamento", resultado)
        self.assertIn("impacta_30_porcento", resultado)

    def test_simular_gasto_parcelado(self) -> None:
        resultado = self.registry.executar(
            _call(
                "simular_gasto", valor=600, parcelado=True, num_parcelas=3
            )
        )
        self.assertIn("simulacao_parcelamento", resultado)
        self.assertEqual(
            resultado["simulacao_parcelamento"]["valor_parcela"],
            Decimal("200.00"),
        )
