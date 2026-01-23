from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    path('', views.home, name='home'),
    path('report/', views.report_issue, name='report'),
    path('issue/<int:pk>/', views.issue_detail, name='detail'),
    path('category/<int:category_id>/', views.issues_by_category, name='by_category'),
]
