from django.urls import path
from . import views

app_name = 'authorities'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('issue/<int:issue_id>/', views.issue_detail, name='issue_detail'),
    path('issue/<int:issue_id>/update/', views.post_update, name='post_update'),
]
