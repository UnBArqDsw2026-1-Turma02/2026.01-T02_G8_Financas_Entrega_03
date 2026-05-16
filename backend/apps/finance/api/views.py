"""ViewSets da API de Finance."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.finance.api.serializers import (
    AjustarLimiteDiarioSerializer,
    AlertasResponseSerializer,
    CarteiraSerializer,
    CategoriaSerializer,
    DashboardCategoriasResponseSerializer,
    DashboardTendenciaResponseSerializer,
    DashboardVisaoGeralSerializer,
    EntradaSerializer,
    ExtraSerializer,
    ExtratoResponseSerializer,
    LimiteDiarioSerializer,
    ParcelamentoSerializer,
    ProgressoSerializer,
    ReservaSerializer,
    SaidaSerializer,
    SimulacaoGastoRequestSerializer,
    SimulacaoGastoResponseSerializer,
)
from apps.finance.models import Categoria, Entrada, Parcelamento, Saida
from apps.finance.services import (
    AlertaService,
    CarteiraService,
    DashboardService,
    ExtratoFinanceiroBuilder,
    FinancasTransacaoService,
    OrcamentoService,
    ProgressoService,
    SimulacaoGastoService,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Categoria.objects.filter(usuario=self.request.user).order_by("nome")

    def perform_create(self, serializer: CategoriaSerializer) -> None:
        try:
            serializer.save(usuario=self.request.user)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc


class EntradaViewSet(viewsets.ModelViewSet):
    serializer_class = EntradaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Entrada.objects.filter(usuario=self.request.user).order_by("-data")

    def perform_create(self, serializer: EntradaSerializer) -> None:
        service = FinancasTransacaoService()
        try:
            entrada = service.criar_transacao(
                tipo="entrada",
                usuario=self.request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        serializer.instance = entrada


class SaidaViewSet(viewsets.ModelViewSet):
    serializer_class = SaidaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Saida.objects.filter(usuario=self.request.user).order_by("-data")

    def perform_create(self, serializer: SaidaSerializer) -> None:
        service = FinancasTransacaoService()
        try:
            saida = service.criar_transacao(
                tipo="saida",
                usuario=self.request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        serializer.instance = saida


class ParcelamentoViewSet(viewsets.ModelViewSet):
    serializer_class = ParcelamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Parcelamento.objects.filter(usuario=self.request.user).order_by(
            "-data"
        )

    def perform_create(self, serializer: ParcelamentoSerializer) -> None:
        service = FinancasTransacaoService()
        try:
            parcelamento = service.criar_transacao(
                tipo="parcelamento",
                usuario=self.request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc
        serializer.instance = parcelamento

    def update(self, request, *args, **kwargs):
        parcelamento = self.get_object()
        if not parcelamento.pode_editar():
            raise serializers.ValidationError(
                {
                    "parcela_atual": (
                        "Edição permitida apenas enquanto estiver na 1ª parcela."
                    )
                }
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="antecipar")
    def antecipar(self, request, *args, **kwargs):
        parcelamento = self.get_object()
        try:
            parcelamento.antecipar_parcela()
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc
        serializer = self.get_serializer(parcelamento)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExtratoView(APIView):
    """Expõe o `ExtratoFinanceiroBuilder` (Issue #04) via REST.

    Cada query param presente aciona o método correspondente do Builder; ausência
    de filtros devolve o extrato completo do usuário autenticado.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        builder = ExtratoFinanceiroBuilder(usuario=request.user)
        try:
            self._aplicar_filtros(builder, request)
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc

        extrato = builder.build()
        return Response(
            ExtratoResponseSerializer(extrato).data, status=status.HTTP_200_OK
        )

    def _aplicar_filtros(self, builder: ExtratoFinanceiroBuilder, request) -> None:
        params = request.query_params

        if "tipo" in params:
            builder.filtro_tipo(params["tipo"])

        ano = params.get("ano")
        mes = params.get("mes")
        if ano is not None or mes is not None:
            if ano is None or mes is None:
                raise serializers.ValidationError(
                    {"ano_mes": "Informe 'ano' e 'mes' juntos."}
                )
            try:
                builder.filtro_ano_mes(int(ano), int(mes))
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(
                    {"ano_mes": "'ano' e 'mes' devem ser inteiros."}
                ) from exc

        if "categoria" in params:
            categoria = Categoria.objects.filter(
                pk=params["categoria"], usuario=request.user
            ).first()
            if categoria is None:
                raise serializers.ValidationError(
                    {"categoria": "Categoria não encontrada."}
                )
            builder.filtro_categoria(categoria)

        if "pagamento" in params:
            builder.filtro_pagamento(params["pagamento"].upper())

        if "tipo_gasto" in params:
            builder.filtro_tipo_gasto(params["tipo_gasto"].upper())

        if "nome" in params:
            builder.pesquisa_nome(params["nome"])


class SimulacaoGastoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request_serializer = SimulacaoGastoRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        service = SimulacaoGastoService()
        try:
            resultado = service.simular(
                usuario=request.user,
                **request_serializer.validated_data,
            )
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc

        response_serializer = SimulacaoGastoResponseSerializer(resultado)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class LimiteDiarioView(APIView):
    """GET retorna o limite diario do dia atual."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        limite = OrcamentoService().obter_limite_diario(request.user)
        return Response(
            LimiteDiarioSerializer(limite).data, status=status.HTTP_200_OK
        )


class AjustarLimiteDiarioView(APIView):
    """PUT permite ajustar o limite diario para um valor menor que o calculado."""

    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = AjustarLimiteDiarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            limite = OrcamentoService().ajustar_limite(
                request.user,
                serializer.validated_data["limite_ajustado"],
            )
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc
        return Response(
            LimiteDiarioSerializer(limite).data, status=status.HTTP_200_OK
        )


class ReservaView(APIView):
    """GET retorna o saldo da reserva do usuario."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reserva = OrcamentoService().obter_reserva(request.user)
        return Response(
            ReservaSerializer(reserva).data, status=status.HTTP_200_OK
        )


class ExtraView(APIView):
    """GET retorna o saldo do extra (somatorio do mes corrente)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from django.utils import timezone

        hoje = timezone.localdate()
        valor = OrcamentoService().obter_extra_mes(
            request.user, ano=hoje.year, mes=hoje.month
        )
        return Response(
            ExtraSerializer(
                {"valor": valor, "ano": hoje.year, "mes": hoje.month}
            ).data,
            status=status.HTTP_200_OK,
        )


class CarteiraView(APIView):
    """GET retorna o estado consolidado da carteira do usuario."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        estado = CarteiraService().obter_estado(request.user)
        return Response(
            CarteiraSerializer(estado).data, status=status.HTTP_200_OK
        )


class _DashboardViewMixin:
    """Resolve `ano`/`mes` da query string (default = mês atual)."""

    def _ano_mes(self, request) -> tuple[int | None, int | None]:
        params = request.query_params
        ano = params.get("ano")
        mes = params.get("mes")
        if ano is not None or mes is not None:
            if ano is None or mes is None:
                raise serializers.ValidationError(
                    {"ano_mes": "Informe 'ano' e 'mes' juntos."}
                )
            try:
                ano_int, mes_int = int(ano), int(mes)
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(
                    {"ano_mes": "'ano' e 'mes' devem ser inteiros."}
                ) from exc
            if not 1 <= mes_int <= 12:
                raise serializers.ValidationError(
                    {"mes": "'mes' deve estar entre 1 e 12."}
                )
            return ano_int, mes_int
        return None, None


class DashboardVisaoGeralView(_DashboardViewMixin, APIView):
    """GET `/api/v1/dashboard/` — totais consolidados do mês."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ano, mes = self._ano_mes(request)
        visao = DashboardService().obter_visao_geral(
            request.user, ano=ano, mes=mes
        )
        return Response(
            DashboardVisaoGeralSerializer(visao).data,
            status=status.HTTP_200_OK,
        )


class DashboardCategoriasView(_DashboardViewMixin, APIView):
    """GET `/api/v1/dashboard/categorias/` — gastos agrupados por categoria."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ano, mes = self._ano_mes(request)
        categorias = DashboardService().obter_gastos_por_categoria(
            request.user, ano=ano, mes=mes
        )
        payload = DashboardCategoriasResponseSerializer(
            {"categorias": categorias}
        ).data
        return Response(payload, status=status.HTTP_200_OK)


class DashboardTendenciaView(_DashboardViewMixin, APIView):
    """GET `/api/v1/dashboard/tendencia/` — gastos diários do mês."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ano, mes = self._ano_mes(request)
        dias = DashboardService().obter_tendencia_diaria(
            request.user, ano=ano, mes=mes
        )
        payload = DashboardTendenciaResponseSerializer({"dias": dias}).data
        return Response(payload, status=status.HTTP_200_OK)


class ProgressoView(APIView):
    """GET `/api/v1/progresso/` — streak atual e calendário do mês."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        progresso = ProgressoService().obter_progresso(request.user)
        payload = ProgressoSerializer(
            {
                "ano": progresso.ano,
                "mes": progresso.mes,
                "streak": progresso.streak,
                "calendario": [
                    {
                        "data": dia.data,
                        "dentro_limite": dia.dentro_limite,
                        "usou_reserva": dia.usou_reserva,
                        "usou_extra": dia.usou_extra,
                        "gasto": dia.gasto,
                        "limite": dia.limite,
                    }
                    for dia in progresso.calendario
                ],
            }
        ).data
        return Response(payload, status=status.HTTP_200_OK)


class AlertasView(APIView):
    """GET `/api/v1/alertas/` — alertas pendentes do dia."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        alertas = AlertaService().obter_alertas(request.user)
        payload = AlertasResponseSerializer(
            {
                "alertas": [
                    {"gatilho": a.gatilho, "mensagem": a.mensagem}
                    for a in alertas
                ]
            }
        ).data
        return Response(payload, status=status.HTTP_200_OK)
