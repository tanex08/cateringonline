from django.contrib import admin
from .models import MenuCategory, MenuItem, Order, OrderItem, Review
from django.db.models import Count, Avg # Import Count and Avg

# Register your models here.
admin.site.register(MenuCategory)
admin.site.register(MenuItem)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['menu_item']
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'delivery_address', 'scheduled_datetime', 'number_of_guests', 'status', 'created_at', 'get_total_cost']
    list_filter = ['status', 'created_at', 'scheduled_datetime']
    search_fields = ['id', 'user__username', 'delivery_address']
    inlines = [OrderItemInline]

    def get_total_cost(self, obj):
        return obj.get_total_cost()
    get_total_cost.short_description = 'Total Cost'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'rating', 'comment_summary', 'created_at')
    list_filter = ('rating', 'created_at', 'user')
    search_fields = ('order__id', 'user__username', 'comment')
    readonly_fields = ('order', 'user', 'created_at')

    def comment_summary(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return "No comment"
    comment_summary.short_description = 'Comment'

    def changelist_view(self, request, extra_context=None):
    
        response = super().changelist_view(request, extra_context=extra_context)
        
      
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response 

      
        metrics = {
            'total_reviews': qs.count(),
            'average_rating': qs.aggregate(Avg('rating'))['rating__avg'],
        }
        
     
        rating_distribution = qs.values('rating').annotate(count=Count('rating')).order_by('-rating')
        
       
        extra_context = extra_context or {}
        extra_context['review_metrics'] = metrics
        extra_context['rating_distribution'] = [{
            'rating': entry['rating'],
            'count': entry['count'],
            'percentage': (entry['count'] / metrics['total_reviews'] * 100) if metrics['total_reviews'] else 0
        } for entry in rating_distribution]
        
        response.context_data.update(extra_context)
        return response

