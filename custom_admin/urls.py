from django.urls import path
from . import views


urlpatterns = [
    path('', views.index_view, name='custom_admin'),
    path('users/', views.users_view, name='admin_users'),
    path('users/<int:pk>/', views.single_user_view, name='admin_single_user'),
    path('users/<int:pk>/earnings/', views.user_earnings_view, name='admin_user_earnings'),
    path('users/<int:pk>/withdrawals/', views.user_withdrawals_view, name='admin_user_withdrawals'),
    path('users/<int:pk>/referrals/', views.user_referrals_view, name='admin_user_referrals'),
    path('users/<int:pk>/award-cash/', views.award_cash_view, name='admin_award_cash'),
    path('users/<int:pk>/activation/', views.user_activation_view, name='admin_user_activation'),
    path('users/<int:pk>/change-password/', views.change_user_password_view, name='admin_change_user_password'),
    path('users/<int:pk>/delete/', views.delete_user_view, name='admin_delete_user'),
    path('users/<int:pk>/freezing/', views.user_freezing_view, name='admin_user_freezing'),
    path('users/<int:pk>/sw-top-up/', views.spinwin_top_up_view, name='admin_spinwin_top_up'),

    # Payments
    path('mpesa-received/', views.mpesa_received_view, name='admin_mpesa_received'),
    path('mpesa-sent/', views.mpesa_sent_view, name='admin_mpesa_sent'),
    path('fw-payments/', views.fw_payments_view, name='admin_fw_payments'),

    # Withdrawals
    path('withdrawals/', views.withdrawals_view, name='admin_withdrawals'),
    path('withdrawals/cancel/', views.cancel_withdrawal_view, name='admin_cancel_withdrawal'),
    path('withdrawals/disburse/', views.disburse_withdrawal_view, name='admin_disburse_withdrawal'),
    path('withdrawals/auto-disburse/', views.auto_disburse_withdrawal_view, name='admin_auto_disburse_withdrawal'),

    # Tasks
    path('tasks/', views.tasks_view, name='admin_tasks'),
    path('tasks/new/', views.NewTaskView.as_view(), name='admin_new_task'),
    path('tasks/delete/', views.delete_task_view, name='admin_delete_task'),
    path('tasks/<int:pk>/edit/', views.EditTaskView.as_view(), name='admin_edit_task'),
    path('tasks/user-subscribing/', views.tasks_user_subscribing_view, name='admin_tasks_user_subscribing'),
]
