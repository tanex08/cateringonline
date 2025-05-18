from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, Review, MenuCategory, MenuItem
import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='First Name', max_length=150, required=True)
    last_name = forms.CharField(label='Last Name', max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use. Please use a different one.")
        return email

class CartAddItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, 
        initial=1, 
        widget=forms.NumberInput(attrs={'class': 'w-16 px-2 py-1 text-center border-gray-300 rounded-md shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})
    )
    update = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

class OrderCreateForm(forms.ModelForm):
    scheduled_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input w-full rounded-md shadow-sm'}),
    )
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea w-full rounded-md shadow-sm', 'placeholder': 'Full address including street, city, postal code'})
    )
    number_of_guests = forms.IntegerField(
        min_value=1, 
        initial=1, 
        widget=forms.NumberInput(attrs={'class': 'form-input w-full rounded-md shadow-sm'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea w-full rounded-md shadow-sm', 'placeholder': 'Any special requests or notes for your order?'}),
        required=False
    )

    class Meta:
        model = Order
        fields = ['delivery_address', 'scheduled_datetime', 'number_of_guests', 'notes']

    def clean_scheduled_datetime(self):
        dt = self.cleaned_data.get('scheduled_datetime')
        if dt:
            if dt < datetime.datetime.now(dt.tzinfo) + datetime.timedelta(hours=24):
                raise forms.ValidationError("Reservation must be at least 24 hours in advance.")
        return dt

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=Review.RATING_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'flex items-center space-x-2'}), 
        label="Your Rating"
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea w-full rounded-md shadow-sm mt-2', 'placeholder': 'Tell us about your experience...'}),
        required=False,
        label="Your Comments (Optional)"
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']

# Forms for Staff Menu Management
class MenuCategoryForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input w-full rounded-md shadow-sm'}))
    # Add description if you add it to the model later
    class Meta:
        model = MenuCategory
        fields = ['name'] # Add 'description' if applicable

class MenuItemForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}))
    price = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}))
    category = forms.ModelChoiceField(
        queryset=MenuCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})
    )
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}))
    is_available = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-offset-0 focus:ring-indigo-200 focus:ring-opacity-50'}))

    class Meta:
        model = MenuItem
        fields = ['name', 'category', 'description', 'price', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'price': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'category': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'image': forms.ClearableFileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-offset-0 focus:ring-indigo-200 focus:ring-opacity-50'}),
        }

class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})
        }

class SalesReportDateFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input rounded-md shadow-sm border-gray-300 focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")
        return cleaned_data

class UserProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='First Name', max_length=150, required=False)
    last_name = forms.CharField(label='Last Name', max_length=150, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if the email is being changed to one that already exists for another user
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use by another account.")
        return email