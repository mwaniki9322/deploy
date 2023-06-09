from django.urls import path
from . import views


urlpatterns = [
    path('confirmation/<str:mpesa_secret>/', views.confirmation_view, name='mpesa_confirmation'),
    path('validation/<str:mpesa_secret>/', views.validation, name='mpesa_validation'),
    path('callback/<str:mpesa_secret>/', views.callback_view, name='mpesa_callback'),
    path('b2c-result/<str:mpesa_secret>/<str:withdrawal_pk>/', views.b2c_result_view,
         name='mpesa_b2c_result'),
    path('b2c-queue-time-out/<str:mpesa_secret>/<str:withdrawal_pk>/', views.b2c_queue_time_out_view,
         name='mpesa_b2c_queue_time_out'),
]
