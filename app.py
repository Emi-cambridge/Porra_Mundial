import sqlite3
import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(page_title="Porra Mundial Familiar", page_icon="⚽", layout="centered")

DB_NAME = "porra_mundial.db"

# --- FUNCIONES DE BASE DE DATOS ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea las tablas de forma automática si no existen e inserta datos iniciales."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        nombre TEXT,
                        es_admin INTEGER DEFAULT 0)''')
    
    # Tabla de Partidos
    cursor.execute('''CREATE TABLE IF NOT EXISTS partidos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        equipo1 TEXT,
                        equipo2 TEXT,
                        fecha TEXT,
                        goles1 INTEGER DEFAULT NULL,
                        goles2 INTEGER DEFAULT NULL,
                        jugado INTEGER DEFAULT 0)''')
    
    # Tabla de Apuestas
    cursor.execute('''CREATE TABLE IF NOT EXISTS apuestas (
                        usuario_id INTEGER,
                        partido_id INTEGER,
                        goles1 INTEGER,
                        goles2 INTEGER,
                        PRIMARY KEY (usuario_id, partido_id))''')
    
    # 1. INYECCIÓN AUTOMÁTICA DE FAMILIARES (image_ebb6ce.jpg)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        # Administrador principal
        cursor.execute("INSERT INTO usuarios (username, password, nombre, es_admin) VALUES ('admin', 'admin123', 'Administrador', 1)")
        
        # Lista de la familia extraída de la imagen
        familiares = [
            ('Emi', 'familia2026', 'Emi'),
            ('Laura', 'familia2026', 'Laura'),
            ('nico', 'familia2026', 'Nico'),
            ('Lorenzo', 'familia2026', 'Lorenzo'),
            ('Fatima', 'familia2026', 'Fatima'),
            ('Tamara', 'familia2026', 'Tamara'),
            ('irma', 'familia2026', 'Tía Irma Ortiz'),
            ('miguel', 'familia2026', 'Miguel Felipe'),
            ('sara', 'familia2026', 'Sara María'),
            ('omar', 'familia2026', 'OmaR'),
            ('monica', 'familia2026', 'Monica'),
            ('clara', 'familia2026', 'Tía Clara Inés'),
            ('catis', 'familia2026', 'Catis'),
            ('sebas', 'familia2026', 'Sebas'),
            ('maria_f', 'familia2026', 'Maria F'),
            ('gloria', 'familia2026', 'Tía Gloria')
        ]
        cursor.executemany("INSERT INTO usuarios (username, password, nombre, es_admin) VALUES (?, ?, ?, 0)", familiares)
    
    # 2. INYECCIÓN AUTOMÁTICA DE PARTIDOS DEL MUNDIAL 2026
    cursor.execute("SELECT COUNT(*) FROM partidos")
    if cursor.fetchone()[0] == 0:
        partidos_mundial = [
            # JORNADA 1
            ("México", "Sudáfrica", "Grupo A - 11-Jun"),
            ("Corea del Sur", "República Checa", "Grupo A - 11-Jun"),
            ("Canadá", "Bosnia y Herzegovina", "Grupo B - 12-Jun"),
            ("Estados Unidos", "Paraguay", "Grupo D - 12-Jun"),
            ("Catar", "Suiza", "Grupo B - 13-Jun"),
            ("Brasil", "Marruecos", "Grupo C - 13-Jun"),
            ("Haití", "Escocia", "Grupo C - 13-Jun"),
            ("Australia", "Turquía", "Grupo D - 13-Jun"),
            ("Alemania", "Curazao", "Grupo E - 14-Jun"),
            ("Países Bajos", "Japón", "Grupo F - 14-Jun"),
            ("Costa de Marfil", "Ecuador", "Grupo E - 14-Jun"),
            ("Suecia", "Túnez", "Grupo F - 14-Jun"),
            ("España", "Cabo Verde", "Grupo H - 15-Jun"),
            ("Bélgica", "Egipto", "Grupo G - 15-Jun"),
            ("Arabia Saudita", "Uruguay", "Grupo H - 15-Jun"),
            ("Irán", "Nueva Zelanda", "Grupo G - 15-Jun"),
            ("Francia", "Senegal", "Grupo I - 16-Jun"),
            ("Irak", "Noruega", "Grupo I - 16-Jun"),
            ("Argentina", "Argelia", "Grupo J - 16-Jun"),
            ("Austria", "Jordania", "Grupo J - 16-Jun"),
            ("Portugal", "RD Congo", "Grupo K - 17-Jun"),
            ("Uzbekistán", "Colombia", "Grupo K - 17-Jun"),
            ("Inglaterra", "Croacia", "Grupo L - 17-Jun"),
            ("Ghana", "Panamá", "Grupo L - 17-Jun"),
            
            # JORNADA 2
            ("República Checa", "Sudáfrica", "Grupo A - 18-Jun"),
            ("Suiza", "Bosnia y Herzegovina", "Grupo B - 18-Jun"),
            ("Canadá", "Catar", "Grupo B - 18-Jun"),
            ("México", "Corea del Sur", "Grupo A - 18-Jun"),
            ("Estados Unidos", "Australia", "Grupo D - 19-Jun"),
            ("Escocia", "Marruecos", "Grupo C - 19-Jun"),
            ("Brasil", "Haití", "Grupo C - 19-Jun"),
            ("Turquía", "Paraguay", "Grupo D - 20-Jun"),
            ("Países Bajos", "Suecia", "Grupo F - 20-Jun"),
            ("Alemania", "Costa de Marfil", "Grupo E - 20-Jun"),
            ("Ecuador", "Curazao", "Grupo E - 20-Jun"),
            ("Túnez", "Japón", "Grupo F - 21-Jun"),
            ("España", "Arabia Saudita", "Grupo H - 21-Jun"),
            ("Bélgica", "Irán", "Grupo G - 21-Jun"),
            ("Uruguay", "Cabo Verde", "Grupo H - 21-Jun"),
            ("Nueva Zelanda", "Egipto", "Grupo G - 21-Jun")
        ]
        cursor.executemany("INSERT INTO partidos (equipo1, equipo2, fecha) VALUES (?, ?, ?)", partidos_mundial)
        
    conn.commit()
    conn.close()
# Inicializar Base de Datos inmediatamente al cargar
init_db()

# --- LÓGICA DE PUNTOS Y CLASIFICACIÓN ---
def calcular_clasificacion():
    """Calcula el ranking dinámico sumando los puntos de cada apuesta."""
    conn = get_db_connection()
    usuarios = conn.execute("SELECT id, nombre FROM usuarios WHERE es_admin = 0").fetchall()
    partidos = conn.execute("SELECT id, goles1, goles2 FROM partidos WHERE jugado = 1").fetchall()
    apuestas = conn.execute("SELECT usuario_id, partido_id, goles1, goles2 FROM apuestas").fetchall()
    conn.close()
    
    # Mapear apuestas para búsqueda rápida: (usuario_id, partido_id) -> (goles1, goles2)
    apuestas_map = {(a['usuario_id'], a['partido_id']): (a['goles1'], a['goles2']) for a in apuestas}
    
    ranking = []
    for u in usuarios:
        puntos_totales = 0
        plenos = 0         # 3 puntos
        aciertos_signo = 0 # 1 punto
        
        for p in partidos:
            p_id = p['id']
            g_real1, g_real2 = p['goles1'], p['goles2']
            
            if (u['id'], p_id) in apuestas_map:
                g_bet1, g_bet2 = apuestas_map[(u['id'], p_id)]
                
                # 1. Resultado exacto (Pleno) -> 3 Puntos
                if g_real1 == g_bet1 and g_real2 == g_bet2:
                    puntos_totales += 3
                    plenos += 1
                # 2. Acierto de Ganador o Empate -> 1 Punto
                elif (g_real1 > g_real2 and g_bet1 > g_bet2) or \
                     (g_real1 < g_real2 and g_bet1 < g_bet2) or \
                     (g_real1 == g_real2 and g_bet1 == g_bet2):
                    puntos_totales += 1
                    aciertos_signo += 1
                    
        ranking.append({
            "Familiar": u['nombre'],
            "Puntos Totales": puntos_totales,
            "Plenos (3 pts)": plenos,
            "Aciertos Signo (1 pt)": aciertos_signo
        })
    
    df = pd.DataFrame(ranking)
    if not df.empty:
        df = df.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
        df.index += 1  # La posición empieza en 1
    return df

# --- CONTROL DE SESIÓN (LOGIN) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚽ Polla Mundial 2026")
    st.subheader("Inicia sesión para participar")
    
    with st.form("login_form"):
        username = st.text_input("Usuario").strip().lower()
        password = st.text_input("Contraseña", type="password")
        botón_login = st.form_submit_button("Entrar")
        
        if botón_login:
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password)).fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.session_state.nombre = user['nombre']
                st.session_state.es_admin = user['es_admin']
                st.success(f"¡Bienvenido/a {user['nombre']}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
else:
    # --- MENÚ DE NAVEGACIÓN ---
    st.sidebar.title(f"👋 ¡Hola, {st.session_state.nombre}!")
    
    opciones_menu = ["🏆 Clasificación", "📝 Mis Apuestas"]
    if st.session_state.es_admin == 1:
        opciones_menu.append("⚙️ Panel Administrador")
        
    menu = st.sidebar.radio("Ir a:", opciones_menu)
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    # --- PANTALLA: CLASIFICACIÓN ---
    if menu == "🏆 Clasificación":
        st.title("🏆 Clasificación de la Familia")
        st.write("Aquí puedes ver quién va liderando la porra mundialista.")
        
        tabla_puntos = calcular_clasificacion()
        if not tabla_puntos.empty:
            st.dataframe(tabla_puntos, use_container_width=True)
        else:
            st.info("Aún no hay puntos calculados. ¡Los puntos aparecerán cuando el administrador cierre los primeros partidos!")

    # --- PANTALLA: MIS APUESTAS ---
    elif menu == "📝 Mis Apuestas":
        st.title("📝 Tus Pronósticos")
        st.write("Introduce o modifica tus resultados aquí. Se guardarán automáticamente al pulsar el botón.")
        
        conn = get_db_connection()
        # Partidos activos (que no han terminado)
        partidos = conn.execute("SELECT * FROM partidos WHERE jugado = 0").fetchall()
        # Obtener apuestas previas del usuario actual
        apuestas_usuario = {a['partido_id']: (a['goles1'], a['goles2']) for a in conn.execute("SELECT partido_id, goles1, goles2 FROM apuestas WHERE usuario_id = ?", (st.session_state.user_id,)).fetchall()}
        conn.close()
        
        if not partidos:
            st.info("No hay partidos abiertos para apostar en este momento.")
        else:
            for p in partidos:
                # Contenedor visual moderno para cada partido
                with st.container(border=True):
                    st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                    st.caption(f"📅 {p['fecha']}")
                    
                    # Valores por defecto si ya existía una apuesta previa
                    def_g1, def_g2 = (0, 0)
                    if p['id'] in apuestas_usuario:
                        def_g1, def_g2 = apuestas_usuario[p['id']]
                        st.markdown("<span style='color: green;'>✓ Ya tienes una apuesta registrada para este partido.</span>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 2, 3])
                    with col1:
                        g1 = st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=20, value=def_g1, key=f"g1_{p['id']}")
                    with col2:
                        g2 = st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=20, value=def_g2, key=f"g2_{p['id']}")
                    with col3:
                        st.write("") # Espaciadores
                        st.write("")
                        if st.button("Guardar Pronóstico", key=f"btn_{p['id']}", use_container_width=True):
                            conn = get_db_connection()
                            conn.execute("INSERT OR REPLACE INTO apuestas (usuario_id, partido_id, goles1, goles2) VALUES (?, ?, ?, ?)",
                                         (st.session_state.user_id, p['id'], g1, g2))
                            conn.commit()
                            conn.close()
                            st.success("¡Guardado!")
                            st.rerun()

    # --- PANTALLA: PANEL ADMINISTRADOR ---
    elif menu == "⚙️ Panel Administrador":
        st.title("⚙️ Panel de Control (Admin)")
        
        tab1, tab2, tab3 = st.tabs(["Cerrar Partidos", "Añadir Partidos", "Añadir Familiares"])
        
        # Pestaña 1: Introducir resultados reales
        with tab1:
            st.subheader("Introducir Resultados Reales")
            st.write("Cuando un partido finalice, introduce aquí el resultado definitivo. Al hacerlo, el sistema bloqueará las apuestas para ese partido y recalculará los puntos automáticamente.")
            
            conn = get_db_connection()
            partidos_activos = conn.execute("SELECT * FROM partidos WHERE jugado = 0").fetchall()
            conn.close()
            
            if not partidos_activos:
                st.info("No hay partidos pendientes de cerrar.")
            else:
                for p in partidos_activos:
                    with st.container(border=True):
                        st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                        c1, c2, c3 = st.columns([2, 2, 3])
                        with c1:
                            res1 = st.number_input(f"Resultado {p['equipo1']}", min_value=0, max_value=20, value=0, key=f"res1_{p['id']}")
                        with c2:
                            res2 = st.number_input(f"Resultado {p['equipo2']}", min_value=0, max_value=20, value=0, key=f"res2_{p['id']}")
                        with c3:
                            st.write("")
                            st.write("")
                            if st.button("Finalizar y Calcular Puntos", key=f"fin_{p['id']}", use_container_width=True):
                                conn = get_db_connection()
                                conn.execute("UPDATE partidos SET goles1 = ?, goles2 = ?, jugado = 1 WHERE id = ?", (res1, res2, p['id']))
                                conn.commit()
                                conn.close()
                                st.success("Partido cerrado. ¡Puntos actualizados!")
                                st.rerun()
                                
        # Pestaña 2: Crear nuevos partidos
        with tab2:
            st.subheader("Registrar Nuevo Partido")
            with st.form("nuevo_partido_form"):
                eq1 = st.text_input("Equipo Local (Ej: España)")
                eq2 = st.text_input("Equipo Visitante (Ej: Italia)")
                fecha_partido = st.text_input("Fase / Fecha (Ej: Octavos - 24 Junio)")
                check_partido = st.form_submit_button("Crear Partido")
                
                if check_partido and eq1 and eq2:
                    conn = get_db_connection()
                    conn.execute("INSERT INTO partidos (equipo1, equipo2, fecha) VALUES (?, ?, ?)", (eq1, eq2, fecha_partido))
                    conn.commit()
                    conn.close()
                    st.success(f"Partido {eq1} vs {eq2} añadido con éxito.")
                    st.rerun()
                    
        # Pestaña 3: Crear cuentas a familiares
        with tab3:
            st.subheader("Registrar un Miembro de la Familia")
            st.write("Crea las cuentas aquí para que tu familia no necesite registrarse públicamente.")
            with st.form("nuevo_usuario_form"):
                nuevo_user = st.text_input("Usuario de Login (Ej: tio_juan)").strip().lower()
                nueva_pass = st.text_input("Contraseña de Login (Ej: juan2026)")
                nuevo_nombre = st.text_input("Nombre Visible (Ej: Tío Juan)")
                check_usuario = st.form_submit_button("Crear Cuenta Familiar")
                
                if check_usuario and nuevo_user and nueva_pass and nuevo_nombre:
                    try:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO usuarios (username, password, nombre, es_admin) VALUES (?, ?, ?, 0)", 
                                     (nuevo_user, nueva_pass, nuevo_nombre))
                        conn.commit()
                        conn.close()
                        st.success(f"¡Cuenta de {nuevo_nombre} creada!")
                    except sqlite3.IntegrityError:
                        st.error("Ese nombre de usuario ya existe.")
