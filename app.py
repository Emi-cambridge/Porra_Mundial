import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de la página web
st.set_page_config(page_title="Porra Mundial Familiar", page_icon="⚽", layout="centered")

# --- CONEXIÓN OFICIAL Y ENCRIPTADA A GOOGLE SHEETS ---
# Utiliza las credenciales de Secrets. Nadie más que el servidor puede ver los datos.
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_tabla(pestana):
    """Lee datos en tiempo real de forma segura sin almacenamiento en caché."""
    return conn.read(worksheet=pestana, ttl=0)

# --- DICCIONARIO DE ASIGNACIÓN DE PAÍSES Y BANDERAS ---
BANDERAS_FAMILIA = {
    'admin': "🛠️ Admin (Organizador)",
    'emi': "🇪🇸 España",
    'laura': "🇦🇷 Argentina",
    'nico': "🇧🇷 Brasil",
    'lorenzo': "🇮🇹 Italia",
    'fatima': "🇫🇷 Francia",
    'tamara': "🇩🇪 Alemania",
    'irma': "🇲🇽 México",
    'miguel': "🇨🇴 Colombia",
    'sara': "🇵🇹 Portugal",
    'omar': "🇲🇦 Marruecos",
    'monica': "🇬🇧 Inglaterra",
    'clara': "🇧🇪 Bélgica",
    'catis': "🇳🇱 Países Bajos",
    'sebas': "🇺🇸 Estados Unidos",
    'maria_f': "🇺🇾 Uruguay",
    'gloria': "🇨🇱 Chile",
    'mafe': "🇪🇨 Ecuador",
    'javivi': "🇯🇵 Japón",
    'jaime': "🇨🇦 Canadá",
    'cristina': "🇭🇷 Croacia",
    'andrea': "🇨🇭 Suiza",
    'claudia': "🇰🇷 Corea del Sur",
    'gerardo': "🇻🇪 Venezuela"
}

