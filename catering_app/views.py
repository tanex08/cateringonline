from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserRegistrationForm, CartAddItemForm, OrderCreateForm, ReviewForm, MenuCategoryForm, MenuItemForm, OrderStatusUpdateForm, SalesReportDateFilterForm, UserProfileUpdateForm
from .models import MenuCategory, MenuItem, Order, OrderItem, Review
from django.contrib.auth.decorators import login_required, user_passes_test
from .cart import Cart
from django.contrib.auth.views import LoginView as AuthLoginView 
from django.urls import reverse_lazy
from django.db.models import Sum, Avg, Count 
import datetime 
from django.utils import timezone 
from datetime import timedelta 


from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
User = get_user_model()



class CustomLoginView(AuthLoginView):
    template_name = 'catering_app/login.html'
    redirect_authenticated_user = True 

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse_lazy('catering_app:staff_dashboard')
        else:
            return reverse_lazy('catering_app:dashboard')

def home(request):
    return render(request, 'catering_app/base.html') 

def register(request):
    if request.user.is_authenticated:
        return redirect('catering_app:dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            
           
            current_site = get_current_site(request)
            mail_subject = render_to_string('catering_app/account_activation_subject.txt').strip()
            message = render_to_string('catering_app/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            try:
                email.send()
                messages.success(request, 'Please check your email to complete the registration and activate your account.')
                return redirect('catering_app:account_activation_sent') 
            except Exception as e: 
                messages.error(request, f'Error sending activation email: {e}. Please contact support.')
                

        else:
           
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'catering_app/register.html', {'form': form})

def account_activation_sent(request):
    return render(request, 'catering_app/account_activation_sent.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # login(request, user) # Optional: log the user in directly after activation
        messages.success(request, 'Thank you for your email confirmation. You can now log in to your account.')
        return redirect('catering_app:login') # Or 'catering_app:account_activation_complete'
    else:
        messages.error(request, 'Activation link is invalid or has expired!')
        return redirect('catering_app:register') # Or 'catering_app:account_activation_invalid'



def menu_list(request):
    categories = MenuCategory.objects.prefetch_related('items').filter(items__is_available=True).distinct()
   
    
    context = {
        'categories': categories
    }
    return render(request, 'catering_app/menu_list.html', context)

@login_required
def dashboard(request):

    context = {
        'welcome_message': f'Welcome to your dashboard, {request.user.username}!'
    }
    return render(request, 'catering_app/dashboard.html', context)

@require_POST
def add_to_cart(request, item_id):
    cart = Cart(request)
    menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    form = CartAddItemForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(item=menu_item,
                 quantity=cd['quantity'],
                 update_quantity=cd['update'])
        messages.success(request, f'"{menu_item.name}" was added to your cart.')
    else:
        messages.error(request, 'There was an error adding the item to your cart.')
    return redirect('catering_app:cart_detail') 

@require_POST 
def remove_from_cart(request, item_id):
    cart = Cart(request)
    menu_item = get_object_or_404(MenuItem, id=item_id)
    cart.remove(menu_item)
    messages.success(request, f'"{menu_item.name}" was removed from your cart.')
    return redirect('catering_app:cart_detail')

def cart_detail(request):
    cart = Cart(request)
   
    for item_in_cart in cart:
        item_in_cart['update_quantity_form'] = CartAddItemForm(
            initial={'quantity': item_in_cart['quantity'], 'update': True}
        )
    return render(request, 'catering_app/cart_detail.html', {'cart': cart})

@login_required
def order_create(request):
    cart = Cart(request)
    if not cart: # If cart is empty, redirect them
        messages.info(request, "Your cart is empty. Please add items before making a reservation.")
        return redirect('catering_app:menu_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user 

            order.save() 

            for item_in_cart in cart:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item_in_cart['item'],
                    price=item_in_cart['price'], 
                    quantity=item_in_cart['quantity']
                )
            
            cart.clear()
            
           
            request.session['order_id'] = order.id
          
            return redirect('catering_app:order_created')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = OrderCreateForm()
    
        
    return render(request, 'catering_app/order_create.html', {'cart': cart, 'form': form})

@login_required
def order_created(request):
    order_id = request.session.get('order_id')
    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user) 
        except Order.DoesNotExist:
            pass 
    
    if not order:
        messages.error(request, "Could not retrieve your order confirmation. Please check your dashboard.")
        return redirect('catering_app:dashboard')

    return render(request, 'catering_app/order_created.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at') 
    context = {
        'orders': orders
    }
    return render(request, 'catering_app/order_history.html', context)

@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, status='DELIVERED') 
    
  
    existing_review = Review.objects.filter(order=order, user=request.user).first()
    if existing_review:
        messages.info(request, "You have already reviewed this order.")
        return redirect('catering_app:order_history')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.user = request.user
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('catering_app:order_history')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'order': order
    }
    return render(request, 'catering_app/add_review.html', context)


