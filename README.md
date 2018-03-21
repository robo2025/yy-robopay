# Robo2025 支付

## 运行

1. 做内外穿透，需要在本机运行 frpc, frpc 的配置文件如下

```ini
[common]
server_addr = 123.206.92.160
server_port = 7002

[web]
type = http
local_port = 8000
custom_domains = unionpaytest.robo2025.com
```

2. 迁移数据库 

```bash
python manage.py makemigrations api_server
python manage.py migrate
```

3. 运行并测试程序

```bash
python manage.py runserver 0.0.0.0:8000
``` 

## URL

1. [payment/](http://127.0.0.1:8000/payment/): 创建订单

2. [payment/xxxx/form/](http://127.0.0.1:8000/payment/DD123456/form/): 银联订单 JSON 版本

3. [payment/xxxx/html/](http://127.0.0.1:8000/payment/DD123456/html/): 银联订单 HTML 版本

4. [unionpay/front/](http://127.0.0.1:8000/unionpay/front/): 银联订单前台返回

5. [unionpay/back/](http://http://unionpaytest.robo2025.com:8000/unionpay/back/): 银联订单后台返回, 需要 FRP 做内外穿透