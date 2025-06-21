from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed to any request.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the job.
        return obj.client == request.user

class IsJobOwner(permissions.BasePermission):
    """
    Custom permission to only allow the owner of a job to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user

class IsProposalOwner(permissions.BasePermission):
    """
    Custom permission to only allow the owner of a proposal to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.freelancer == request.user or obj.job.client == request.user

class IsClient(permissions.BasePermission):
    """
    Custom permission to only allow clients to perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_client

class IsFreelancer(permissions.BasePermission):
    """
    Custom permission to only allow freelancers to perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_freelancer
