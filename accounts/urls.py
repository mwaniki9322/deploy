from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/registration/login.html'), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('change-utc-offset/', views.change_utc_offset, name='change_utc_offset'),

    # Password reset
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('dashboard/', views.dashboard_view, name='user_dashboard'),
    path('earnings/', views.earnings_view, name='earnings'),
    path('withdrawals/', views.withdrawals_view, name='withdrawals'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('referrals/', views.referrals_view, name='referrals'),
    path('settings/', views.AccountSettingsView.as_view(), name='account_settings'),

    # Membership
    path('activate/', views.ActivateAccountView.as_view(), name='activate_account'),
    path('activate-start/', views.activate_start, name='activate_start'),
]
