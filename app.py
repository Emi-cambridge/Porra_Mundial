import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de la página web
st.set_page_config(page_title="Porra Mundial Familiar", page_icon="⚽", layout="centered")

# --- CONEXIÓN OFICIAL A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_tabla(pestana):
    """Lee datos en tiempo real de una pestaña de Google Sheets."""
    return conn.read(worksheet=pestana, ttl=0)

# --- DICCIONARIO DE ASIGNACIÓN DE PAÍSES Y BANDERAS ---
BANDERAS_FAMILIA = {
    'admin': "🛠️ Admin (Organizador)",
    'emi': "🇪🇸 España",
    'laura': "🇦🇷 Argentina",
    'nico': "🇧🇷 Brasil",
    'fatima': "🇫🇷 Francia",
    'tamara': "🇩🇪 Alemania",
    'miguel': "🇮🇹 Italia",
    'monica': "🇬🇧 Inglaterra",
    'clara': "🇧🇪 Bélgica",
    'catis': "🇳🇱 Países Bajos",
    'sebas': "🇺🇸 Estados Unidos",
    'gloria': "🇲🇦 Marruecos",
    'mafe': "🇨🇴 Colombia",
    'javivi': "🇺🇾 Uruguay",
    'jaime': "🇲🇽 México",
    'cristina': "🇨🇱 Chile",
    'andrea': "🇵🇹 Portugal",
    'claudia': "🇯🇵 Japón",
    'gerardo': "🇨🇦 Canadá"
}

