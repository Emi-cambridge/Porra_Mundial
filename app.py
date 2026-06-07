import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# Configuración de la página web
st.set_page_config(page_title="Porra Mundialista", page_icon="⚽", layout="centered")

# --- ESTILOS CSS PARA HACER LA BARRA LATERAL Y BOTONES MÁS VISIBLES ---
st.markdown("""
    <style>
        /* Hacer más visible el botón nativo para abrir/cerrar la barra lateral */
        button[data-testid="stSidebarCollapseButton"] {
            background-color: #f0f2f6 !important;
            border: 2px solid #3498db !important;
            border-radius: 8px !important;
            padding: 5px !important;
            transform: scale(1.2); /* Lo hace un 20% más grande */
            margin-left: 10px !important;
        }
        
        /* Modificar el texto de las opciones de radio en la barra lateral */
        div[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] {
            font-size: 1.1rem !important;
            font-weight: bold !important;
        }
        
        /* Hacer más grandes y visibles los botones/opciones del menú lateral */
        div[data-testid="stSidebar"] label[data-testid="stMarkdownContainer"] p {
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            color: #1a1a1a !important;
            padding: 4px 0px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN OFICIAL Y ENCRIPTADA A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_tabla(pestana):
    """Lee datos en tiempo real de forma segura sin almacenamiento en caché."""
    return conn.read(worksheet=pestana, ttl=0)

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
        
        ranking.append({
            "Familiar": u['nombre'],
            "Puntos Totales": puntos_totales,
            "Plenos (3 pts)": plenos,
            "Aciertos (1 pt)": aciertos_signo
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
    st.title("⚽ Porra Mundialista 2026")
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
        st.write("Introduce tus resultados y haz clic en **Guardar Apuesta**. El plazo cierra definitivamente el día antes de cada partido.")
        
        df_partidos = leer_tabla("partidos")
        df_apuestas = leer_tabla("apuestas")
        
        if df_partidos.empty:
            st.warning("No se ha podido cargar el calendario de partidos.")
        else:
            partidos_activos = df_partidos[df_partidos['jugado'] == 0]
            
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
                hoy = datetime.date.today()
                meses = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, 
                         "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                
                # Selector de filtro de partidos
                filtro = st.selectbox(
                    "🔍 Filtrar partidos por estado:",
                    ["Mostrar todos los partidos", "Solo partidos PENDIENTES", "Solo partidos GUARDADOS"]
                )
                
                for _, p in partidos_activos.iterrows():
                    p_id = int(p['id'])
                    tiene_apuesta = p_id in apuestas_usuario
                    
                    # Filtrado dinámico en tiempo real
                    if filtro == "Solo partidos PENDIENTES" and tiene_apuesta:
                        continue
                    if filtro == "Solo partidos GUARDADOS" and not tiene_apuesta:
                        continue
                        
                    bloqueado_por_fecha = False
                    
                    if 'fecha' in p and pd.notna(p['fecha']):
                        try:
                            txt_fecha = str(p['fecha']).strip().lower()
                            partes = txt_fecha.split('-')
                            
                            if len(partes) == 2:
                                dia_partido = int(partes[0])
                                mes_texto = partes[1][:3]
                                mes_partido = meses.get(mes_texto, 6)
                                
                                fecha_partido_real = datetime.date(2026, mes_partido, dia_partido)
                                limite_apuesta = fecha_partido_real - datetime.timedelta(days=1)
                                
                                if hoy > limite_apuesta:
                                    bloqueado_por_fecha = True
                        except:
                            bloqueado_por_fecha = False

                    with st.container(border=True):
                        # CORREGIDO: Línea 226 restaurada por completo
                        st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                        st.caption(f"📅 Fecha del encuentro: {p['fecha']}")
                        
                        def_g1, def_g2 = 0, 0
                        if tiene_apuesta:
                            def_g1, def_g2 = apuestas_usuario[p_id]
                            if not bloqueado_por_fecha:
                                st.markdown("<span style='color: #2ecc71; font-weight: bold;'>✓ Tienes una apuesta guardada. Puedes cambiarla hasta el cierre.</span>", unsafe_allow_html=True)
                        
                        if bloqueado_por_fecha:
                            st.markdown(f"<span style='color: #e74c3c; font-weight: bold;'>🔒 Plazo cerrado. El tiempo límite expiró el día anterior al partido.</span>", unsafe_allow_html=True)
                            if tiene_apuesta:
                                st.info(f"Tu pronóstico final guardado fue: **{def_g1} - {def_g2}**")
                        
                        col1, col2, col3 = st.columns([2, 2, 3])
                        with col1:
                            g1 = st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=20, value=def_g1, key=f"g1_{p_id}", disabled=bloqueado_por_fecha)
                        with col2:
                            g2 = st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=20, value=def_g2, key=f"g2_{p_id}", disabled=bloqueado_por_fecha)
                        with col3:
                            st.write("")
                            st.write("")
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
                fecha_partido = st.text_input("Fecha (Ej: 15-Jun)")
                check_partido = st.form_submit_button("Crear Partido")
                
                if check_partido and eq1 and eq2:
                    df_partidos_completo = leer_tabla("partidos")
                    nuevo_id = int(df_partidos_completo['id'].max() + 1) if not df_partidos_completo.empty else 1
                    nueva_fila = pd.DataFrame([{"id": nuevo_id, "equipo1": eq1, "equipo2": eq2, "fecha": fecha_partido, "goles1": "", "goles2": "", "jugado": 0}])
                    df_partidos_completo = pd.concat([df_partidos_completo, nueva_fila], ignore_index=True)
                    conn.update(worksheet="partidos", data=df_partidos_completo)
                    st.success("Partido añadido con éxito.")
                    st.rerun()
