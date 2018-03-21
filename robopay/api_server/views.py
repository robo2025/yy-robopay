from rest_framework import viewsets, status, renderers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route
import logging

from . import utils
from .models import Payment
from .serializers import PaymentSerializer, UnionPaySerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = "order_id"

    def list(self, request, *args, **kwargs):
        serializer = PaymentSerializer(self.queryset, many=True)
        return Response({
            'status': 'ok',
            'data': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'ok',
                'data': serializer.data
            })

        return Response({
            'status': 'error',
            'error': '提交数据异常',
        }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id', '')
        if not utils.check_order_id(order_id):
            return Response({
                'status': 'error',
                'error': '支付订单未找到',
            }, status=status.HTTP_404_NOT_FOUND)

        payment = self.get_object()
        serializer = PaymentSerializer(payment)
        return Response({
            'status': 'ok',
            'error': None,
            'data': serializer.data
        })

    @detail_route()
    def form(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id', '')
        if not utils.check_order_id(order_id):
            return Response({
                'status': 'error',
                'error': '支付订单未找到',
            }, status=status.HTTP_404_NOT_FOUND)

        req_params, req_url = utils.get_payment_form(order_id)
        req_data = {
            'req_params': req_params,
            'req_url': req_url,
        }

        return Response({
            'status': 'ok',
            'data': req_data
        })

    @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    def html(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id', '')
        if not utils.check_order_id(order_id):
            html_str = "<h1>支付订单未找到</h1>"
            return Response(html_str)

        html_str = utils.get_payment_form_html(order_id)
        return Response(html_str)


class UnionPayFrontView(APIView):
    def post(self, request):
        parse_data = utils.parse_response_data(request.data)
        logging.info("接收银联前台数据: {}".format(parse_data))

        if not utils.validate_unionpay_data(parse_data):
            logging.error("银联返回数据验证错误!")
            return Response({
                'status': 'error',
                'error': '银联返回数据格式验证错误',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'ok',
            'data': parse_data,
        })


class UnionPayBackView(APIView):
    def post(self, request):
        parse_data = utils.parse_response_data(request.data)
        logging.info("接收银联后台数据: {}".format(parse_data))

        if not utils.validate_unionpay_data(parse_data):
            logging.error("银联返回数据验证错误!")
            return Response({
                'status': 'error',
                'error': '银联返回数据验证错误',
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UnionPaySerializer(data=parse_data)
        if serializer.is_valid():
            respCode = serializer.validated_data['respCode']
            if respCode == "00":
                logging.info("银联后台数据有效, resp: {}".format(respCode))
                serializer.save()
            elif respCode == "03" or respCode == "04" or respCode == "05":
                logging.warning("银联后台数据正在处理中, resp: {}".format(respCode))
            else:
                logging.error("银联后台数据返回失效值, resp: {}".format(respCode))
            return Response({
                'status': 'ok',
            })

        logging.error("银联返回数据格式错误!")
        return Response({
            'status': 'error',
        }, status=status.HTTP_400_BAD_REQUEST)
