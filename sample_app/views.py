# -*- encoding: utf-8 -*-

import json

from django.shortcuts import render
from django.template import loader
from django.http import JsonResponse, HttpResponse
from django import template
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from .forms import AccountForm, UserRegisterForm
from .models import Cart

from .models import Products, Category, Feedback


def _build_context(request=None, limit=None):
    selected_product_id = None
    if request is not None:
        selected_product_id = request.GET.get("product") or request.GET.get("product_id")

    all_products = Products.objects.filter(is_published=True).select_related("category").order_by("-created_at")
    products = all_products[:limit] if limit else all_products

    selected_product = None
    if selected_product_id:
        selected_product = all_products.filter(id=selected_product_id).first()

    if selected_product is None and products:
        selected_product = products.first()

    feedback_items = list(Feedback.objects.filter(product=selected_product).select_related("user").order_by("-created_at")) if selected_product else []

    if not feedback_items and selected_product:
        feedback_items = [
            {"user": "Amina R.", "text": "Love the smooth finish and how lightweight it feels. It looks even better in person."},
            {"user": "Noah K.", "text": "A very easy piece to style in the kitchen. The size is perfect for everyday use."},
        ]

    return {
        "variable": "Simple Variable Injection",
        "bool_var": True,
        "list": [1, 2, 3, 4, 5],
        "products": products,
        "categories": Category.objects.all().order_by("title"),
        "selected_product": selected_product,
        "feedback_items": feedback_items,
        "cart_count": Cart.objects.filter(user=request.user).count() if request and request.user.is_authenticated else 0,
    }


def pages(request):
    context = _build_context(request)

    requested_html = request.path.split('/')[-1]

    if not requested_html or requested_html == '':
        requested_html = 'index.html'

    try:
        html_file = loader.get_template(requested_html)
        return HttpResponse(html_file.render(context, request))
    except template.TemplateDoesNotExist:
        return HttpResponse("template not found = " + requested_html, status=404)
    except Exception:
        return HttpResponse("Error 500", status=500)


def shop_page(request):
    return render(request, "products-view.html", _build_context(request))


def main_page(request):
    return render(request, "main_page.html", _build_context(request, limit=5))


def _parse_json_body(request):
    if request.content_type and "application/json" in request.content_type:
        return json.loads(request.body.decode("utf-8"))
    return request.POST.dict()


def _serialize_product(product):
    return {
        "id": product.id,
        "title": product.title,
        "content": product.content,
        "price": product.price,
        "category_id": product.category_id,
        "category_title": product.category.title if product.category else None,
        "is_published": product.is_published,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "image": product.image.url if product.image else None,
    }


