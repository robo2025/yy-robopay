import logging
from datetime import datetime, timedelta
from unionpay.SDKConfig import SDKConfig
from unionpay.AcpService import AcpService
from .models import Payment


def get_payment_info(order_id):
    try:
        payment = Payment.objects.get(order_id=order_id)
        return payment
    except Payment.DoesNotExist:
        return None


def generate_payments_id(order_id):
    payment_id = order_id.replace('DD', '')
    return 'ZF' + payment_id


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

    res_data = AcpService.post(req_params, req_url)
    logging.info(res_data)
    if not validate_unionpay_data(res_data):
        error_msg = "银联返回数据验证错误!"
        logging.error(error_msg)
        return False, error_msg

    return True, res_data


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
