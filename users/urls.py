# urls.py
from django.urls import path
from . import views


from .views import CurrentUserView, UserListView,FournisseurListView 

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("admin/create-user/", views.create_user_view, name="create_user"),
    path("admin/assign-roles/", views.assign_roles_view, name="assign_roles"),
    path("admin/users/", views.list_users_view, name="list_users"),
    path("admin/groups/", views.list_groups_view, name="list_groups"),
    path(
        "admin/delete-user/<int:user_id>/", views.delete_user_view, name="delete_user"
    ),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users-f/", FournisseurListView .as_view(), name="user-f"),
]
