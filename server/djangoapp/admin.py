from django.contrib import admin
# from .models import related models
from .models import CarMake, CarModel

# Register your models here.

# CarModelInline class
class CarModelInline(admin.StackedInline):
    '''CarModelInline'''
    model = CarModel
    extra = 2
# CarModelAdmin class
class CarModelAdmin(admin.ModelAdmin):
    '''CarModelAdmin'''
    list_display = ['car_make', 'name', 'dealer_id', 'model_type', 'year']
    list_filter = ['model_type', 'car_make', 'dealer_id', 'year',]
    search_fields = ['car_make', 'name']
# CarMakeAdmin class with CarModelInline
class CarMakeAdmin(admin.ModelAdmin):
    '''CarMakeAdmin'''
    list_display = ['name', 'description']
    search_fields = ['name']
    inlines = [CarModelInline]
# Register models here
admin.site.register(CarMake, CarMakeAdmin)
admin.site.register(CarModel, CarModelAdmin)
