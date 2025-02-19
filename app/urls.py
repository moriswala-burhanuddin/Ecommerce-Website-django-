from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .forms import LoginForm, MypasswordChangeForm
from .views import  oversized_tshirt, summer_tshirt, hoodies,product_detail,payment_process, new_confirm_payment, confirm_order,cancel_order
from .views import add_product
from .views import privacy_policy, why_choose_us, payment_instructions, order_cancellation_policy,serve_media



urlpatterns = [
    path('', views.ProductView.as_view(), name="home"),
    path('shop/', views.shop, name='shop'),
    path('product-detail/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:product_id>/', product_detail, name='product-detail'),
    
   path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),


    path('cart/', views.show_cart, name='showcart'), 
    
    path('pluscart/', views.plus_cart, name='pluscart'),
    path('minuscart/', views.minus_cart, name='minuscart'),
    path('removecart/', views.remove_cart, name='removecart'),
    path('add-product/', add_product, name='add_product'),
  
    path('buy/', views.buy_now, name='buy-now'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('address/', views.address, name='address'),
    path('add-address/', views.add_address, name='add_address'), 
    path('edit-address/<int:id>/', views.edit_address, name='edit_address'),    # URL for editing address
    path('address/delete/<int:id>/', views.delete_address, name='delete_address'), 
    path('orders/', views.orders, name='orders'),
    path('place_order/', views.place_order, name='place_order'),
    path('order-summary/', views.order_summary, name='order_summary'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    
    # Mobile URL paths
    path('mobile/', views.mobile, name='mobile'),
    path('mobile/<slug:data>/', views.mobile, name='mobiledata'),

    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='app/login.html',
        authentication_form=LoginForm
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('passwordchange/', auth_views.PasswordChangeView.as_view(
        template_name='app/passwordchange.html',
        form_class=MypasswordChangeForm,
        success_url='/passwordchangedone/'
    ), name='passwordchange'),

    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app/passwordchangedone.html'
    ), name='passwordchangedone'),
    
    # Reset password
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='app/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='app/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='app/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='app/password_reset_complete.html'), name='password_reset_complete'),
    
    path('registration/', views.CustomerRegistrationView.as_view(), name='customerregistration'),
    path('new_checkout/', views.new_checkout, name='new_checkout'),
    path('checkout/individual/', views.individual_checkout, name='individual_checkout'),
    
    # Correct payment URLs to capture both total_amount and order_id
    path('payment/<str:total_amount>/<int:order_id>/', payment_process, name='payment_process'),

    path('generate_qr_code/<str:transaction_id>/', views.generate_qr_code, name='generate_qr_code'),
    path('confirm_payment/<int:order_id>/', new_confirm_payment, name='new_confirm_payment'),

    path('confirm_order/<int:order_id>/', confirm_order, name='confirm_order'),
    path('oversized_tshirts/', oversized_tshirt, name='oversized_tshirt'),
    path('summer_tshirts/', summer_tshirt, name='summer_tshirt'),
    path('hoodies/', hoodies, name='hoodies'),

    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('why-choose-us/', why_choose_us, name='why_choose_us'),
    path('payment-instructions/', payment_instructions, name='payment_instructions'),
    path('order-cancellation/', order_cancellation_policy, name='order_cancellation_policy'),
    path('media/<path:path>/', serve_media, name='serve_media'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