def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user, login_url='catering_app:login') 
def staff_dashboard(request):
    
    pending_orders_count = Order.objects.filter(status='PENDING').count()
    confirmed_orders_count = Order.objects.filter(status='CONFIRMED').count()
    preparing_orders_count = Order.objects.filter(status='PREPARING').count()

    
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_reviews_count = Review.objects.filter(created_at__gte=seven_days_ago).count()


    actionable_orders = Order.objects.filter(status__in=['PENDING', 'CONFIRMED']) \
                            .order_by('scheduled_datetime')[:5] 

    context = {
        'greeting': f'Hello, {request.user.first_name or request.user.username}!',
        'pending_orders_count': pending_orders_count,
        'confirmed_orders_count': confirmed_orders_count,
        'preparing_orders_count': preparing_orders_count,
        'recent_reviews_count': recent_reviews_count,
        'actionable_orders': actionable_orders,
        'page_title': 'Staff Dashboard'
    }
    return render(request, 'catering_app/staff_dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_menu_list(request):
    categories = MenuCategory.objects.prefetch_related('items').all()
    context = {
        'categories': categories,
    }
    return render(request, 'catering_app/staff/staff_menu_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_category_create(request):
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu category created successfully.')
            return redirect('catering_app:staff_menu_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MenuCategoryForm()
    context = {
        'form': form,
        'form_title': 'Create New Menu Category'
    }
    return render(request, 'catering_app/staff_category_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_category_update(request, category_id):
    category = get_object_or_404(MenuCategory, id=category_id)
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('catering_app:staff_menu_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MenuCategoryForm(instance=category)
    context = {
        'form': form,
        'form_title': f'Edit Category: {category.name}',
        'category': category
    }
    return render(request, 'catering_app/staff_category_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_category_delete(request, category_id):
    category = get_object_or_404(MenuCategory, id=category_id)
    if request.method == 'POST':
        category_name = category.name
        if category.items.exists(): 
            messages.error(request, f'Cannot delete category "{category_name}" because it contains menu items. Please delete or reassign items first.')
            return redirect('catering_app:staff_menu_list')
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect('catering_app:staff_menu_list')
    
    context = {
        'category': category,
        'page_title': f'Confirm Delete: {category.name}'
    }
    return render(request, 'catering_app/staff_category_confirm_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_menu_item_create(request, category_id):
    category = get_object_or_404(MenuCategory, id=category_id)
    if request.method == 'POST':
     
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save(commit=False)
            menu_item.category = category 
            menu_item.save()
            messages.success(request, f'Menu item "{menu_item.name}" created successfully under {category.name}.')
            return redirect('catering_app:staff_menu_list')
    else:
        form = MenuItemForm(initial={'category': category})
        form.fields['category'].disabled = True 
    return render(request, 'catering_app/staff/staff_menu_item_form.html', {'form': form, 'category': category, 'action': 'Create'})

@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_menu_item_update(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Menu item "{item.name}" updated successfully.')
            return redirect('catering_app:staff_menu_list')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'catering_app/staff/staff_menu_item_form.html', {'form': form, 'item': item, 'category': item.category, 'action': 'Update'})

@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_menu_item_delete(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    category_id = item.category.id
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'Menu item "{item_name}" deleted successfully.')
        return redirect('catering_app:staff_menu_list') 
    return render(request, 'catering_app/staff/staff_menu_item_confirm_delete.html', {'item': item, 'category_id': category_id})

@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_menu_item_add(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() 
            messages.success(request, f'Menu item "{form.cleaned_data["name"]}" created successfully.')
            return redirect('catering_app:staff_menu_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MenuItemForm()
    return render(request, 'catering_app/staff/staff_menu_item_form.html', {
        'form': form, 
        'action': 'Create New', 
        'category': None  
    })

@login_required
@user_passes_test(is_staff_user)
def staff_order_list(request):
    orders = Order.objects.all().order_by('-created_at') 

    context = {
        'orders': orders,
        'page_title': 'Manage Orders'
    }
    return render(request, 'catering_app/staff/staff_order_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__menu_item'), id=order_id)
    
    if request.method == 'POST':
        status_form = OrderStatusUpdateForm(request.POST, instance=order)
        if status_form.is_valid():
            status_form.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}.')
            return redirect('catering_app:staff_order_detail', order_id=order.id) 
        else:
            messages.error(request, 'Failed to update order status. Please correct the errors below.')
    else:
        status_form = OrderStatusUpdateForm(instance=order)

    context = {
        'order': order,
        'status_form': status_form, 
        'page_title': f'Order #{order.id} Details'
    }
    return render(request, 'catering_app/staff/staff_order_detail.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_review_list(request):
    reviews = Review.objects.select_related('order', 'user').all().order_by('-created_at')

    context = {
        'reviews': reviews,
        'page_title': 'Customer Reviews'
    }
    return render(request, 'catering_app/staff/staff_review_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_sales_report(request):
    completed_orders = Order.objects.filter(status='DELIVERED')
    date_filter_form = SalesReportDateFilterForm(request.GET or None)

    start_date_display = None
    end_date_display = None

    if date_filter_form.is_valid():
        start_date = date_filter_form.cleaned_data.get('start_date')
        end_date = date_filter_form.cleaned_data.get('end_date')
        
        start_date_display = start_date
        end_date_display = end_date

        if start_date:
            completed_orders = completed_orders.filter(updated_at__gte=start_date) 
        if end_date:

            completed_orders = completed_orders.filter(updated_at__lte=datetime.datetime.combine(end_date, datetime.time.max))

    total_revenue = 0
    for order in completed_orders:
        total_revenue += order.get_total_cost()

    number_of_orders = completed_orders.count()
    average_order_value = total_revenue / number_of_orders if number_of_orders > 0 else 0

    context = {
        'total_revenue': total_revenue,
        'number_of_orders': number_of_orders,
        'average_order_value': average_order_value,
        'recent_orders': completed_orders.order_by('-updated_at')[:10],
        'page_title': 'Sales Report',
        'date_filter_form': date_filter_form,
        'start_date_display': start_date_display,
        'end_date_display': end_date_display,
    }
    return render(request, 'catering_app/staff/staff_sales_report.html', context)

@login_required
@user_passes_test(is_staff_user)
def staff_user_list(request):

    users = User.objects.filter(is_staff=False).annotate(
        order_count=Count('orders') 
    ).order_by('username')

    context = {
        'users': users,
        'page_title': 'Customer Management'
    }
    return render(request, 'catering_app/staff/staff_user_list.html', context)

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('catering_app:profile_update') # Or to dashboard
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    return render(request, 'catering_app/profile_update.html', {'form': form})
