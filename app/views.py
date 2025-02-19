from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.views.static import serve
from django.conf import settings
from .models import Customer, Product, Cart, OrderPlaced, Transaction, Review, STATE_CHOICES
from .forms import CustomerRegistrationForm, CustomerProfileForm, ProductForm
import uuid
import random
import logging
import qrcode
from io import BytesIO
from decimal import Decimal
from urllib.parse import quote
from django.http import Http404 

logger = logging.getLogger(__name__)

def new_confirm_payment(request, order_id):
    context = {
        'order_id': order_id,
    }
    return render(request, 'app/new_confirm_payment.html', context)

def confirm_order(request, order_id):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        
        # Assuming you only expect a numeric transaction ID
        if not transaction_id.isdigit():
            return HttpResponseBadRequest("Invalid transaction ID.")

        order = get_object_or_404(OrderPlaced, id=order_id)

        order.status = 'Pending'  # Change the status as needed
        order.save()

        # Create a new transaction record
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            order=order,
            payment_status='Success'  # Adjust based on your payment gateway response
        )

        return redirect('orders')  # Redirect to the orders page

    return HttpResponseBadRequest("Invalid request.")


def cancel_order(request, order_id):
    order = get_object_or_404(OrderPlaced, id=order_id, user=request.user)
    if order.status != 'Delivered':  # Ensure order can be cancelled
        order.cancelled = True
        order.status = 'Cancel'
        order.save()
        messages.success(request, "Your order has been cancelled successfully! Your money will be returned within 2 hours. Please cancel before the order is delivered.")
    else:
        messages.error(request, "You cannot cancel an order that has already been delivered.")
    
    return redirect('orders')  # Redirect to the orders page


def order_history(request):
    orders = OrderPlaced.objects.filter(user=request.user).prefetch_related('transaction_set')  # Pre-fetch related transactions
    return render(request, 'app/orders.html', {'orders': orders})


def create_order(request):
    if request.method == 'POST':
        user = request.user
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        carts = Cart.objects.filter(user=user)

        if product_id:
            product = get_object_or_404(Product, id=product_id)
            total_amount = product.discounted_price * quantity
            customer = get_object_or_404(Customer, user=user)
            order = OrderPlaced.objects.create(
                user=user,
                customer=customer,
                product=product,
                quantity=quantity
            )
            return redirect('payment_process', total_amount=total_amount, order_id=orders[0].id)
        elif carts.exists():
            total_amount = sum(cart.product.discounted_price * cart.quantity for cart in carts)
            customer = get_object_or_404(Customer, user=user)

            orders = []
            for cart in carts:
                order = OrderPlaced.objects.create(
                    user=user,
                    customer=customer,
                    product=cart.product,
                    quantity=cart.quantity
                )
                orders.append(order)

            # Pass the ID of the first order for payment processing
            if orders:
                return redirect('payment_process', total_amount=total_amount, order_id=orders[0].id)

        return HttpResponse("No items in cart", status=400)

    return HttpResponse("Invalid request method", status=400)


# Custom view to serve media files securely
def serve_media(request, path):
    if not request.user.is_authenticated:
        raise Http404("Media file not found or access restricted.")
    return serve(request, path, document_root=settings.MEDIA_ROOT)

def payment_process(request, total_amount, order_id):
    try:
        total_amount = float(total_amount)  # Convert to float
        order = get_object_or_404(OrderPlaced, id=order_id)

        # Generate a unique numeric transaction ID
        transaction_id = str(random.randint(1000000000, 9999999999))  # 10-digit numeric ID

        # Payment URL creation
        recipient_upi_id = '8128260653@okbizaxis'
        recipient_name = 'BURHANUDDIN MORISWALA'
        transaction_note = 'Payment for Order'

        payment_url = (
            f"upi://pay?pa={quote(recipient_upi_id)}&pn={quote(recipient_name)}&"
            f"am={quote(f'{total_amount:.2f}')}&tid={quote(transaction_id)}&tn={quote(transaction_note)}"
        )

        logger.info("Payment URL generated: %s", payment_url)

        # Generate the QR code dynamically
        qr_code_image = qrcode.make(payment_url)

        # Save the QR code image to a file in the media/qr_codes directory
        qr_code_path = f"qr_codes/{transaction_id}_qr.png"
        img_io = BytesIO()
        qr_code_image.save(img_io, 'PNG')
        img_io.seek(0)

        # Save QR code image to the media folder
        with open(f"{settings.MEDIA_ROOT}/{qr_code_path}", 'wb') as f:
            f.write(img_io.read())

        # Construct the URL to the saved QR code image
        qr_code_url = f"/media/{qr_code_path}"

        # Pass the URL of the QR code image to the template
        context = {
            'qr_code_url': qr_code_url,
            'total_amount': total_amount,
            'order_id': order_id,
        }

        return render(request, 'app/payment_page.html', context)

    except Exception as e:
        logger.error("Error processing payment: %s", str(e))
        return render(request, 'app/payment_error.html', {'error': str(e)})
    

