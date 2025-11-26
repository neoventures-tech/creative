from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from authentication.models import User

class CustomUserAdmin(UserAdmin):
    list_display = ['username','first_name','last_name',]
    search_fields = ('username',)
    ordering = ('-id',)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions



# admin.site.unregister(Group)
admin.site.register(User,CustomUserAdmin)
