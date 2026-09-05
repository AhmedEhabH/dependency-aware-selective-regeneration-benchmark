from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsProjectMember(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, _obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff
