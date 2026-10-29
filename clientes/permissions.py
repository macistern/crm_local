from django.contrib.auth.decorators import user_passes_test


def administrator_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="Administradores").exists()),
        login_url="login",
    )(view_func)