def generate_qr_code(request, transaction_id):
    # Generate the payment URL (you can customize it based on your requirements)
    payment_url = f"upi://pay?pa=8128260653@okbizaxis&pn=BURHANUDDIN&am=100&tid={transaction_id}&tn=Payment+for+Order"
    
    # Generate QR code
    qr_code_image = qrcode.make(payment_url)
    
    # Save QR code to in-memory file (BytesIO)
    img_io = BytesIO()
    qr_code_image.save(img_io, 'PNG')
    img_io.seek(0)
    
    # Return the image as HTTP response
    response = HttpResponse(img_io, content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr_code_{transaction_id}.png"'
    
    return response

def new_checkout(request):
    if request.user.is_authenticated:
        carts = Cart.objects.filter(user=request.user)
        total_amount = sum(cart.product.discounted_price * cart.quantity for cart in carts)
        context = {
            'carts': carts,
            'total_amount': total_amount,
        }
        return render(request, 'app/new_checkout.html', context)
    else:
        return redirect('login')

@login_required
def payment_view(request, order_id):
    order = get_object_or_404(OrderPlaced, id=order_id)
    total_amount = order.product.discounted_price * order.quantity  # Calculate total amount

    # Here, you would typically handle the payment success logic
    payment_successful = True  # Replace with actual payment logic

    if payment_successful:
        order.status = 'Accepted'  # Update status as needed
        order.save()

        # Create a transaction record
        Transaction.objects.create(
            transaction_id='your_unique_transaction_id',  # Generate this uniquely
            order=order,
            payment_status='Completed'
        )

        return redirect('order_confirmation', order_id=order.id)

    return HttpResponseBadRequest("Payment failed.")




def payment_page(request, total_amount):
    # Payment URL and QR code generation logic remains the same
    # Ensure you're just generating the payment page without modifying the cart

    recipient_upi_id = 'aabb52530909@okicici'
    recipient_name = 'BURHANUDDIN MORISWALA'
    transaction_note = 'Payment for Order'

    payment_url = f"upi://pay?pa={recipient_upi_id}&pn={recipient_name}&am={total_amount}&tid=1234567890&tt={transaction_note}"

    qr_code_image = qrcode.make(payment_url)
    qr_code_path = f'media/qr_codes/{total_amount}_qr.png'
    qr_code_image.save(qr_code_path)

    qr_code_url = f'/media/qr_codes/{total_amount}_qr.png'
    
    context = {
        'qr_code_url': qr_code_url,
        'total_amount': total_amount,
    }
    return render(request, 'app/payment_page.html', context)


def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        size = request.POST.get('size')  # Get the selected size
        # Logic to add the product and size to the cart
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity += 1  # Increment quantity if already exists
        cart_item.save()
        return redirect('showcart')  # Redirect to cart or wherever you want



class ProductView(View):
    def get(self, request):
        topwears = Product.objects.filter(category='TW')
        bottomwears = Product.objects.filter(category='BW')
        mobiles = Product.objects.filter(category='M')
        oversized_tshirts = Product.objects.filter(category='OT')
        summer_tshirts = Product.objects.filter(category='ST')
        hoodies = Product.objects.filter(category='HD')

        return render(request, 'app/home.html', {
            'topwears': topwears,
            'bottomwears': bottomwears,
            'mobiles': mobiles,
            'oversized_tshirts': oversized_tshirts,
            'summer_tshirts': summer_tshirts,
            'hoodies': hoodies,
        })


@login_required
def oversized_tshirt(request, data=None):
    oversized_tshirts = Product.objects.filter(category='OT')

    # Filtering logic
    color = request.GET.get('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if color:
        oversized_tshirts = oversized_tshirts.filter(brand=color)  # Assuming brand is used for color
    if min_price:
        oversized_tshirts = oversized_tshirts.filter(selling_price__gte=min_price)
    if max_price:
        oversized_tshirts = oversized_tshirts.filter(selling_price__lte=max_price)

    return render(request, 'app/oversized_tshirt.html', {'oversized_tshirts': oversized_tshirts})

@login_required
def summer_tshirt(request, data=None):
    summer_tshirts = Product.objects.filter(category='ST')

    # Filtering logic
    color = request.GET.get('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if color:
        summer_tshirts = summer_tshirts.filter(brand=color)  # Assuming brand is used for color
    if min_price:
        summer_tshirts = summer_tshirts.filter(selling_price__gte=min_price)
    if max_price:
        summer_tshirts = summer_tshirts.filter(selling_price__lte=max_price)

    return render(request, 'app/summer_tshirt.html', {'summer_tshirts': summer_tshirts})

@login_required
def hoodies(request, data=None):
    hoodies = Product.objects.filter(category='HD')

    # Filtering logic
    color = request.GET.get('color')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if color:
        hoodies = hoodies.filter(brand=color)  # Assuming brand is used for color
    if min_price:
        hoodies = hoodies.filter(selling_price__gte=min_price)
    if max_price:
        hoodies = hoodies.filter(selling_price__lte=max_price)

    return render(request, 'app/hoodies.html', {'hoodies': hoodies})




@login_required
def mobile(request, data=None):
    if data is None:
        mobiles = Product.objects.filter(category='M')
    else:
        mobiles = Product.objects.filter(category='M', brand=data)
    return render(request, 'app/mobile.html', {'mobiles': mobiles})

class ProductDetailView(View):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'app/productdetail.html', {'product': product})
    



# views.py


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success_page')  # Redirect to a success page
    else:
        form = ProductForm()
    
    return render(request, 'app/add_product.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        size = request.POST.get('size')  # Get the selected size
        # Logic to add the product and size to the cart
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity += 1  # Increment quantity if already exists
        cart_item.save()
        return redirect('showcart')  # Redirect to cart or wherever you want



@login_required
def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = 0.0
    shipping_amount = 70.0
    total_amount = 0.0
    if cart.exists():
        for p in cart:
            temp_amount = p.quantity * p.product.discounted_price
            amount += temp_amount
        total_amount = amount + shipping_amount
        return render(request, 'app/addtocart.html', {
            'carts': cart,
            'totalamount': total_amount,
            'amount': amount
        })
    else:
        return render(request, 'app/emptycart.html')

@login_required
def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity += 1
        c.save()
        amount = 0.0
        shipping_amount = 70.0
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            temp_amount = item.quantity * item.product.discounted_price
            amount += temp_amount
        total_amount = amount + shipping_amount
        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': total_amount
        }
        return JsonResponse(data)

@login_required
def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity -= 1
        c.save()
        amount = 0.0
        shipping_amount = 70.0
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            temp_amount = item.quantity * item.product.discounted_price
            amount += temp_amount
        total_amount = amount + shipping_amount
        data = {
            'quantity': c.quantity,
            'amount': amount,
            'totalamount': total_amount
        }
        return JsonResponse(data)

@login_required
def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.delete()
        amount = 0.0
        shipping_amount = 70.0
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            temp_amount = item.quantity * item.product.discounted_price
            amount += temp_amount
        total_amount = amount + shipping_amount
        data = {
            'amount': amount,
            'totalamount': total_amount
        }
        return JsonResponse(data)
    
    

def shop(request):
    products = Product.objects.all()
    return render(request, 'app/shop.html', {'products': products})

@login_required
def buy_now(request):
    if request.method == 'GET':
        product_id = request.GET.get('prod_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Get all addresses for the user
        addresses = Customer.objects.filter(user=request.user)

        return render(request, 'app/buynow.html', {
            'product': product,
            'add': addresses  # Pass addresses to the template
        })

@login_required
def place_order(request):
    if request.method == 'POST':
        user = request.user
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        carts = Cart.objects.filter(user=user)

        if product_id:
            product = get_object_or_404(Product, id=product_id)
            total_amount = product.discounted_price * quantity
            customer = get_object_or_404(Customer, user=user)
            order = OrderPlaced.objects.create(
                user=user,
                customer=customer,
                product=product,
                quantity=quantity
            )
            return redirect('payment_process', total_amount=total_amount, order_id=order.id)

        elif carts.exists():
            total_amount = sum(cart.product.discounted_price * cart.quantity for cart in carts)
            customer = get_object_or_404(Customer, user=user)

            orders = []
            for cart in carts:
                order = OrderPlaced.objects.create(
                    user=user,
                    customer=customer,
                    product=cart.product,
                    quantity=cart.quantity
                )
                orders.append(order)

            if orders:
                return redirect('payment_process', total_amount=total_amount, order_id=orders[0].id)

        return HttpResponse("No items in cart", status=400)

    return HttpResponse("Invalid request method", status=400)

@login_required
def order_summary(request):
    return render(request, 'app/order_summary.html')


@login_required
def orders(request):
    user_orders = OrderPlaced.objects.filter(user=request.user)
    return render(request, 'app/orders.html', {'orders': user_orders})


class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})
    
    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Congratulations! Registered Successfully.')
            form.save()
        return render(request, 'app/customerregistration.html', {'form': form})





def individual_checkout(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        total_price = product.discounted_price * quantity
        
        # Pass the data to the template
        context = {
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
            # customer_info should be fetched here
        }
        return render(request, 'app/individual_checkout.html', context)
    
    else:
        # Check the current user for debugging purposes
        print(f"Current logged-in user: {request.user.username}")  # Debugging line
        product_id = request.GET.get('product_id')
        quantity = request.GET.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)
        total_price = product.discounted_price * int(quantity)

        # Fetch the customer's information
        try:
            customer_info = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            customer_info = None  # Handle case where no customer is found for the user

        print(f"Customer info found: {customer_info}")  # Debugging line

        context = {
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
            'customer_info': customer_info,
        }
        return render(request, 'app/individual_checkout.html', context)

@login_required
def address(request):
    # Fetch customer information (assuming each user has only one customer object)
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {'add': add, 'active': 'address'})