# --- LÓGICA DE PUNTOS Y CLASIFICACIÓN ---
def calcular_clasificacion():
    """Calcula el ranking dinámico leyendo directamente de Google Sheets."""
    df_usuarios = leer_tabla("usuarios")
    df_partidos = leer_tabla("partidos")
    df_apuestas = leer_tabla("apuestas")
    
    # Filtrar usuarios que no son admin
    usuarios = df_usuarios[df_usuarios['es_admin'] == 0]
    # Partidos que ya se jugaron
    partidos_jugados = df_partidos[df_partidos['jugado'] == 1]
    
    # Mapear apuestas para búsqueda rápida: (usuario_id, partido_id) -> (goles1, goles2)
    apuestas_map = {}
    if not df_apuestas.empty:
        for _, row in df_apuestas.iterrows():
            apuestas_map[(int(row['usuario_id']), int(row['partido_id']))] = (int(row['goles1']), int(row['goles2']))
            
    ranking = []
    for _, u in usuarios.iterrows():
        puntos_totales = 0
        plenos = 0         
        aciertos_signo = 0 
        u_id = int(u['id'])
        
        for _, p in partidos_jugados.iterrows():
            p_id = int(p['id'])
            g_real1, g_real2 = int(p['goles1']), int(p['goles2'])
            
            if (u_id, p_id) in apuestas_map:
                g_bet1, g_bet2 = apuestas_map[(u_id, p_id)]
                
                # Resultado exacto (Pleno)
                if g_real1 == g_bet1 and g_real2 == g_bet2:
                    puntos_totales += 3
                    plenos += 1
                # Ganador o empate (Signo)
                elif (g_real1 > g_real2 and g_bet1 > g_bet2) or \
                     (g_real1 < g_real2 and g_bet1 < g_bet2) or \
                     (g_real1 == g_real2 and g_bet1 == g_bet2):
                    puntos_totales += 1
                    aciertos_signo += 1
        
        seleccion = BANDERAS_FAMILIA.get(u['username'], "🏳️ Sin País")
                    
        ranking.append({
            "Familiar": u['nombre'],
            "Selección Asignada": seleccion,
            "Puntos Totales": puntos_totales,
            "Plenos (3 pts)": plenos,
            "Aciertos Signo (1 pt)": aciertos_signo
        })
    
    df = pd.DataFrame(ranking)
    if not df.empty:
        df = df.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
        df.index += 1  
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
            df_usuarios = leer_tabla("usuarios")
            # Buscar coincidencia exacta en el DataFrame de Google Sheets
            user_row = df_usuarios[(df_usuarios['username'] == username) & (df_usuarios['password'].astype(str) == str(password))]
            
            if not user_row.empty:
                user = user_row.iloc[0]
                st.session_state.logged_in = True
                st.session_state.user_id = int(user['id'])
                st.session_state.username = user['username']
                st.session_state.nombre = user['nombre']
                st.session_state.es_admin = int(user['es_admin'])
                st.success(f"¡Bienvenido/a {user['nombre']}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
else:
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
        st.write("Introduce o modifica tus resultados aquí. Se guardarán directamente en Google Sheets.")
        
        df_partidos = leer_tabla("partidos")
        df_apuestas = leer_tabla("apuestas")
        
        # Partidos activos (jugado == 0)
        partidos_activos = df_partidos[df_partidos['jugado'] == 0]
        
        # Buscar apuestas existentes del usuario
        apuestas_usuario = {}
        if not df_apuestas.empty:
            df_u_apuestas = df_apuestas[df_apuestas['usuario_id'] == st.session_state.user_id]
            for _, row in df_u_apuestas.iterrows():
                apuestas_usuario[int(row['partido_id'])] = (int(row['goles1']), int(row['goles2']))
        
        if partidos_activos.empty:
            st.info("No hay partidos abiertos para apostar en este momento.")
        else:
            for _, p in partidos_activos.iterrows():
                p_id = int(p['id'])
                with st.container(border=True):
                    st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                    st.caption(f"📅 {p['fecha']}")
                    
                    def_g1, def_g2 = 0, 0
                    if p_id in apuestas_usuario:
                        def_g1, def_g2 = apuestas_usuario[p_id]
                        st.markdown("<span style='color: green;'>✓ Ya tienes una apuesta registrada para este partido.</span>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 2, 3])
                    with col1:
                        g1 = st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=20, value=def_g1, key=f"g1_{p_id}")
                    with col2:
                        g2 = st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=20, value=def_g2, key=f"g2_{p_id}")
                    with col3:
                        st.write("")
                        st.write("")
                        if st.button("Guardar Pronóstico", key=f"btn_{p_id}", use_container_width=True):
                            df_apuestas_completo = leer_tabla("apuestas")
                            
                            # Buscar si ya existía la fila para pisarla o añadirla nueva
                            fila_existente = df_apuestas_completo[(df_apuestas_completo['usuario_id'] == st.session_state.user_id) & (df_apuestas_completo['partido_id'] == p_id)]
                            
                            if not fila_existente.empty:
                                df_apuestas_completo.loc[fila_existente.index, ['goles1', 'goles2']] = [g1, g2]
                            else:
                                nueva_fila = pd.DataFrame([{"usuario_id": st.session_state.user_id, "partido_id": p_id, "goles1": g1, "goles2": g2}])
                                df_apuestas_completo = pd.concat([df_apuestas_completo, nueva_fila], ignore_index=True)
                            
                            conn.update(worksheet="apuestas", data=df_apuestas_completo)
                            st.success("¡Guardado!")
                            st.rerun()

    # --- PANTALLA: PANEL ADMINISTRADOR ---
    elif menu == "⚙️ Panel Administrador":
        st.title("⚙️ Panel de Control (Admin)")
        tab1, tab2, tab3 = st.tabs(["Cerrar Partidos", "Añadir Partidos", "Añadir Familiares"])
        
        with tab1:
            st.subheader("Introducir Resultados Reales")
            df_partidos = leer_tabla("partidos")
            partidos_activos = df_partidos[df_partidos['jugado'] == 0]
            
            if partidos_activos.empty:
                st.info("No hay partidos pendientes de cerrar.")
            else:
                for _, p in partidos_activos.iterrows():
                    p_id = int(p['id'])
                    with st.container(border=True):
                        st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                        c1, c2, c3 = st.columns([2, 2, 3])
                        with c1:
                            res1 = st.number_input(f"Resultado {p['equipo1']}", min_value=0, max_value=20, value=0, key=f"res1_{p_id}")
                        with c2:
                            res2 = st.number_input(f"Resultado {p['equipo2']}", min_value=0, max_value=20, value=0, key=f"res2_{p_id}")
                        with c3:
                            st.write("")
                            st.write("")
                            if st.button("Finalizar y Calcular Puntos", key=f"fin_{p_id}", use_container_width=True):
                                df_partidos_completo = leer_tabla("partidos")
                                df_partidos_completo.loc[df_partidos_completo['id'] == p_id, ['goles1', 'goles2', 'jugado']] = [res1, res2, 1]
                                conn.update(worksheet="partidos", data=df_partidos_completo)
                                st.success("Partido cerrado en Google Sheets.")
                                st.rerun()
                                
        with tab2:
            st.subheader("Registrar Nuevo Partido")
            with st.form("nuevo_partido_form"):
                eq1 = st.text_input("Equipo Local (Ej: España)")
                eq2 = st.text_input("Equipo Visitante (Ej: Italia)")
                fecha_partido = st.text_input("Fase / Fecha (Ej: Octavos - 24 Junio)")
                check_partido = st.form_submit_button("Crear Partido")
                
                if check_partido and eq1 and eq2:
                    df_partidos_completo = leer_tabla("partidos")
                    nuevo_id = int(df_partidos_completo['id'].max() + 1) if not df_partidos_completo.empty else 1
                    nueva_fila = pd.DataFrame([{"id": nuevo_id, "equipo1": eq1, "equipo2": eq2, "fecha": fecha_partido, "goles1": "", "goles2": "", "jugado": 0}])
                    df_partidos_completo = pd.concat([df_partidos_completo, nueva_fila], ignore_index=True)
                    conn.update(worksheet="partidos", data=df_partidos_completo)
                    st.success("Partido añadido.")
                    st.rerun()
                    
        with tab3:
            st.subheader("Registrar un Miembro de la Familia")
            with st.form("nuevo_usuario_form"):
                nuevo_user = st.text_input("Usuario de Login (Ej: tio_juan)").strip().lower()
                nueva_pass = st.text_input("Contraseña de Login")
                nuevo_nombre = st.text_input("Nombre Visible")
                check_usuario = st.form_submit_button("Crear Cuenta Familiar")
                
                if check_usuario and nuevo_user and nueva_pass and nuevo_nombre:
                    df_usuarios_completo = leer_tabla("usuarios")
                    if nuevo_user in df_usuarios_completo['username'].values:
                        st.error("Ese usuario ya existe.")
                    else:
                        nuevo_id = int(df_usuarios_completo['id'].max() + 1)
                        nueva_fila = pd.DataFrame([{"id": nuevo_id, "username": nuevo_user, "password": nueva_pass, "nombre": nuevo_nombre, "es_admin": 0}])
                        df_usuarios_completo = pd.concat([df_usuarios_completo, nueva_fila], ignore_index=True)
                        conn.update(worksheet="usuarios", data=df_usuarios_completo)
                        st.success(f"¡Cuenta de {nuevo_nombre} guardada en Google Sheets!")
                        st.rerun()
