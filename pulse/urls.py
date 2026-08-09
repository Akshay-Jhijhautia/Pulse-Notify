from django.urls import path

from .views import (
    LoginView,
    PriceAlertDeactivateView,
    PriceAlertListCreateView,
    RegisterView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('alerts/', PriceAlertListCreateView.as_view(), name='alert-list-create'),
    path(
        'alerts/<int:id>/',
        PriceAlertDeactivateView.as_view(),
        name='alert-deactivate',
    ),
]
