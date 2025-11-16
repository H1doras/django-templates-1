# -*- encoding: utf-8 -*-

from django.urls import path, re_path, include
from sample_app import views
from django.conf import settings
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("shop/", views.shop_page, name="shop"),
    path("api/products/", views.product_list_create, name="product-list-create"),
    path("api/products/<int:product_id>/", views.product_detail, name="product-detail"),
    path('', views.index, name ='index'),
    # Matches any html file
    re_path(r'^.*\.html', views.pages, name='pages'),
    re_path(r'', views.pages, name='pages'),
]