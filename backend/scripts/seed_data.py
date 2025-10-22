"""
Script para generar datos de prueba
backend/scripts/seed_data.py

Crea:
- 3 categorías de socios
- 20 socios con QR
- 10 pagos registrados
- 15 accesos simulados
- 3 usuarios del sistema
"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from random import randint, choice, uniform

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.usuario import Usuario, RolUsuario
from app.models.miembro import Miembro, Categoria, EstadoMiembro, TipoDocumento
from app.models.pago import Pago, MovimientoCaja, TipoPago, MetodoPago, EstadoPago
from app.models.acceso import Acceso, TipoAcceso, ResultadoAcceso
from app.services.qr_service import QRService
from app.utils.security import hash_password


# ==================== DATOS DE EJEMPLO ====================

NOMBRES = [
    "Juan", "María", "Carlos", "Ana", "Luis", "Laura", "Pedro", "Sofia",
    "Diego", "Valentina", "Miguel", "Camila", "Javier", "Lucía", "Roberto",
    "Martina", "Fernando", "Isabella", "Andrés", "Emma"
]

APELLIDOS = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez", "Ortiz", "Chávez", "Ruiz"
]

LOCALIDADES = [
    "Córdoba", "Villa Carlos Paz", "Río Cuarto", "San Francisco",
    "Villa María", "Alta Gracia", "Jesús María", "La Falda"
]


def crear_categorias(db):
    """Crear categorías de socios"""
    print("\n Creando categorías...")
    
    categorias_data = [
        {
            "nombre": "Titular",
            "descripcion": "Socio titular con todos los beneficios",
            "cuota_base": 5000.0,
            "tiene_cuota_fija": True,
            "caracteristicas": "Acceso completo a todas las instalaciones",
            "modulo_tipo": "generico"
        },
        {
            "nombre": "Adherente",
            "descripcion": "Familiar del socio titular",
            "cuota_base": 3000.0,
            "tiene_cuota_fija": True,
            "caracteristicas": "Acceso con algunas restricciones",
            "modulo_tipo": "generico"
        },
        {
            "nombre": "Cadete",
            "descripcion": "Socio menor de edad",
            "cuota_base": 2000.0,
            "tiene_cuota_fija": True,
            "caracteristicas": "Acceso limitado según edad",
            "modulo_tipo": "generico"
        }
    ]
    
    categorias = []
    for cat_data in categorias_data:
        # Verificar si la categoría ya existe
        existe = db.query(Categoria).filter(Categoria.nombre == cat_data["nombre"]).first()
        if existe:
            print(f"   [WARN]  Categoría '{cat_data['nombre']}' ya existe, omitiendo.")
            categorias.append(existe)
            continue
        
        categoria = Categoria(**cat_data)
        db.add(categoria)
        categorias.append(categoria)
    
    db.commit()
    
    for cat in categorias:
        db.refresh(cat)
        print(f"   [OK] {cat.nombre} - ${cat.cuota_base}")
    
    return categorias


def crear_usuarios(db):
    """Crear usuarios del sistema"""
    print("\n Creando usuarios del sistema...")
    
    usuarios_data = [
        {
            "username": "operador1",
            "email": "operador1@club.com",
            "password": "Operador123!",
            "nombre": "María",
            "apellido": "González",
            "rol": RolUsuario.OPERADOR,
            "telefono": "3515551111"
        },
        {
            "username": "portero1",
            "email": "portero1@club.com",
            "password": "Portero123!",
            "nombre": "Carlos",
            "apellido": "Ramírez",
            "rol": RolUsuario.PORTERO,
            "telefono": "3515552222"
        },
        {
            "username": "tesorero",
            "email": "tesorero@club.com",
            "password": "Tesorero123!",
            "nombre": "Ana",
            "apellido": "Martínez",
            "rol": RolUsuario.ADMINISTRADOR,
            "telefono": "3515553333"
        }
    ]
    
    usuarios = []
    for user_data in usuarios_data:
        # Verificar si ya existe
        existe = db.query(Usuario).filter(
            Usuario.username == user_data["username"]
        ).first()
        
        if existe:
            print(f"   [WARN]  {user_data['username']} ya existe")
            usuarios.append(existe)
            continue
        
        password = user_data.pop("password")
        usuario = Usuario(
            **user_data,
            password_hash=hash_password(password),
            is_active=True,
            is_verified=True
        )
        db.add(usuario)
        usuarios.append(usuario)
        print(f"   [OK] {usuario.username} ({usuario.rol.value})")
    
    db.commit()
    
    for u in usuarios:
        db.refresh(u)
    
    return usuarios


def crear_socios(db, categorias):
    """Crear socios de ejemplo con QR"""
    print("\n Creando socios...")
    
    socios = []
    
    for i in range(20):
        nombre = choice(NOMBRES)
        apellido = choice(APELLIDOS)
        dni = f"{20000000 + randint(0, 10000000)}"
        
        # Generar número de socio
        numero_socio = f"M-{(i+1):05d}"
        
        # Datos aleatorios
        categoria = choice(categorias)
        fecha_nac = date(randint(1960, 2005), randint(1, 12), randint(1, 28))
        localidad = choice(LOCALIDADES)
        
        # Determinar estado (80% activos, 15% morosos, 5% suspendidos)
        rand = randint(1, 100)
        if rand <= 80:
            estado = EstadoMiembro.ACTIVO
            saldo = uniform(0, 1000)
        elif rand <= 95:
            estado = EstadoMiembro.MOROSO
            saldo = -uniform(1000, 5000)
        else:
            estado = EstadoMiembro.SUSPENDIDO
            saldo = -uniform(500, 2000)
        
        # Crear socio (sin QR todavía)
        socio = Miembro(
            numero_miembro=numero_socio,
            tipo_documento=TipoDocumento.DNI,
            numero_documento=dni,
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nac,
            email=f"{nombre.lower()}.{apellido.lower()}@email.com",
            telefono=f"351555{randint(1000, 9999)}",
            celular=f"351555{randint(1000, 9999)}",
            direccion=f"Calle {randint(1, 50)} N° {randint(100, 9999)}",
            localidad=localidad,
            provincia="Córdoba",
            codigo_postal=f"X{randint(5000, 5999)}",
            categoria_id=categoria.id,
            fecha_alta=date.today() - timedelta(days=randint(30, 730)),
            estado=estado,
            saldo_cuenta=saldo,
            modulo_tipo="generico",
            # QR temporal
            qr_code=f"TEMP_{numero_socio}",
            qr_hash=f"TEMP_HASH_{numero_socio}",
            qr_generated_at=datetime.utcnow().isoformat()
        )
        # Verificar si el socio ya existe
        existing_socio = db.query(Miembro).filter(Miembro.numero_miembro == numero_socio).first()
        if existing_socio:
            print(f"   [WARN]  Socio con número '{numero_socio}' ya existe, omitiendo.")
            continue
        
        db.add(socio)
        socios.append(socio)
    
    db.commit()
    
    # Generar QR para cada socio
    print("\n    Generando códigos QR...")
    for socio in socios:
        db.refresh(socio)
        
        # Generar QR
        qr_data = QRService.generar_qr_miembro(
            miembro_id=socio.id,
            numero_documento=socio.numero_documento,
            numero_miembro=socio.numero_miembro,
            nombre_completo=socio.nombre_completo,
            personalizar=True
        )
        
        socio.qr_code = qr_data["qr_code"]
        socio.qr_hash = qr_data["qr_hash"]
        socio.qr_generated_at = qr_data["timestamp"]
    
    db.commit()
    
    for socio in socios:
        db.refresh(socio)
        print(f"   [OK] {socio.numero_miembro} - {socio.nombre_completo} ({socio.estado.value})")
    
    return socios


def crear_pagos(db, socios, usuarios):
    """Crear pagos de ejemplo"""
    print("\n Creando pagos...")
    
    operador = next((u for u in usuarios if u.rol == RolUsuario.OPERADOR), usuarios[0])
    
    pagos = []
    
    # Crear 10 pagos aleatorios
    for i in range(10):
        socio = choice([s for s in socios if s.estado != EstadoMiembro.BAJA])
        
        monto = socio.categoria.cuota_base
        metodo = choice(list(MetodoPago))
        
        # Fecha aleatoria en los últimos 3 meses
        dias_atras = randint(1, 90)
        fecha = date.today() - timedelta(days=dias_atras)
        
        pago = Pago(
            miembro_id=socio.id,
            tipo=TipoPago.CUOTA,
            concepto=f"Cuota {fecha.strftime('%B %Y')}",
            descripcion="Pago de cuota mensual",
            monto=monto,
            descuento=0.0,
            recargo=0.0,
            monto_final=monto,
            metodo_pago=metodo,
            estado=EstadoPago.APROBADO,
            fecha_pago=fecha,
            fecha_periodo=date(fecha.year, fecha.month, 1),
            numero_comprobante=f"REC-{date.today().year}-{(i+1):05d}",
            registrado_por_id=operador.id
        )
        
        db.add(pago)
        pagos.append(pago)
        
        # Actualizar saldo del socio
        socio.saldo_cuenta += monto
        socio.ultima_cuota_pagada = fecha
        
        # Registrar movimiento de caja
        movimiento = MovimientoCaja(
            tipo="ingreso",
            concepto=pago.concepto,
            monto=monto,
            categoria_contable="Cuotas",
            fecha_movimiento=fecha,
            numero_comprobante=pago.numero_comprobante,
            pago_id=pago.id,
            registrado_por_id=operador.id
        )
        db.add(movimiento)
    
    db.commit()
    
    for pago in pagos:
        db.refresh(pago)
        print(f"   [OK] {pago.numero_comprobante} - ${pago.monto_final} ({pago.metodo_pago.value})")
    
    return pagos


def crear_accesos(db, socios, usuarios):
    """Crear registros de acceso"""
    print("\n Creando registros de acceso...")
    
    portero = next((u for u in usuarios if u.rol == RolUsuario.PORTERO), usuarios[0])
    
    accesos = []
    
    # Crear 15 accesos en los últimos 7 días
    for i in range(15):
        socio = choice([s for s in socios if s.estado != EstadoMiembro.BAJA])
        
        # Fecha aleatoria en los últimos 7 días
        dias_atras = randint(0, 7)
        hora = randint(8, 20)
        minuto = randint(0, 59)
        fecha_hora = datetime.now() - timedelta(days=dias_atras, hours=24-hora, minutes=60-minuto)
        
        # Determinar resultado según estado del socio
        if socio.estado == EstadoMiembro.ACTIVO:
            resultado = ResultadoAcceso.PERMITIDO
            mensaje = "Acceso autorizado"
        elif socio.estado == EstadoMiembro.MOROSO:
            resultado = ResultadoAcceso.RECHAZADO
            mensaje = f"Cuota impaga - Deuda: ${abs(socio.saldo_cuenta):.2f}"
        else:
            resultado = ResultadoAcceso.RECHAZADO
            mensaje = "Socio suspendido"
        
        acceso = Acceso(
            miembro_id=socio.id,
            fecha_hora=fecha_hora.isoformat(),
            tipo_acceso=TipoAcceso.QR,
            resultado=resultado,
            ubicacion=choice(["Entrada Principal", "Cancha 1", "Gimnasio", "Pileta"]),
            dispositivo_id=f"DEVICE-{randint(1, 3):03d}",
            qr_code_escaneado=socio.qr_code,
            qr_validacion_exitosa=True,
            mensaje=mensaje,
            registrado_por_id=portero.id,
            estado_miembro_snapshot=socio.estado.value,
            saldo_cuenta_snapshot=socio.saldo_cuenta
        )
        
        db.add(acceso)
        accesos.append(acceso)
    
    db.commit()
    
    for acceso in accesos:
        db.refresh(acceso)
        icono = "[OK]" if acceso.resultado == ResultadoAcceso.PERMITIDO else "[ERROR]"
        print(f"   {icono} Acceso {acceso.resultado.value} - {acceso.mensaje[:40]}")
    
    return accesos


def main():
    """Función principal"""
    print("=" * 60)
    print("  GENERADOR DE DATOS DE PRUEBA")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya hay datos
        from app.models.miembro import Miembro
        count = db.query(Miembro).count()
        
        if count > 0:
            print(f"\n[WARN]  Ya existen {count} socios en la base de datos")
            respuesta = input("¿Deseas agregar más datos de prueba? (si/no): ")
            if respuesta.lower() not in ['si', 's', 'yes', 'y']:
                print("[ERROR] Operación cancelada")
                return
        
        print("\n Iniciando generación de datos...")
        
        # Crear datos
        categorias = crear_categorias(db)
        usuarios = crear_usuarios(db)
        socios = crear_socios(db, categorias)
        pagos = crear_pagos(db, socios, usuarios)
        accesos = crear_accesos(db, socios, usuarios)
        
        print("\n" + "=" * 60)
        print("[OK] DATOS DE PRUEBA CREADOS EXITOSAMENTE")
        print("=" * 60)
        print(f"\n Resumen:")
        print(f"   • Categorías: {len(categorias)}")
        print(f"   • Usuarios: {len(usuarios)}")
        print(f"   • Socios: {len(socios)}")
        print(f"   • Pagos: {len(pagos)}")
        print(f"   • Accesos: {len(accesos)}")
        
        print(f"\n Credenciales de usuarios creados:")
        print(f"   • operador1 / Operador123!")
        print(f"   • portero1 / Portero123!")
        print(f"   • tesorero / Tesorero123!")
        
        print(f"\n Inicia el servidor con:")
        print(f"   uvicorn app.main:app --reload")
        print(f"\n Documentación API:")
        print(f"   http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
