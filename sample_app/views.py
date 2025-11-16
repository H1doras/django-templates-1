# -*- encoding: utf-8 -*-

import json

from django.shortcuts import render
from django.template import loader
from django.http import JsonResponse, HttpResponse
from django import template
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from .models import Products, Category, Feedback


def _build_context(request=None):
    selected_product_id = None
    if request is not None:
        selected_product_id = request.GET.get("product") or request.GET.get("product_id")

    products = Products.objects.filter(is_published=True).select_related("category").order_by("-created_at")
    selected_product = None
    if selected_product_id:
        selected_product = products.filter(id=selected_product_id).first()

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
    return render(request, "products-view.html", _build_context())


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
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            # just a mail system
            htmly = get_template('email.html')
            d = {'username': username}
            subject, from_email, to = 'welcome', 'your_email@gmail.com', email
            html_content = htmly.render(d)
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            ################################################################## 
            messages.success(request, f'Your account has been created ! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form, 'title': 'register here'})
 
#login forms 
def Login(request):
    if request.method == 'POST':
 
        # AuthenticationForm_can_also_be_used__
 
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f' welcome {username} !!')
            return redirect('initial_lg')
        else:
            messages.info(request, f'account done not exit please sign in')
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'title': 'log in'})