# --- LÓGICA DE PUNTOS Y CLASIFICACIÓN ---
def calcular_clasificacion():
    """Calcula el ranking dinámico leyendo directamente de Google Sheets."""
    df_usuarios = leer_tabla("usuarios")
    df_partidos = leer_tabla("partidos")
    df_apuestas = leer_tabla("apuestas")
    
    if df_usuarios.empty or df_partidos.empty:
        return pd.DataFrame()
        
    usuarios = df_usuarios[df_usuarios['es_admin'] == 0]
    partidos_jugados = df_partidos[df_partidos['jugado'] == 1]
    
    apuestas_map = {}
    if not df_apuestas.empty:
        for _, row in df_apuestas.iterrows():
            try:
                apuestas_map[(int(row['usuario_id']), int(row['partido_id']))] = (int(row['goles1']), int(row['goles2']))
            except:
                continue
            
    ranking = []
    for _, u in usuarios.iterrows():
        puntos_totales = 0
        plenos = 0         
        aciertos_signo = 0 
        u_id = int(u['id'])
        
        for _, p in partidos_jugados.iterrows():
            p_id = int(p['id'])
            try:
                g_real1, g_real2 = int(p['goles1']), int(p['goles2'])
                if (u_id, p_id) in apuestas_map:
                    g_bet1, g_bet2 = apuestas_map[(u_id, p_id)]
                    if g_real1 == g_bet1 and g_real2 == g_bet2:
                        puntos_totales += 3
                        plenos += 1
                    elif (g_real1 > g_real2 and g_bet1 > g_bet2) or \
                         (g_real1 < g_real2 and g_bet1 < g_bet2) or \
                         (g_real1 == g_real2 and g_bet1 == g_bet2):
                        puntos_totales += 1
                        aciertos_signo += 1
            except:
                continue
        
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
            if not df_usuarios.empty:
                df_usuarios.columns = df_usuarios.columns.str.strip().str.lower()
                user_row = df_usuarios[(df_usuarios['username'].astype(str).str.strip().str.lower() == username) & 
                                       (df_usuarios['password'].astype(str).str.strip() == str(password).strip())]
                
                if not user_row.empty:
                    user = user_row.iloc[0]
                    st.session_state.logged_in = True
                    st.session_state.user_id = int(user['id'])
                    st.session_state.username = str(user['username'])
                    st.session_state.nombre = str(user['nombre'])
                    st.session_state.es_admin = int(user['es_admin'])
                    st.success(f"¡Bienvenido/a {user['nombre']}!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            else:
                st.error("Error al conectar de forma segura con Google Sheets.")
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
        st.write("Aquí puedes ver quién va liderando la porra mundialista en tiempo real.")
        
        tabla_puntos = calcular_clasificacion()
        if not tabla_puntos.empty:
            st.dataframe(tabla_puntos, use_container_width=True)
        else:
            st.info("Aún no hay puntos calculados. ¡Aparecerán cuando el administrador cierre los primeros partidos!")

# --- PANTALLA: MIS APUESTAS ---
    elif menu == "📝 Mis Apuestas":
        st.title("📝 Tus Pronósticos")
        st.write("Introduce tus resultados y haz clic en **Guardar Apuesta**. Recuerda que el plazo máximo es el día anterior a cada partido.")
        
        df_partidos = leer_tabla("partidos")
        df_apuestas = leer_tabla("apuestas")
        
        if df_partidos.empty:
            st.warning("No se ha podido cargar el calendario de partidos.")
        else:
            partidos_activos = df_partidos[df_partidos['jugado'] == 0]
            
            # Mapear apuestas del usuario activo para mostrarlas en pantalla si ya existen
            apuestas_usuario = {}
            if not df_apuestas.empty:
                df_apuestas.columns = df_apuestas.columns.str.strip().str.lower()
                df_u_apuestas = df_apuestas[df_apuestas['usuario_id'].astype(int) == st.session_state.user_id]
                for _, row in df_u_apuestas.iterrows():
                    try:
                        apuestas_usuario[int(row['partido_id'])] = (int(row['goles1']), int(row['goles2']))
                    except:
                        continue
            
            if partidos_activos.empty:
                st.info("No hay partidos abiertos para apostar en este momento.")
            else:
                # Obtener la fecha actual del servidor (Formato: AAAA-MM-DD)
                import datetime
                hoy = datetime.date.today()
                
                for _, p in partidos_activos.iterrows():
                    p_id = int(p['id'])
                    
                    # Verificar si la columna fecha_limite existe en el Excel, si no, por defecto permite apostar
                    bloqueado_por_fecha = False
                    if 'fecha_limite' in p and pd.notna(p['fecha_limite']):
                        try:
                            # Convertimos el texto del Excel (AAAA-MM-DD) en una fecha real de Python
                            limite = datetime.datetime.strptime(str(p['fecha_limite']).strip(), "%Y-%m-%d").date()
                            if hoy > limite:
                                bloqueado_por_fecha = True
                        except Exception as e:
                            # Si hay un fallo de formato en el Excel, no bloqueamos para evitar colgar la web
                            bloqueado_por_fecha = False

                    with st.container(border=True):
                        st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                        st.caption(f"📅 {p['fecha']}")
                        
                        def_g1, def_g2 = 0, 0
                        if p_id in apuestas_usuario:
                            def_g1, def_g2 = apuestas_usuario[p_id]
                            if not bloqueado_por_fecha:
                                st.markdown("<span style='color: #2ecc71; font-weight: bold;'>✓ Tienes una apuesta guardada. Puedes modificarla hasta el cierre.</span>", unsafe_allow_html=True)
                        
                        # Si está bloqueado por fecha, mostramos la alerta y desactivamos la edición
                        if bloqueado_por_fecha:
                            st.markdown(f"<span style='color: #e74c3c; font-weight: bold;'>🔒 Plazo cerrado. No se permiten más apuestas o cambios para este partido.</span>", unsafe_allow_html=True)
                            if p_id in apuestas_usuario:
                                st.info(f"Tu pronóstico final guardado fue: **{def_g1} - {def_g2}**")
                        
                        col1, col2, col3 = st.columns([2, 2, 3])
                        with col1:
                            g1 = st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=20, value=def_g1, key=f"g1_{p_id}", disabled=bloqueado_por_fecha)
                        with col2:
                            g2 = st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=20, value=def_g2, key=f"g2_{p_id}", disabled=bloqueado_por_fecha)
                        with col3:
                            st.write("")
                            st.write("")
                            # Solo renderizamos el botón si el plazo está vigente
                            if not bloqueado_por_fecha:
                                if st.button("Guardar Apuesta", key=f"btn_{p_id}", use_container_width=True):
                                    df_apuestas_completo = leer_tabla("apuestas")
                                    df_apuestas_completo.columns = df_apuestas_completo.columns.str.strip().str.lower()
                                    
                                    fila_existente = df_apuestas_completo[
                                        (df_apuestas_completo['usuario_id'].astype(int) == st.session_state.user_id) & 
                                        (df_apuestas_completo['partido_id'].astype(int) == p_id)
                                    ]
                                    
                                    if not fila_existente.empty:
                                        df_apuestas_completo.loc[fila_existente.index, ['goles1', 'goles2']] = [int(g1), int(g2)]
                                    else:
                                        nueva_fila = pd.DataFrame([{"usuario_id": int(st.session_state.user_id), "partido_id": int(p_id), "goles1": int(g1), "goles2": int(g2)}])
                                        df_apuestas_completo = pd.concat([df_apuestas_completo, nueva_fila], ignore_index=True)
                                    
                                    conn.update(worksheet="apuestas", data=df_apuestas_completo)
                                    st.success("¡Apuesta guardada con éxito!")
                                    st.rerun()
    # --- PANTALLA: PANEL ADMINISTRADOR ---
    elif menu == "⚙️ Panel Administrador":
        st.title("⚙️ Panel de Control (Admin)")
        tab1, tab2 = st.tabs(["Cerrar Partidos con Resultados Reales", "Añadir Nuevos Partidos"])
        
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
                            if st.button("Finalizar Partido", key=f"fin_{p_id}", use_container_width=True):
                                df_partidos_completo = leer_tabla("partidos")
                                df_partidos_completo.loc[df_partidos_completo['id'] == p_id, ['goles1', 'goles2', 'jugado']] = [res1, res2, 1]
                                conn.update(worksheet="partidos", data=df_partidos_completo)
                                st.success("Partido cerrado. Puntos calculados en la Clasificación.")
                                st.rerun()
                                
        with tab2:
            st.subheader("Registrar Nuevo Partido")
            with st.form("nuevo_partido_form"):
                eq1 = st.text_input("Equipo Local")
                eq2 = st.text_input("Equipo Visitante")
                fecha_partido = st.text_input("Fecha / Fase")
                check_partido = st.form_submit_button("Crear Partido")
                
                if check_partido and eq1 and eq2:
                    df_partidos_completo = leer_tabla("partidos")
                    nuevo_id = int(df_partidos_completo['id'].max() + 1) if not df_partidos_completo.empty else 1
                    nueva_fila = pd.DataFrame([{"id": nuevo_id, "equipo1": eq1, "equipo2": eq2, "fecha": fecha_partido, "goles1": "", "goles2": "", "jugado": 0}])
                    df_partidos_completo = pd.concat([df_partidos_completo, nueva_fila], ignore_index=True)
                    conn.update(worksheet="partidos", data=df_partidos_completo)
                    st.success("Partido añadido con éxito.")
                    st.rerun()
