from rest_framework import serializers
from django.db import transaction
from .models import Payment, UnionPay
from . import utils


class PaymentSerializer(serializers.ModelSerializer):
    """
    支付订单的序列化
    """

    class Meta:
        model = Payment
        fields = ('payment_id', 'order_id', 'unionpay_id', 'payment_amount', 'payment_status', 'payment_time')
        read_only_fields = ('payment_id', 'unionpay_id', 'payment_amount', 'payment_status', 'payment_time')

    def create(self, validated_data):
        order_id = validated_data['order_id']
        payment_id = utils.get_payments_id(order_id)
        payment_amount = utils.get_payment_amount(order_id)
        payment_time = utils.get_payment_time()
        payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            payment_amount=payment_amount,
            payment_time=payment_time,
        )
        payment.save()
        return payment


class UnionPaySerializer(serializers.Serializer):
    """
    银联订单返回
    """

    accNo = serializers.CharField()
    accessType = serializers.CharField()
    bizType = serializers.CharField()
    currencyCode = serializers.CharField()
    encoding = serializers.CharField()
    merId = serializers.CharField()
    orderId = serializers.CharField()
    payCardType = serializers.CharField()
    payType = serializers.CharField()
    queryId = serializers.CharField()
    respCode = serializers.CharField()
    respMsg = serializers.CharField()
    settleAmt = serializers.CharField()
    settleCurrencyCode = serializers.CharField()
    settleDate = serializers.CharField()
    signMethod = serializers.CharField()
    signPubKeyCert = serializers.CharField()
    traceNo = serializers.CharField()
    traceTime = serializers.CharField()
    txnAmt = serializers.CharField()
    txnSubType = serializers.CharField()
    txnTime = serializers.CharField()
    txnType = serializers.CharField()
    version = serializers.CharField()

    def create(self, validated_data):
        order_id = validated_data.get('orderId')
        unionpay_id = validated_data.get('queryId')
        unionpay_card = validated_data.get('accNo')
        merchant_id = validated_data.get('merId')
        unionpay_count = int(validated_data.get('settleAmt'))
        unionpay_time = validated_data.get('txnTime')

        unionpay = UnionPay(
            order_id=order_id,
            unionpay_id=unionpay_id,
            unionpay_card=unionpay_card,
            merchant_id=merchant_id,
            unionpay_count=unionpay_count,
            unionpay_time=unionpay_time,
        )

        try:
            payment = Payment.objects.get(order_id=order_id)
        except Payment.DoesNotExist:
            return unionpay

        payment.unionpay_id = unionpay_id
        payment.payment_status = 'p'

        with transaction.atomic():
            unionpay.save()
            payment.save()

        return unionpay
