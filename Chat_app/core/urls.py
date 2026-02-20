from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.user_list, name='user-list'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
]