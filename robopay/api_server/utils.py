import logging
from time import time
from datetime import datetime, timedelta
from unionpay.SDKConfig import SDKConfig
from unionpay.AcpService import AcpService
from .models import Payment, UnionPay, Refund


def get_payment_info(order_id):
    try:
        payment = Payment.objects.get(order_id=order_id)
        return payment
    except Payment.DoesNotExist:
        return None


def get_unionpay_info(order_id):
    try:
        unionpay = UnionPay.objects.get(order_id=order_id)
        return unionpay
    except UnionPay.DoesNotExist:
        return None


def generate_payments_id(order_id):
    payment_id = order_id.replace('DD', '')
    return 'ZF' + payment_id


def generate_refund_id(order_id):
    payment_id = order_id.replace('DD', '')
    return 'TK' + payment_id + datetime.now().strftime("%M%S")


def get_payment_amount(order_id):
    return 1000


def get_payment_merchant_id():
    return "777290058110048"


def get_payment_form(order_id):
    time_now = datetime.now().strftime('%Y%m%d%H%M%S')
    time_out = datetime.now() + timedelta(minutes=15)
    time_out = time_out.strftime('%Y%m%d%H%M%S')

    req = {}
    req["version"] = SDKConfig().version
    req["encoding"] = SDKConfig().encoding
    req["txnType"] = "01"
    req["txnSubType"] = "01"
    req["bizType"] = "000202"
    req["frontUrl"] = SDKConfig().frontUrl
    req["backUrl"] = SDKConfig().backUrl
    req["signMethod"] = SDKConfig().signMethod
    req["channelType"] = "07"
    req["accessType"] = "0"
    req["currencyCode"] = "156"

    req["merId"] = get_payment_merchant_id()
    req["orderId"] = order_id
    req["txnAmt"] = str(get_payment_amount(order_id))
    req["txnTime"] = time_now
    req['payTimeout'] = time_out

    # 签名示例
    req_params = AcpService.sign(req)
    req_url = SDKConfig().frontTransUrl

    return req_params, req_url


def get_payment_form_html(order_id):
    req_params, req_url = get_payment_form(order_id)
    return AcpService.createAutoFormHtml(req_params, req_url)


def validate_unionpay_data(data_dict):
    return AcpService.validate(data_dict)


def parse_response_data(data_dict):
    parse_dict = {}
    for el in data_dict:
        parse_dict[el] = data_dict[el]
    return parse_dict


def get_query_form(order_id):
    payment = get_payment_info(order_id)
    if not payment:
        return None, None

    txnTime = payment.payment_time or datetime.fromtimestamp(payment.created_time).strftime('%Y%m%d%H%M%S')

    req = {}
    req["version"] = SDKConfig().version
    req["encoding"] = SDKConfig().encoding
    req["signMethod"] = SDKConfig().signMethod
    req["txnType"] = "00"
    req["txnSubType"] = "00"
    req["bizType"] = "000000"
    req["accessType"] = "0"
    req["channelType"] = "07"

    req["merId"] = get_payment_merchant_id()
    req["orderId"] = order_id
    req["txnTime"] = txnTime

    # 签名示例
    req_params = AcpService.sign(req)
    req_url = SDKConfig().singleQueryUrl

    return req_params, req_url


def process_unionpay_query(order_id):
    req_params, req_url = get_query_form(order_id)

    if not req_params:
        error_msg = "找不到订单 {} 的信息".format(order_id)
        logging.error(error_msg)
        return False, error_msg

    resp_data = AcpService.post(req_params, req_url)
    logging.info(resp_data)
    if not validate_unionpay_data(resp_data):
        error_msg = "银联返回数据验证错误!"
        logging.error(error_msg)
        return False, error_msg

    return True, resp_data


def check_unionpay_payment_status(data):
    respCode = data['respCode']
    origRespCode = data['origRespCode']

    if respCode == "00":
        if origRespCode == "00":
            payment_status = "交易成功"
        elif origRespCode == "03" \
                or origRespCode == "04" \
                or origRespCode == "05":
            payment_status = "交易处理中，请稍微查询。"
        else:
            payment_status = "交易失败"

        return payment_status

    if respCode == "03" \
            or respCode == "04" \
            or respCode == "05":
        payment_status = "处理超时，请稍微查询"
        return payment_status

    payment_status = "请求失败"
    return payment_status


def check_refund_amount(unionpay, amount):
    return unionpay.unionpay_count >= amount


def get_refund_form(unionpay, refund_id, refund_amount):
    time_now = datetime.now().strftime('%Y%m%d%H%M%S')

    req = {}
    req["version"] = SDKConfig().version
    req["encoding"] = SDKConfig().encoding
    req["signMethod"] = SDKConfig().signMethod
    req["txnType"] = "04"
    req["txnSubType"] = "00"
    req["bizType"] = "000201"
    req["accessType"] = "0"
    req["channelType"] = "07"
    req["backUrl"] = SDKConfig().backUrl

    req["merId"] = get_payment_merchant_id()
    req["orderId"] = refund_id
    req['origQryId'] = unionpay.unionpay_id
    req["txnTime"] = time_now
    req["txnAmt"] = str(refund_amount)

    # 签名示例
    req_params = AcpService.sign(req)
    req_url = SDKConfig().backTransUrl

    return req_params, req_url


def process_refund(order_id, amount):
    unionpay = get_unionpay_info(order_id)
    if not unionpay:
        error_msg = "找不到已付款订单: {}".format(order_id)
        logging.error(error_msg)
        return False, error_msg

    if not check_refund_amount(unionpay, amount):
        error_msg = "退款金额大于支付金额!"
        logging.error(error_msg)
        return False, error_msg

    logging.debug("存储退款数据到数据库")

    refund_id = generate_refund_id(unionpay.order_id)
    refund = Refund(
        refund_id=refund_id,
        order_id=unionpay.order_id,
        unionpay_payment_id=unionpay.unionpay_id,
        refund_amount=amount,
        created_time=int(time()),
    )
    refund.save()

    req_params, req_url = get_refund_form(unionpay, refund_id, amount)
    resp_data = AcpService.post(req_params, req_url)

    if not AcpService.validate(resp_data):
        error_msg = "退款回复报文验证失败"
        logging.error(error_msg)
        return False, error_msg

    logging.info(resp_data)
    respCode = resp_data['respCode']

    if respCode == "00":
        logging.info("退款受理成功!")
        return True, resp_data

    if respCode == "03" or respCode == "04" or respCode == "05":
        error_msg = "退款受理超时"
        logging.warning(error_msg)
        return False, error_msg

    error_msg = "退款受理失败"
    logging.error(error_msg)

    refund.refund_status = 'e'
    refund.save()

    return False, error_msg
