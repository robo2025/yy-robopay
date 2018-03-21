from django.urls import path, include
from .views import PaymentViewSet
from .views import UnionPayFrontView, UnionPayBackView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('payment', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('unionpay/front/', UnionPayFrontView.as_view(), name='unionpay-front'),
    path('unionpay/back/', UnionPayBackView.as_view(), name='unionpay-front'),
]
