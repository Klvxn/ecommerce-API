from django import forms
from orders.models import Order

class CartForm(forms.Form):
    
    quantity = forms.IntegerField(widget=forms.NumberInput, initial=1, required=True)


class OrderForm(forms.Form):

    street_address = forms.CharField()
    zip_code = forms.IntegerField(widget=forms.NumberInput)
    city = forms.CharField()
    state = forms.CharField()

    class Meta:
        model = Order
        exclude = ['status', 'customer', 'address']


class LoginForm(forms.Form):

    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


from cart.cart import Cart
from customers.models import Address
from .models import Product
from orders.models import Order, OrderItem


from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as login_user
from django.urls import path, reverse


def product_view(request):
    products = Product.objects.filter(available=True)
    context = {'products': products}
    return render(request, 'products_page.html', context)


def product_detail(request, pk):
    product = Product.objects.get(pk=pk)
    if request.method == "POST":
        print(request.POST)
        form = CartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            user_cart = Cart(request)
            user_cart.add_item(product, quantity)
            context = {'form': form}
            return render(request, 'product_page.html', context)
    form = CartForm()
    context = {'form': form, 'product': product}
    return render(request, 'product_page.html', context)


def cart_items(request):
    user_cart = Cart(request)
    context = {'cart': user_cart}
    return render(request, 'cart_page.html', context)

@require_POST
def remove_item(request, product):
    product = Product.objects.get(name=product)
    user_cart = Cart(request)
    user_cart.remove_item(product=product)
    return HttpResponseRedirect('/cart/')


@login_required(login_url='/login/')
def create_order(request):
    user_cart = Cart(request)
    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            order = Order(customer=request.user)
            order.address = Address.objects.create(
                street_address=form.cleaned_data['street_address'],
                zip_code=form.cleaned_data['zip_code'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state']
            )
            order.save()

            for item in user_cart:
                OrderItem.objects.create(
                    order=order,
                    product=Product.objects.get(name=item['product']),
                    quantity=item['quantity'],
                    cost_per_item=item['price']
                )
 
            user_cart.clear()
            context = {'form': form, 'order': order}
            return redirect(reverse('payment', args=[order.pk]))

    else:
        form = OrderForm()
    context = {'form': form}
    return render(request, 'order_create.html', context)


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            login_user(request, user)
            return HttpResponseRedirect('/order/')
    form = LoginForm()
    context = {'form': form}
    return render(request, 'login.html', context)



urlpatterns = [
    path("prods/<int:pk>/", product_detail, name='product_detail'),
    path("prods/", product_view),
    path("cart/", cart_items),
    path("order/", create_order),
    path("login/", login),
    path("remove_cart-item/<str:product>/", remove_item, name='remove_item'),
]
