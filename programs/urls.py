# programs/urls.py
from django.urls import path
from . import views

app_name = 'programs'

urlpatterns = [
    # Program management
    path('', views.index, name='index'),
    path('create/', views.create_program, name='create'),
    path('<int:pk>/', views.program_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_program, name='edit'),
    path('<int:pk>/delete/', views.delete_program, name='delete'),
    
    # House management
    path('<int:program_pk>/houses/', views.houses_list, name='houses_list'),
    path('<int:program_pk>/houses/<int:house_pk>/', views.house_detail, name='house_detail'),
    
    # House general info
    path('<int:program_pk>/houses/<int:house_pk>/general-info/', views.house_general_info, name='house_general_info'),
    path('<int:program_pk>/houses/<int:house_pk>/general-info/edit/', views.edit_house_general_info, name='edit_house_general_info'),
    
    # Technical analysis
    path('<int:program_pk>/houses/<int:house_pk>/technical-analysis/', views.technical_analysis, name='technical_analysis'),
    path('<int:program_pk>/houses/<int:house_pk>/rooms/<str:room_type>/<int:room_number>/', views.room_detail, name='room_detail'),
    path('<int:program_pk>/houses/<int:house_pk>/rooms/<str:room_type>/<int:room_number>/edit/', views.edit_room_detail, name='edit_room_detail'),
]