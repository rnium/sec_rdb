from rest_framework.permissions import BasePermission

class IsCampusAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user is not None and hasattr(request.user, 'adminaccount'):
            return True
        else:
            return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.adminaccount.is_super_admin:
            return True
        else:
            return (request.user.adminaccount.dept.name == obj.dept.name)
        
class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (hasattr(request.user, 'adminaccount') and request.user.adminaccount.is_super_admin)