@login_required
def edit_address(request, id):
    # Get the customer's address based on the ID
    customer = get_object_or_404(Customer, id=id, user=request.user)

    if request.method == 'POST':
        # Update address fields from the POST data
        customer.name = request.POST.get('name', customer.name)
        customer.locality = request.POST.get('locality', customer.locality)
        customer.city = request.POST.get('city', customer.city)
        customer.state = request.POST.get('state', customer.state)
        customer.zipcode = request.POST.get('zipcode', customer.zipcode)
        customer.phone_number = request.POST.get('phone_number', customer.phone_number)

        customer.save()
        messages.success(request, "Address updated successfully!")
        return redirect('address')  # Redirect to address page after saving

    # Pass STATE_CHOICES to the template
    return render(request, 'app/edit_address.html', {
        'customer': customer,
        'STATE_CHOICES': STATE_CHOICES # Make sure this is passed to the template
    })


@login_required
def delete_address(request, id):
    # Get the customer's address based on the ID
    customer = get_object_or_404(Customer, id=id, user=request.user)

    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Address deleted successfully!")
        return redirect('address')  # Redirect to address page after deleting

    return render(request, 'app/delete_address.html', {'customer': customer})


@login_required
def add_address(request):
    # Check if the user already has a Customer record
    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Directly updating the customer model with the address details
        customer.name = request.POST.get('name', customer.name)
        customer.locality = request.POST.get('locality', customer.locality)
        customer.city = request.POST.get('city', customer.city)
        customer.zipcode = request.POST.get('zipcode', customer.zipcode)
        customer.state = request.POST.get('state', customer.state)
        customer.phone_number = request.POST.get('phone_number', customer.phone_number)
        
        # Save the customer object with the new address information
        customer.save()

        # Redirect to the address page (address list)
        return redirect('address')

    return render(request, 'app/add_address.html')  # Render the add_address template

