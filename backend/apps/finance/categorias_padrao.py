"""Categorias pré-cadastradas atribuídas a todo usuário.

Consumido por:
- ``RegisterSerializer`` (seed no cadastro de novos usuários).
- Data migration ``0005_seed_categorias_padrao`` (backfill dos já existentes).
"""

from __future__ import annotations

from typing import Iterable

CATEGORIAS_PADRAO: list[dict[str, str]] = [
    {
        "nome": "Alimentação",
        "descricao": "Mercado, restaurantes, delivery e refeições em geral",
        "cor": "#FF6B6B",
    },
    {
        "nome": "Transporte",
        "descricao": "Combustível, transporte público e aplicativos de mobilidade",
        "cor": "#4ECDC4",
    },
    {
        "nome": "Moradia",
        "descricao": "Aluguel, condomínio, IPTU e manutenção da casa",
        "cor": "#95A5A6",
    },
    {
        "nome": "Lazer",
        "descricao": "Cinema, viagens, hobbies e assinaturas de entretenimento",
        "cor": "#F39C12",
    },
    {
        "nome": "Saúde",
        "descricao": "Plano de saúde, farmácia, consultas e exames",
        "cor": "#2ECC71",
    },
    {
        "nome": "Educação",
        "descricao": "Cursos, livros e mensalidades escolares",
        "cor": "#3498DB",
    },
    {
        "nome": "Contas",
        "descricao": "Energia, água, internet e telefone",
        "cor": "#9B59B6",
    },
    {
        "nome": "Outros",
        "descricao": "Gastos diversos sem categoria específica",
        "cor": "#7F8C8D",
    },
]


def seed_categorias_padrao(usuario, *, model=None) -> None:
    """Cria as categorias padrão para ``usuario`` de forma idempotente.

    Idempotente por ``(usuario, nome)``: rodar várias vezes não duplica linhas
    e preserva categorias que o usuário já tenha personalizado.

    ``model`` permite injetar o ``Categoria`` histórico em data migrations
    (``apps.get_model("finance", "Categoria")``); quando omitido, usa o modelo
    em tempo de execução.
    """
    if model is None:
        from apps.finance.models import Categoria as model  # noqa: N806

    for cat in CATEGORIAS_PADRAO:
        model.objects.get_or_create(
            usuario=usuario,
            nome=cat["nome"],
            defaults={"descricao": cat["descricao"], "cor": cat["cor"]},
        )


__all__: Iterable[str] = ("CATEGORIAS_PADRAO", "seed_categorias_padrao")
