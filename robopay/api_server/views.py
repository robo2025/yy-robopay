from rest_framework import viewsets, status, renderers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route
import logging

from . import utils
from .models import Payment, Refund
from .serializers import PaymentSerializer, UnionPaySerializer, RefundSerializer, UnionPayRefundSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = "order_id"

    def list(self, request, *args, **kwargs):
        queryset = Payment.objects.all()
        serializer = PaymentSerializer(queryset, many=True)
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
        payment = utils.get_payment_info(order_id)
        if not payment:
            return Response({
                'status': 'error',
                'error': '支付订单未找到',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment)
        return Response({
            'status': 'ok',
            'error': None,
            'data': serializer.data
        })

    @detail_route()
    def form(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id', '')
        payment = utils.get_payment_info(order_id)
        if not payment:
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
        payment = utils.get_payment_info(order_id)
        if not payment:
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

        if parse_data['txnType'] == '01':
            serializer = UnionPaySerializer(data=parse_data)
        elif parse_data['txnType'] == '04':
            serializer = UnionPayRefundSerializer(data=parse_data)
        else:
            return Response({
                'status': 'error',
                'error': '暂未支持的处理类型: '.format(parse_data['txnType']),
            }, status=status.HTTP_400_BAD_REQUEST)

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


class UnionPayQueryView(APIView):
    def get(self, request, order_id):
        status, data = utils.process_unionpay_query(order_id)
        if not status:
            return Response({
                'status': 'error',
                'error': data,
            })

        payment_status = utils.check_unionpay_payment_status(data)
        return Response({
            'status': 'ok',
            'data': payment_status,
        })


class RefundViewSet(viewsets.GenericViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer

    def list(self, request, *args, **kwargs):
        queryset = Refund.objects.all()
        serializer = RefundSerializer(queryset, many=True)
        return Response({
            'status': 'ok',
            'data': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = RefundSerializer(data=request.data)
        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            refund_amount = serializer.validated_data['refund_amount']
            resp_status, resp_data = utils.process_refund(order_id, refund_amount)
            if resp_status:
                return Response({
                    'status': 'ok',
                    'data': resp_data
                })
            else:
                return Response({
                    'status': 'error',
                    'error': resp_data,
                })

        return Response({
            'status': 'error',
            'error': '提交数据异常',
        }, status=status.HTTP_400_BAD_REQUEST)
