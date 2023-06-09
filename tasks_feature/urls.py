from django.urls import path
from . import views


urlpatterns = [
    path('', views.index_view, name='user_tasks'),
    path('subscribe/', views.SubscribeView.as_view(), name='tasks_subscribe'),
    path('subscribe-start/', views.subscribe_start, name='tasks_subscribe_start'),
    path('wallet-transfer/', views.wallet_transfer_view, name='tasks_wallet_transfer'),
    path('<int:pk>/take/', views.TakeTaskView.as_view(), name='take_task'),
]
