# from django.contrib import admin
# from .models import Customer, Product, Cart, OrderPlaced,Transaction

# @admin.register(Customer)
# class CustomerModelAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'name', 'locality', 'city', 'zipcode', 'state']

# @admin.register(Product)
# class ProductModelAdmin(admin.ModelAdmin):
#     list_display = ['id', 'title', 'selling_price', 'discounted_price', 'description', 'brand', 'category', 'product_image']

# @admin.register(Cart)
# class CartModelAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'product', 'quantity']

# @admin.register(OrderPlaced)
# class OrderPlacedModelAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'customer', 'product', 'quantity',
#                     'ordered_date', 'status']
    
# admin.site.register(Transaction)

from django.contrib import admin
from .models import Customer, Product, Cart, OrderPlaced, Transaction

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'locality', 'city', 'zipcode', 'state', 'phone_number']  # Added phone_number
    search_fields = ['name', 'city', 'phone_number']  # Added phone_number to search fields

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'selling_price', 'discounted_price', 'brand', 'category']
    list_filter = ['category']
    search_fields = ['title', 'brand']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity']

@admin.register(OrderPlaced)
class OrderPlacedModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer', 'product', 'quantity', 'ordered_date', 'status']
    list_filter = ['status', 'ordered_date']
    search_fields = ['user__username', 'product__title']

@admin.register(Transaction)
class TransactionModelAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'created_at']
