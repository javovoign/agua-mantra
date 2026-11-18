from django.contrib.auth.decorators import user_passes_test

def es_administrador(user):
    return user.groups.filter(name='Administrador').exists()

def es_chofer(user):
    return user.groups.filter(name='Chofer').exists()

# Uso en vistas:
# @user_passes_test(es_administrador)
# def editar_cliente(request, cliente_id):
#     ...