from django.urls import path
from . import views

urlpatterns = [
    # Público
    path('', views.index, name='index'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Panel admin
    path('panel/', views.panel, name='panel'),

    # ⭐ NUEVA RUTA: Asignar Choferes
    path('panel/asignar-choferes/', views.asignar_choferes, name='asignar_choferes'),
    
    # Webpay
    path('webpay/crear/', views.webpay_crear, name='webpay_crear'),
    path('pedidos/webpay/retorno/', views.webpay_retorno, name='webpay_retorno'),
    
    # Rutas (admin y chofer)
    path('rutas/', views.rutas, name='rutas'),
    
    # Inventario (solo admin)
    path('inventario/', views.inventario, name='inventario'),
]