class ProfileView(View):
    def get(self, request):
        # Fetch the customer object, create one if it doesn't exist
        customer, created = Customer.objects.get_or_create(user=request.user)
        form = CustomerProfileForm(instance=customer)  # Pre-populate the form with current data
        return render(request, 'app/profile.html', {'form': form, 'active': 'profile'})

    def post(self, request):
        customer = Customer.objects.get(user=request.user)
        form = CustomerProfileForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')

        return render(request, 'app/profile.html', {'form': form, 'active': 'profile'})

    

@login_required
def order_summary(request):
    pass


def privacy_policy(request):
    return render(request, 'app/privacy-policy.html')

def why_choose_us(request):
    return render(request, 'app/why_choose_us.html')

def payment_instructions(request):
    return render(request, 'app/payment_instructions.html')

def order_cancellation_policy(request):
    return render(request, 'app/order_cancellation_policy.html')




@login_required
def order_confirmation(request, order_id):
    # Get the specific order
    order = get_object_or_404(OrderPlaced, id=order_id)
    
    # Fetch all orders for the same transaction or user
    orders = OrderPlaced.objects.filter(user=request.user, customer=order.customer)
    
    # Prepare product images
    for order in orders:
        order.product_image_url = order.product.product_image.url if order.product.product_image else None
    
    return render(request, 'app/order_confirmation.html', {
        'orders': orders  # Pass all orders to the template
    })



from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review  # Import your Review model

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)

    if request.method == 'POST':
        # Handle review submission
        user_name = request.POST.get('user_name')
        content = request.POST.get('content')
        Review.objects.create(product=product, user_name=user_name, content=content)
        return redirect('product-detail', product_id=product_id)

    suggested_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:12]

    # Define the sizes list
    sizes = ['S', 'M', 'L', 'XL', 'XXL']

    return render(request, 'app/productdetail.html', {
        'product': product,
        'reviews': reviews,
        'suggested_products': suggested_products,
        'sizes': sizes,  # Add sizes to context
    })









