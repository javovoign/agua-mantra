# ============================================================
# IMPORTS
# ============================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from functools import wraps
from .models import Cliente, Pedido, Inventario
from .services.webpay import WebpayService
from django.contrib.auth.models import User, Group

# ============================================================
# DECORADOR PERSONALIZADO
# ============================================================
def solo_administrador(view_func):
    """
    Decorador que permite el acceso solo a usuarios del grupo 'Administrador'
    o superusuarios. El resto es redirigido a rutas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificamos si es superusuario O si pertenece al grupo Administrador
        if not (request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()):
            messages.warning(request, 'No tienes permiso para acceder a esa sección')
            return redirect('rutas')
            
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================
# VISTA PÚBLICA: FORMULARIO DE PEDIDOS
# ============================================================
def index(request):
    """
    Página pública con el formulario de pedidos.
    """
    if request.method == 'POST':
        # 1. Obtenemos la cantidad del formulario
        cantidad_raw = request.POST.get('cantidad', '')
        
        # 2. Intentamos convertirla a entero de forma segura
        try:
            cantidad = int(cantidad_raw)
        except ValueError:
            cantidad = 0 # Si no es un número, la forzamos a 0 para que falle la validación
            
        # 3. Validamos el rango permitido (1 a 50)
        if cantidad < 1 or cantidad > 50:
            messages.error(request, 'Cantidad inválida. Debes pedir entre 1 y 50 bidones.')
            return redirect('index')
            
        # 4. Si todo está bien, guardamos en sesión
        request.session['pedido_pendiente'] = {
            'nombre': request.POST.get('nombre'),
            'telefono': request.POST.get('telefono'),
            'direccion': request.POST.get('direccion'),
            'cantidad': cantidad,
        }
        return redirect('webpay_crear')
    
    return render(request, 'pedidos/index.html')


# ============================================================
# LOGIN Y LOGOUT
# ============================================================
def login_view(request):
    """Página de login para administradores y choferes."""
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Chofer').exists():
            return redirect('rutas')
        return redirect('panel')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Chofer').exists():
                return redirect('rutas')
            return redirect('panel')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'pedidos/login.html')


def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('index')


# ============================================================
# WEBPAY: CREAR Y CONFIRMAR
# ============================================================
def webpay_crear(request):
    """RF02: Redirige al cliente a Webpay."""
    datos = request.session.get('pedido_pendiente')
    if not datos:
        messages.error(request, 'No hay pedido pendiente. Por favor completa el formulario.')
        return redirect('index')
    
    total = datos['cantidad'] * 5000
    buy_order = request.session.session_key[:20]
    
    service = WebpayService()
    return_url = request.build_absolute_uri('/pedidos/webpay/retorno/')
    
    response = service.crear_transaccion(
        pedido_id=buy_order,
        monto=total,
        return_url=return_url
    )
    
    request.session['webpay_token'] = response['token']
    request.session['webpay_buy_order'] = buy_order
    
    return redirect(f"{response['url']}?token_ws={response['token']}")


def webpay_retorno(request):
    """Confirma el pago y crea el pedido SOLO si fue exitoso."""
    token = request.GET.get('token_ws')
    
    if not token:
        messages.error(request, 'Token de pago no recibido')
        return redirect('index')
    
    service = WebpayService()
    response = service.confirmar_transaccion(token)
    
    if response['status'] == 'AUTHORIZED':
        datos = request.session.get('pedido_pendiente')
        if not datos:
            messages.error(request, 'No hay datos de pedido en la sesión')
            return redirect('index')
        
        cliente, creado = Cliente.objects.get_or_create(
            telefono=datos['telefono'],
            defaults={'nombre': datos['nombre'], 'direccion': datos['direccion']}
        )
        if not creado:
            cliente.nombre = datos['nombre']
            cliente.direccion = datos['direccion']
            cliente.save()
        
        pedido = Pedido.objects.create(
            cliente=cliente,
            cantidad=datos['cantidad'],
            total=datos['cantidad'] * 5000,
            estado='PAGADO',
            token_webpay=token
        )
        
        request.session.pop('pedido_pendiente', None)
        request.session.pop('webpay_token', None)
        request.session.pop('webpay_buy_order', None)
        
        messages.success(request, f'¡Pago exitoso! Pedido #{pedido.id} confirmado.')
    else:
        messages.error(request, 'El pago fue rechazado. Intenta nuevamente.')
    
    return redirect('index')


# ============================================================
# PANEL DE ADMINISTRACIÓN (solo admin)
# ============================================================
@solo_administrador
def panel(request):
    """Panel principal del administrador."""
    total_pedidos = Pedido.objects.count()
    pedidos_pagados = Pedido.objects.filter(estado='PAGADO').count()
    pedidos_pendientes = Pedido.objects.filter(estado='PENDIENTE_PAGO').count()
    pedidos_entregados = Pedido.objects.filter(estado='ENTREGADO').count()
    
    ultimos_pedidos = Pedido.objects.select_related('cliente').order_by('-creado_en')[:10]
    
    context = {
        'total_pedidos': total_pedidos,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_entregados': pedidos_entregados,
        'ultimos_pedidos': ultimos_pedidos,
    }
    return render(request, 'pedidos/panel.html', context)


# ============================================================
# INVENTARIO (solo admin)
# ============================================================
@solo_administrador
def inventario(request):
    """RF07: Monitorear stock y generar alertas."""
    items = Inventario.objects.all()
    
    alertas = []
    total_botellones = 0
    items_data = []
    
    for item in items:
        total_botellones += item.cantidad
        
        if item.umbral_critico and item.umbral_critico > 0:
            porcentaje = int((item.cantidad / item.umbral_critico) * 100)
        else:
            porcentaje = 100
        
        porcentaje_visual = min(porcentaje, 100)
        es_critico = item.cantidad < item.umbral_critico
        
        items_data.append({
            'id': item.id,
            'tipo': item.tipo,
            'tipo_display': item.get_tipo_display(),
            'cantidad': item.cantidad,
            'umbral_critico': item.umbral_critico,
            'porcentaje': porcentaje_visual,
            'es_critico': es_critico,
        })
        
        if es_critico:
            alertas.append({
                'tipo': item.get_tipo_display(),
                'cantidad': item.cantidad,
                'umbral': item.umbral_critico,
            })
    
    context = {
        'items': items_data,
        'alertas': alertas,
        'total_botellones': total_botellones,
    }
    return render(request, 'pedidos/inventario.html', context)


# ============================================================
# RUTAS (admin y chofer)
# ============================================================
@login_required(login_url='login')
def rutas(request):
    """HU04: Simulación de rutas de despacho."""
    pedidos_pendientes = Pedido.objects.filter(estado='PAGADO').select_related('cliente')
    
    pedidos_data = [
        {
            'id': p.id,
            'nombre': p.cliente.nombre,
            'direccion': p.cliente.direccion,
            'cantidad': p.cantidad,
        }
        for p in pedidos_pendientes
    ]
    
    context = {
        'pedidos_json': pedidos_data,
    }
    return render(request, 'pedidos/rutas.html', context)

@solo_administrador
def asignar_choferes(request):
    """
    CRUD para asignar choferes a los pedidos.
    """
    pedidos = Pedido.objects.select_related('cliente', 'chofer_asignado').order_by('-creado_en')
    
    # Buscar todos los usuarios que pertenezcan al grupo Chofer de forma directa
    choferes = User.objects.filter(groups__name='Chofer').distinct()

    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        chofer_id = request.POST.get('chofer_id')
        
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        if chofer_id:
            chofer = get_object_or_404(User, id=chofer_id)
            pedido.chofer_asignado = chofer
            messages.success(request, f'Chofer {chofer.username} asignado al pedido #{pedido.id}')
        else:
            pedido.chofer_asignado = None
            messages.info(request, f'Chofer removido del pedido #{pedido.id}')
        
        pedido.save()
        return redirect('asignar_choferes')

    context = {
        'pedidos': pedidos,
        'choferes': choferes,
    }
    return render(request, 'pedidos/asignar_choferes.html', context)