@csrf_exempt
def product_list_create(request):
    if request.method == "GET":
        products = Products.objects.select_related("category").order_by("-created_at")
        return JsonResponse(
            {"products": [_serialize_product(p) for p in products]},
            safe=False
        )

    if request.method == "POST":
        data = _parse_json_body(request)

        title = (data.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)

        category = None
        category_id = data.get("category_id")
        if category_id:
            category = Category.objects.filter(id=category_id).first()
            if not category:
                return JsonResponse({"error": "category not found"}, status=400)

        try:
            price = int(data.get("price", 0) or 0)
        except ValueError:
            return JsonResponse({"error": "price must be an integer"}, status=400)

        is_published = str(data.get("is_published", False)).lower() in ("1", "true", "yes", "on")

        product = Products.objects.create(
            category=category,
            title=title,
            content=data.get("content", ""),
            price=price,
            is_published=is_published,
        )

        if "image" in request.FILES:
            product.image = request.FILES["image"]
            product.save(update_fields=["image"])

        return JsonResponse(_serialize_product(product), status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def product_detail(request, product_id):
    product = Products.objects.select_related("category").filter(id=product_id).first()
    if not product:
        return JsonResponse({"error": "product not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(_serialize_product(product))

    if request.method == "PUT":
        data = _parse_json_body(request)

        if "title" in data:
            product.title = (data.get("title") or "").strip() or product.title

        if "content" in data:
            product.content = data.get("content", product.content)

        if "price" in data:
            try:
                product.price = int(data.get("price", 0) or 0)
            except ValueError:
                return JsonResponse({"error": "price must be an integer"}, status=400)

        if "is_published" in data:
            product.is_published = str(data.get("is_published")).lower() in ("1", "true", "yes", "on")

        if "category_id" in data and data.get("category_id") not in (None, ""):
            category = Category.objects.filter(id=data.get("category_id")).first()
            if not category:
                return JsonResponse({"error": "category not found"}, status=400)
            product.category = category

        product.save()
        return JsonResponse(_serialize_product(product))

    if request.method == "DELETE":
        product.delete()
        return JsonResponse({"deleted": True, "id": product_id})

    return JsonResponse({"error": "Method not allowed"}, status=405)

#index page 
def index(request):
    return render(request, 'index.html', {'title': 'index'})

#register forms 
def register(request):
    form = UserRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('account')

    return render(request, 'register.html', {'form': form, 'title': 'Create your account'})
 
#login forms 
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.username}.')
        next_url = request.POST.get('next') or request.GET.get('next') or 'account'
        return redirect(next_url)

    return render(request, 'login.html', {'form': form, 'title': 'Log in'})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required(login_url='login')
def account(request):
    form = AccountForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your account details have been updated.')
        return redirect('account')

    cart_items = list(Cart.objects.filter(user=request.user).select_related('product').order_by('-created_at'))
    recent_items = cart_items[:3]

    return render(request, 'account.html', {
        'form': form,
        'cart_count': len(cart_items),
        'recent_items': recent_items,
        'cart_total': sum(item.product.price * item.quantity for item in cart_items),
        'delivery_status': 'Ready for dispatch' if cart_items else 'No items yet',
        'title': 'My account',
    })


@staff_member_required(login_url='login')
def staff_dashboard(request):
    all_cart_items = list(Cart.objects.select_related('user', 'product').order_by('-created_at'))
    recent_products = list(Products.objects.select_related('category').order_by('-created_at')[:6])
    recent_feedback = list(Feedback.objects.select_related('user', 'product').order_by('-created_at')[:6])

    user_entries = []
    user_lookup = {}

    for item in all_cart_items:
        existing = user_lookup.get(item.user_id)
        if existing is None:
            existing = {
                'user': item.user,
                'items': [],
                'total_items': 0,
                'subtotal': 0,
            }
            user_lookup[item.user_id] = existing
            user_entries.append(existing)

        existing['items'].append(item)
        existing['total_items'] += item.quantity
        existing['subtotal'] += item.product.price * item.quantity

    for entry in user_entries:
        if entry['subtotal'] >= 500:
            entry['delivery_status'] = 'Ready for dispatch'
        elif entry['total_items']:
            entry['delivery_status'] = 'Queued for delivery'
        else:
            entry['delivery_status'] = 'No active cart'

    total_customers = len(user_entries)
    total_items = sum(entry['total_items'] for entry in user_entries)
    total_value = sum(entry['subtotal'] for entry in user_entries)

    return render(request, 'staff_dashboard.html', {
        'user_entries': user_entries,
        'recent_products': recent_products,
        'recent_feedback': recent_feedback,
        'total_customers': total_customers,
        'total_items': total_items,
        'total_value': total_value,
        'total_products': Products.objects.count(),
        'published_products': Products.objects.filter(is_published=True).count(),
        'feedback_count': Feedback.objects.count(),
        'title': 'Staff dashboard',
    })


@login_required(login_url='login')
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your password has been changed.')
        return redirect('account')

    return render(request, 'password_change.html', {'form': form, 'title': 'Change password'})

@login_required(login_url='login')
def cart(request):
    items = list(Cart.objects.filter(user=request.user).select_related('product')) if request.user.is_authenticated else []
    subtotal = sum(item.product.price * item.quantity for item in items)
    delivery = 0 if subtotal >= 500 or not items else 35
    return render(request, 'cart.html', {'items': items, 'subtotal': subtotal, 'delivery': delivery, 'total': subtotal + delivery, 'title': 'Your cart'})


@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('shop')

    product = Products.objects.filter(id=product_id, is_published=True).first()
    if not product:
        messages.error(request, 'That product is no longer available.')
        return redirect('shop')

    item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])

    messages.success(request, f'{product.title} was added to your cart.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart'
    return redirect(next_url)


@login_required(login_url='login')
def update_cart(request, item_id):
    if request.method == 'POST':
        item = Cart.objects.filter(id=item_id, user=request.user).first()
        if item:
            try:
                quantity = max(0, min(int(request.POST.get('quantity', 1)), 99))
            except (TypeError, ValueError):
                quantity = item.quantity
            if quantity:
                item.quantity = quantity
                item.save(update_fields=['quantity'])
            else:
                item.delete()
    return redirect('cart')


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        Cart.objects.filter(id=item_id, user=request.user).delete()
    return redirect('cart')