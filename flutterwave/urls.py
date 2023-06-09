from django.urls import path
from . import views


urlpatterns = [
    path('redirect/', views.payment_redirect_view, name='fw_redirect'),
    path('activate/', views.activate_view, name='fw_activate'),
    path('buy-spins/', views.buy_spins_view, name='fw_buy_spins'),
    path('tasks-subscribe/', views.tasks_subscribe_view, name='fw_tasks_subscribe'),
    path('init-payment/', views.init_payment_view, name='fw_init_payment'),
]
