from time import time
from datetime import datetime, timedelta
from unionpay.SDKConfig import SDKConfig
from unionpay.AcpService import AcpService
from .models import Payment
from copy import deepcopy


def check_order_id(order_id):
    try:
        Payment.objects.get(order_id=order_id)
        return True
    except Payment.DoesNotExist:
        return False


def get_payments_id(order_id):
    payment_id = order_id.replace('DD', '')
    return 'ZF' + payment_id


def get_payment_amount(order_id):
    return 1000


def get_payment_merchant_id():
    return "777290058110048"


def get_payment_time():
    return int(time())


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
