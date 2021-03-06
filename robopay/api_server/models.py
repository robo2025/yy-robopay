from django.db import models

ORDER_CHOICE = (
    ('n', '未付款'),
    ('p', '已付款'),
    ('u', '付款撤销'),
    ('r', '已退款'),
    ('t', '付款超时'),
    ('e', '付款错误'),
)

REFUND_CHOICE = (
    ('p', '退款中'),
    ('s', '退款成功'),
    ('e', '退款失败'),
)


class Payment(models.Model):
    payment_id = models.CharField(max_length=30, unique=True, db_index=True)
    order_id = models.CharField(max_length=30, unique=True, db_index=True)
    unionpay_id = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    payment_amount = models.BigIntegerField()
    payment_status = models.CharField(choices=ORDER_CHOICE, default='n', max_length=5)
    payment_time = models.CharField(max_length=30, blank=True, null=True)
    created_time = models.BigIntegerField()

    def __str__(self):
        return self.payment_id

    class Meta:
        db_table = 'payment'


class UnionPay(models.Model):
    order_id = models.CharField(max_length=30, unique=True, db_index=True)
    unionpay_id = models.CharField(max_length=30, unique=True, db_index=True)
    unionpay_card = models.CharField(max_length=30)
    merchant_id = models.CharField(max_length=30)
    unionpay_count = models.BigIntegerField()
    unionpay_time = models.CharField(max_length=100)

    def __str__(self):
        return self.order_id

    class Meta:
        db_table = 'unionpay'


class Refund(models.Model):
    refund_id = models.CharField(max_length=30, unique=True, db_index=True)
    order_id = models.CharField(max_length=30, db_index=True)
    unionpay_payment_id = models.CharField(max_length=30, db_index=True)
    unionpay_refund_id = models.CharField(max_length=30, blank=True, null=True)
    refund_amount = models.BigIntegerField()
    refund_status = models.CharField(choices=REFUND_CHOICE, default='p', max_length=5)
    refund_time = models.CharField(max_length=30, blank=True, null=True)
    created_time = models.BigIntegerField()

    def __str__(self):
        return self.refund_id

    class Meta:
        db_table = 'refund'


class UnionPayRefund(models.Model):
    refund_id = models.CharField(max_length=30, unique=True, db_index=True)
    unionpay_refund_id = models.CharField(max_length=30, unique=True, db_index=True)
    unionpay_payment_id = models.CharField(max_length=30, db_index=True)
    unionpay_payment_card = models.CharField(max_length=30)
    merchant_id = models.CharField(max_length=30)
    refund_count = models.BigIntegerField()
    refund_time = models.CharField(max_length=100)

    def __str__(self):
        return self.refund_id

    class Meta:
        db_table = 'unionpay_refund'
