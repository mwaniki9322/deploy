from django.urls import path
from . import views


urlpatterns = [
    path('', views.index_view, name='spinwin'),
    path('top-up/', views.top_up_spins_view, name='spinwin_top_up'),
    path('spin/', views.spin_view, name='spinwin_spin'),
    path('acknowledge/<int:pk>/', views.acknowledge_spin_record, name='spinwin_acknowledge'),
]
