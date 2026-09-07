# -*- encoding: utf-8 -*-

from django.urls import path, re_path, include
from sample_app import views
from django.conf import settings
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("account/", views.account, name="account"),
    path("account/password/", views.change_password, name="change-password"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add-to-cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update-cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove-from-cart"),
    path("main-page/", views.main_page, name="main-page"),
    path("shop/", views.shop_page, name="shop"),
    path("api/products/", views.product_list_create, name="product-list-create"),
    path("api/products/<int:product_id>/", views.product_detail, name="product-detail"),
    path('', views.index, name ='index'),
    # Matches any html file
    re_path(r'^.*\.html', views.pages, name='pages'),
    re_path(r'', views.pages, name='pages'),
]