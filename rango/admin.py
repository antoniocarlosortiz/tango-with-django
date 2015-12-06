from django.contrib import admin
from rango.models import Category, Page

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    prepopulate_fields = {'slug':('name',)}
    readonly_fields = ('slug',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Page)

from rango.models import UserProfile

admin.site.register(UserProfile)