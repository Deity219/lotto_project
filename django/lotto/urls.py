from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'lotto'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/',
         auth_views.LoginView.as_view(template_name='lotto/login.html'),
         name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='lotto:index'),
         name='logout'),

    # 일반 사용자
    path('buy/', views.buy, name='buy'),
    path('my/', views.my_tickets, name='my_tickets'),
    path('check/', views.check, name='check'),

    # 관리자
    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/sales/', views.admin_sales, name='admin_sales'),
    path('manage/draw/', views.admin_draw, name='admin_draw'),
    path('manage/winners/', views.admin_winners, name='admin_winners'),
]