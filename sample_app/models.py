# -*- encoding: utf-8 -*-

from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    title = models.CharField('title', max_length=256)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.title


class Products(models.Model):
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE, null=True,
                                 related_name='products')
    title = models.CharField('title', max_length=256)
    content = models.TextField('content')
    price = models.IntegerField('price', default=0)
    image = models.ImageField('image', upload_to='product-image', blank=True)
    is_published = models.BooleanField('is published', default=False)
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.title


class Feedback(models.Model):
    product = models.ForeignKey(Products, verbose_name='product', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='user', on_delete=models.CASCADE)
    text = models.TextField('text')
    assessment = models.IntegerField('assessment', choices = [(1, '1 star'), (2, '2 stars'), (3, '3 stars'), (4, '4 stars'), (5, '5 stars')], default = 5)
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f'User: {self.user} | Product: {self.product.title}'


class Cart(models.Model):
    user = models.ForeignKey(User, verbose_name='user', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, verbose_name='product', on_delete=models.CASCADE)
    quantity = models.IntegerField('quantity', default=1)
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f'User: {self.user} | Product: {self.product.title}'

# Create model for News project