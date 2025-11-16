# -*- encoding: utf-8 -*-

from django.contrib import admin

from .models import Cart, Category, Feedback, Products


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'is_published', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'created_at','assessment')

    search_fields = ('text',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'created_at')