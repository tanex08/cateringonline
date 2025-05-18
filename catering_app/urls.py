# catering_app/urls.py
from django.urls import path, include, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'catering_app' 

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/', views.menu_list, name='menu_list'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='catering_app/logged_out.html'), name='logout'),
    
    
    path('account_activation_sent/', views.account_activation_sent, name='account_activation_sent'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
   

 
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    
    path('order/create/', views.order_create, name='order_create'),
    path('order/created/', views.order_created, name='order_created'),
    path('order/history/', views.order_history, name='order_history'),
    path('order/<int:order_id>/review/', views.add_review, name='add_review'),

    
    path('profile/update/', views.profile_update, name='profile_update'),

    
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/menus/', views.staff_menu_list, name='staff_menu_list'),
    path('staff/orders/', views.staff_order_list, name='staff_order_list'),
    path('staff/orders/<int:order_id>/', views.staff_order_detail, name='staff_order_detail'),
    path('staff/reviews/', views.staff_review_list, name='staff_review_list'),
    path('staff/reports/sales/', views.staff_sales_report, name='staff_sales_report'),
    path('staff/users/', views.staff_user_list, name='staff_user_list'),
    path('staff/menus/category/new/', views.staff_category_create, name='staff_category_create'),
    path('staff/menus/category/<int:category_id>/edit/', views.staff_category_update, name='staff_category_update'),
    path('staff/menus/category/<int:category_id>/delete/', views.staff_category_delete, name='staff_category_delete'),
    
   
    path('staff/menus/item/new/', views.staff_menu_item_add, name='staff_menu_item_add'),
    path('staff/menus/category/<int:category_id>/item/new/', views.staff_menu_item_create, name='staff_menu_item_create'),
    path('staff/menus/item/<int:item_id>/edit/', views.staff_menu_item_update, name='staff_menu_item_update'),
    path('staff/menus/item/<int:item_id>/delete/', views.staff_menu_item_delete, name='staff_menu_item_delete'),

    
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='catering_app/password_reset.html',
             email_template_name='catering_app/password_reset_email.html',
             subject_template_name='catering_app/password_reset_subject.txt',
             success_url=reverse_lazy('catering_app:password_reset_done')
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='catering_app/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='catering_app/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='catering_app/password_reset_complete.html'),
         name='password_reset_complete'),
]