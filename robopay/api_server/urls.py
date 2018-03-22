from django.urls import path, include
from .views import PaymentViewSet, RefundViewSet
from .views import UnionPayFrontView, UnionPayBackView, UnionPayQueryView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('payment', PaymentViewSet)
router.register('refund', RefundViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('unionpay/front/', UnionPayFrontView.as_view(), name='unionpay-front'),
    path('unionpay/back/', UnionPayBackView.as_view(), name='unionpay-front'),
    path('unionpay/query/<order_id>/', UnionPayQueryView.as_view(), name='unionpay-query'),
]
