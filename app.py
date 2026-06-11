import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import time

# Configuración de la página web
st.set_page_config(page_title="Porra Mundialista", page_icon="⚽", layout="centered")

# --- DICCIONARIO DE BANDERAS AUTOMÁTICAS ---
BANDERAS = {
    "españa": "🇪🇸", "alemania": "🇩🇪", "francia": "🇫🇷", "inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "italia": "🇮🇹", "portugal": "🇵🇹", "países bajos": "🇳🇱", "holanda": "🇳🇱",
    "bélgica": "🇧🇪", "croacia": "🇭🇷", "argentina": "🇦🇷", "brasil": "🇧🇷",
    "uruguay": "🇺🇾", "colombia": "🇨🇴", "chile": "🇨🇱", "perú": "🇵🇪",
    "méxico": "🇲🇽", "estados unidos": "🇺🇸", "usa": "🇺🇸", "canadá": "🇨🇦",
    "marruecos": "🇲🇦", "senegal": "🇸🇳", "japón": "🇯🇵", "corea del sur": "🇰🇷",
    "australia": "🇦🇺", "arabia saudita": "🇸🇦", "ecuador": "🇪🇨", "suiza": "🇨🇭",
    "dinamarca": "🇩🇰", "túnez": "🇹🇳", "polonia": "🇵🇱", "costa rica": "🇨🇷",
    "gales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "irán": "🇮🇷", "ghana": "🇬🇭", "camerún": "🇨🇲", "serbia": "🇷🇸",
    "sudáfrica": "🇿🇦", "república checa": "🇨🇿", "bosnia y herzegovina": "🇧🇦",
    "paraguay": "🇵🇾", "catar": "🇶🇦", "haití": "🇭🇹", "escocia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "turquía": "🇹🇷", "curazao": "🇨🇼", "costa de marfil": "🇨🇮", "suecia": "🇸🇪",
    "cabo verde": "🇨🇻", "egipto": "🇪🇬", "nueva zelanda": "🇳🇿", "irak": "🇮🇶",
    "noruega": "🇳🇴", "argelia": "🇩🇿", "austria": "🇦🇹", "jordania": "🇯🇴",
    "rd congo": "🇨🇩", "uzbekistán": "🇺🇿", "panamá": "🇵🇦"
}

def obtener_bandera(equipo):
    """Devuelve el emoji de la bandera correspondiente o una bandera blanca si no se encuentra."""
    nombre_limpio = str(equipo).strip().lower()
    return BANDERAS.get(nombre_limpio, "🏳️")

# --- ESTILOS CSS PARA HACER LA BARRA LATERAL OPTIMIZADA Y BOTONES ---
st.markdown("""
    <style>
        button[data-testid="stSidebarCollapseButton"] {
            background-color: #f0f2f6 !important;
            border: 2px solid #3498db !important;
            border-radius: 8px !important;
            padding: 5px !important;
            transform: scale(1.2); 
            margin-left: 10px !important;
        }
        div[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] {
            font-size: 1.1rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stSidebar"] label[data-testid="stMarkdownContainer"] p {
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            color: #1a1a1a !important;
            padding: 4px 0px !important;
        }
        
        /* OPTIMIZACIÓN MÓVIL */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                max-width: 65vw !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN OFICIAL Y ENCRIPTADA A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_tabla(pestana):
    """Lee datos aprovechando la caché durante 10 mins (600s)."""
    return conn.read(worksheet=pestana, ttl=600)

# --- LÓGICA DE PUNTOS Y CLASIFICACIÓN ---
def calcular_clasificacion():
    df_usuarios = leer_tabla("usuarios")
    df_partidos = leer_tabla("partidos")
    df_apuestas = leer_tabla("apuestas")
    
    if df_usuarios.empty or df_partidos.empty:
        return pd.DataFrame()
    
    df_partidos.columns = df_partidos.columns.str.strip().str.lower()
    df_usuarios.columns = df_usuarios.columns.str.strip().str.lower()
        
    usuarios = df_usuarios[df_usuarios['es_admin'] == 0]
    partidos_jugados = df_partidos[df_partidos['jugado'] == 1]
    
    apuestas_map = {}
    if not df_apuestas.empty:
        df_apuestas.columns = df_apuestas.columns.str.strip().str.lower()
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
        df = df.sort_values(by=["Puntos Totales", "Plenos (3 pts)"], ascending=[False, False]).reset_index(drop=True)
        
        max_plenos = df["Plenos (3 pts)"].max()
        total_jugadores = len(df)
        
        for idx in df.index:
            nombre = df.at[idx, "Familiar"]
            
            if df.at[idx, "Plenos (3 pts)"] == max_plenos and max_plenos > 0:
                nombre += " ⭐"
                
            if total_jugadores >= 3:
                if idx == total_jugadores - 1:
                    nombre += " 😵"
                elif idx == total_jugadores - 2:
                    nombre += " 😭"
                elif idx == total_jugadores - 3:
                    nombre += " 😓"
                
            if idx == 0:
                nombre = "🥇 " + nombre
            elif idx == 1:
                nombre = "🥈 " + nombre
            elif idx == 2:
                nombre = "🥉 " + nombre
                
            df.at[idx, "Familiar"] = nombre
            
        df.index += 1  
    return df

# --- LÓGICA DE EVOLUCIÓN PARA EL GRÁFICO ---
def generar_datos_evolucion():
    df_usuarios = leer_tabla("usuarios")
    df_partidos = leer_tabla("partidos")
    df_apuestas = leer_tabla("apuestas")
    
    if df_usuarios.empty or df_partidos.empty:
        return pd.DataFrame()
    
    df_partidos.columns = df_partidos.columns.str.strip().str.lower()
    df_usuarios.columns = df_usuarios.columns.str.strip().str.lower()
        
    usuarios = df_usuarios[df_usuarios['es_admin'] == 0]
    partidos_jugados = df_partidos[df_partidos['jugado'] == 1].sort_values(by='id')
    
    apuestas_map = {}
    if not df_apuestas.empty:
        df_apuestas.columns = df_apuestas.columns.str.strip().str.lower()
        for _, row in df_apuestas.iterrows():
            try:
                apuestas_map[(int(row['usuario_id']), int(row['partido_id']))] = (int(row['goles1']), int(row['goles2']))
            except:
                continue
                
    historial = []
    estado_actual = {u['nombre']: 0 for _, u in usuarios.iterrows()}
    
    for _, p in partidos_jugados.iterrows():
        p_id = int(p['id'])
        etiqueta_partido = f"P{p_id} ({p['equipo1'][:3]}-{p['equipo2'][:3]})"
        try:
            g_real1, g_real2 = int(p['goles1']), int(p['goles2'])
            for _, u in usuarios.iterrows():
                u_id = int(u['id'])
                nombre = u['nombre']
                if (u_id, p_id) in apuestas_map:
                    g_bet1, g_bet2 = apuestas_map[(u_id, p_id)]
                    if g_real1 == g_bet1 and g_real2 == g_bet2:
                        estado_actual[nombre] += 3
                    elif (g_real1 > g_real2 and g_bet1 > g_bet2) or \
                         (g_real1 < g_real2 and g_bet1 < g_bet2) or \
                         (g_real1 == g_real2 and g_bet1 == g_bet2):
                        estado_actual[nombre] += 1
        except:
            pass
            
        historial.append({"Partido": etiqueta_partido, **estado_actual})
        
    if not historial:
        return pd.DataFrame()
        
    df_hist = pd.DataFrame(historial)
    df_hist = df_hist.set_index("Partido")
    return df_hist

# --- CONTROL DE SESIÓN (LOGIN) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'animado_premio' not in st.session_state:
    st.session_state.animado_premio = False

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

    # --- PANTALLA: CLASIFICACIÓN ---
    if menu == "🏆 Clasificación":
        st.title("🏆 Clasificación de la Familia")
        
        # --- MARCADOR ANIMADO DEL PREMIO ---
        contenedor_premio = st.empty()
        
        if not st.session_state.animado_premio:
            pasos = 25
            for i in range(1, pasos + 1):
                valor_actual = int((1500000 / pasos) * i)
                texto_dinamico = f"{valor_actual:,}".replace(",", ".")
                contenedor_premio.markdown(f"""
                    <div style="background-color: #fef9e7; padding: 20px; border-radius: 12px; border: 2px dashed #f1c40f; text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 2rem; font-weight: 800; color: #b7950b; text-shadow: 1px 1px 2px #f9e79f;">
                            💰 ACUMULADO PREMIO: {texto_dinamico} Millones
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(0.08)
            st.session_state.animado_premio = True
            
        contenedor_premio.markdown("""
            <div style="background-color: #fef9e7; padding: 20px; border-radius: 12px; border: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; box-shadow: 0px 4px 10px rgba(241, 196, 15, 0.2);">
                <span style="font-size: 2.1rem; font-weight: 900; color: #b7950b; text-shadow: 1px 1px 2px #f9e79f;">
                    💰 PREMIO TOTAL: 1.500.000 Millones 💰
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("Aquí puedes ver quién va liderando la porra mundialista en tiempo real.")
        
        tabla_puntos = calcular_clasificacion()
        if not tabla_puntos.empty:
            st.dataframe(tabla_puntos, use_container_width=True)
            
            st.divider()
            st.subheader("📈 Evolución de los Puntos")
            st.write("Sigue la carrera por el primer puesto partido a partido.")
            df_evolucion = generar_datos_evolucion()
            if not df_evolucion.empty:
                st.line_chart(df_evolucion)
            else:
                st.info("El gráfico de evolución aparecerá en cuanto se cierre el primer partido.")
        else:
            st.info("Aún no hay puntos calculados. ¡Aparecerán cuando el administrador cierre los primeros partidos!")

    # --- PANTALLA: MIS APUESTAS ---
    elif menu == "📝 Mis Apuestas":
        st.title("📝 Tus Pronósticos")
        st.write("El plazo para guardar apuestas se cierra automáticamente **2 horas antes** del inicio de cada partido.")
        
        df_partidos = leer_tabla("partidos")
        df_apuestas = leer_tabla("apuestas")
        
        if df_partidos.empty:
            st.warning("No se ha podido cargar el calendario de partidos.")
        else:
            df_partidos.columns = df_partidos.columns.str.strip().str.lower()
            
            apuestas_usuario = {}
            if not df_apuestas.empty:
                df_apuestas.columns = df_apuestas.columns.str.strip().str.lower()
                df_u_apuestas = df_apuestas[df_apuestas['usuario_id'].astype(int) == st.session_state.user_id]
                for _, row in df_u_apuestas.iterrows():
                    try:
                        apuestas_usuario[int(row['partido_id'])] = (int(row['goles1']), int(row['goles2']))
                    except:
                        continue
            
            ahora_utc = datetime.datetime.utcnow()
            ahora_bst = ahora_utc + datetime.timedelta(hours=1)
            
            meses = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, 
                     "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
            
            # --- NUEVA BOTONERA PARA ELEGIR LA ZONA HORARIA ---
            c_filtro, c_zona = st.columns(2)
            with c_filtro:
                filtro = st.selectbox(
                    "🔍 Filtrar partidos:",
                    ["Mostrar todos los partidos", "Solo partidos PENDIENTES", "Solo partidos GUARDADOS", "Solo partidos FINALIZADOS"]
                )
            with c_zona:
                zona_horaria = st.radio("🌍 Zona horaria:", ["🇬🇧 UK (BST)", "🇨🇴 Colombia (-6h)"])
                
            st.divider()
            
            for _, p in df_partidos.iterrows():
                p_id = int(p['id'])
                es_jugado = int(p['jugado']) == 1
                tiene_apuesta = p_id in apuestas_usuario
                
                if filtro == "Solo partidos PENDIENTES" and (tiene_apuesta or es_jugado):
                    continue
                if filtro == "Solo partidos GUARDADOS" and not tiene_apuesta:
                    continue
                if filtro == "Solo partidos FINALIZADOS" and not es_jugado:
                    continue
                    
                bloqueado_por_fecha = False
                
                # Valores por defecto para mostrar
                fecha_mostrar = p['fecha'] if pd.notna(p['fecha']) else "Sin fecha"
                hora_mostrar = str(p['hora']).strip() if 'hora' in p and pd.notna(p['hora']) else "Sin hora"
                texto_zona = "(BST)"
                
                if 'fecha' in p and pd.notna(p['fecha']) and 'hora' in p and pd.notna(p['hora']):
                    try:
                        txt_fecha = str(p['fecha']).strip().lower()
                        txt_hora = str(p['hora']).strip()
                        
                        partes_f = txt_fecha.split('-')
                        partes_h = txt_hora.split(':')
                        
                        if len(partes_f) == 2 and len(partes_h) >= 2:
                            dia_partido = int(partes_f[0])
                            mes_texto = partes_f[1][:3]
                            mes_partido = meses.get(mes_texto, 6)
                            
                            hora_p = int(partes_h[0])
                            min_p = int(partes_h[1][:2])
                            
                            fecha_partido_real = datetime.datetime(2026, mes_partido, dia_partido, hora_p, min_p)
                            
                            # --- CÁLCULO ESTRICTO DEL CIERRE EN BST ---
                            limite_apuesta = fecha_partido_real - datetime.timedelta(hours=2)
                            if ahora_bst > limite_apuesta:
                                bloqueado_por_fecha = True
                                
                            # --- CAMBIO COSMÉTICO A HORA DE COLOMBIA ---
                            if "Colombia" in zona_horaria:
                                fecha_col = fecha_partido_real - datetime.timedelta(hours=6)
                                mes_nombres = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 
                                               7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
                                fecha_mostrar = f"{fecha_col.day:02d}-{mes_nombres[fecha_col.month]}"
                                hora_mostrar = fecha_col.strftime("%H:%M")
                                texto_zona = "(COT)"
                    except:
                        pass

                with st.container(border=True):
                    info_grupo = f" ({p['grupo']})" if 'grupo' in p and pd.notna(p['grupo']) and str(p['grupo']).strip() != "" else ""
                    
                    bandera1 = obtener_bandera(p['equipo1'])
                    bandera2 = obtener_bandera(p['equipo2'])
                    
                    st.write(f"### {bandera1} {p['equipo1']} vs {p['equipo2']} {bandera2} {info_grupo}")
                    st.caption(f"📅 {fecha_mostrar} a las {hora_mostrar} {texto_zona}")
                    
                    def_g1, def_g2 = 0, 0
                    if tiene_apuesta:
                        def_g1, def_g2 = apuestas_usuario[p_id]
                        
                    if es_jugado:
                        res_real1 = int(p['goles1']) if pd.notna(p['goles1']) and str(p['goles1']).strip() != "" else 0
                        res_real2 = int(p['goles2']) if pd.notna(p['goles2']) and str(p['goles2']).strip() != "" else 0
                        st.markdown(f"<span style='color: #8e44ad; font-weight: bold;'>🏆 Partido finalizado. Resultado real: {res_real1} - {res_real2}</span>", unsafe_allow_html=True)
                        if tiene_apuesta:
                            st.info(f"Tu pronóstico fue: **{def_g1} - {def_g2}**")
                        else:
                            st.warning("No guardaste ningún pronóstico para este partido.")
                    
                    else:
                        if tiene_apuesta and not bloqueado_por_fecha:
                            st.markdown("<span style='color: #2ecc71; font-weight: bold;'>✓ Tienes una apuesta guardada. Puedes cambiarla hasta el cierre.</span>", unsafe_allow_html=True)
                        
                        if bloqueado_por_fecha:
                            st.markdown(f"<span style='color: #e74c3c; font-weight: bold;'>🔒 Plazo cerrado. Se superó el límite de las 2 horas antes del partido.</span>", unsafe_allow_html=True)
                            if tiene_apuesta:
                                st.info(f"Tu pronóstico final guardado fue: **{def_g1} - {def_g2}**")
                            else:
                                st.warning("No guardaste ningún pronóstico para este partido.")
                        
                        col1, col2, col3 = st.columns([2, 2, 3])
                        with col1:
                            g1 = st.number_input(f"Goles {bandera1} {p['equipo1']}", min_value=0, max_value=20, value=def_g1, key=f"g1_{p_id}", disabled=bloqueado_por_fecha)
                        with col2:
                            g2 = st.number_input(f"Goles {bandera2} {p['equipo2']}", min_value=0, max_value=20, value=def_g2, key=f"g2_{p_id}", disabled=bloqueado_por_fecha)
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
                                    
                                    try:
                                        df_log = leer_tabla("log_apuestas")
                                        fecha_reg = ahora_bst.strftime("%d-%m-%Y %H:%M:%S")
                                        partido_str = f"{p['equipo1']} vs {p['equipo2']}"
                                        
                                        nueva_fila_log = pd.DataFrame([{
                                            "fecha_registro": fecha_reg,
                                            "usuario": st.session_state.nombre,
                                            "partido": partido_str,
                                            "goles1": int(g1),
                                            "goles2": int(g2)
                                        }])
                                        
                                        df_log = pd.concat([df_log, nueva_fila_log], ignore_index=True)
                                        conn.update(worksheet="log_apuestas", data=df_log)
                                    except Exception as e:
                                        pass
                                    
                                    st.cache_data.clear()
                                    st.success("¡Apuesta guardada con éxito!")
                                    st.rerun()

    # --- PANTALLA: PANEL ADMINISTRADOR ---
    elif menu == "⚙️ Panel Administrador":
        st.title("⚙️ Panel de Control (Admin)")
        tab1, tab2, tab3 = st.tabs(["Cerrar Partidos", "Añadir Nuevos Partidos", "Ver Log de Apuestas"])
        
        with tab1:
            st.subheader("Resultados de los Encuentros")
            df_partidos = leer_tabla("partidos")
            
            if df_partidos.empty:
                st.info("No hay partidos en el calendario.")
            else:
                df_partidos.columns = df_partidos.columns.str.strip().str.lower()
                filtro_admin = st.selectbox(
                    "🔍 Filtrar partidos del panel:",
                    ["Solo partidos PENDIENTES de cerrar", "Solo partidos FINALIZADOS", "Mostrar todos los partidos"]
                )
                
                for _, p in df_partidos.iterrows():
                    p_id = int(p['id'])
                    es_jugado = int(p['jugado']) == 1
                    
                    if filtro_admin == "Solo partidos PENDIENTES de cerrar" and es_jugado:
                        continue
                    if filtro_admin == "Solo partidos FINALIZADOS" and not es_jugado:
                        continue
                    
                    with st.container(border=True):
                        info_grupo = f" ({p['grupo']})" if 'grupo' in p and pd.notna(p['grupo']) and str(p['grupo']).strip() != "" else ""
                        bandera1 = obtener_bandera(p['equipo1'])
                        bandera2 = obtener_bandera(p['equipo2'])
                        st.write(f"**{bandera1} {p['equipo1']} vs {p['equipo2']} {bandera2} {info_grupo}**")
                        
                        def_res1 = int(p['goles1']) if es_jugado and pd.notna(p['goles1']) and str(p['goles1']).strip() != "" else 0
                        def_res2 = int(p['goles2']) if es_jugado and pd.notna(p['goles2']) and str(p['goles2']).strip() != "" else 0
                        
                        if es_jugado:
                            st.markdown("<span style='color: #2ecc71; font-weight: bold;'>✓ Partido Finalizado (Resultado guardado)</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #f39c12; font-weight: bold;'>⏳ Pendiente de jugar / cerrar</span>", unsafe_allow_html=True)
                            
                        c1, c2, c3 = st.columns([2, 2, 3])
                        with c1:
                            res1 = st.number_input(f"Resultado {p['equipo1']}", min_value=0, max_value=20, value=def_res1, key=f"res1_{p_id}")
                        with c2:
                            res2 = st.number_input(f"Resultado {p['equipo2']}", min_value=0, max_value=20, value=def_res2, key=f"res2_{p_id}")
                        with c3:
                            st.write("")
                            st.write("")
                            texto_boton = "Modificar Resultado" if es_jugado else "Finalizar Partido"
                            if st.button(texto_boton, key=f"fin_{p_id}", use_container_width=True):
                                df_partidos_completo = leer_tabla("partidos")
                                df_partidos_completo.columns = df_partidos_completo.columns.str.strip().str.lower()
                                df_partidos_completo.loc[df_partidos_completo['id'] == p_id, ['goles1', 'goles2', 'jugado']] = [int(res1), int(res2), 1]
                                conn.update(worksheet="partidos", data=df_partidos_completo)
                                st.cache_data.clear()
                                st.success("¡Datos guardados y puntos actualizados!")
                                st.rerun()
                                
        with tab2:
            st.subheader("Registrar Nuevo Partido")
            with st.form("nuevo_partido_form"):
                eq1 = st.text_input("Equipo Local")
                eq2 = st.text_input("Equipo Visitante")
                fecha_partido = st.text_input("Fecha (Ej: 15-Jun)")
                hora_partido = st.text_input("Hora (Ej: 20:00)")
                grupo_partido = st.text_input("Grupo (Ej: Grupo A)") 
                check_partido = st.form_submit_button("Crear Partido")
                
                if check_partido and eq1 and eq2:
                    df_partidos_completo = leer_tabla("partidos")
                    df_partidos_completo.columns = df_partidos_completo.columns.str.strip().str.lower()
                    nuevo_id = int(df_partidos_completo['id'].max() + 1) if not df_partidos_completo.empty else 1
                    nueva_fila = pd.DataFrame([{"id": nuevo_id, "equipo1": eq1, "equipo2": eq2, "fecha": fecha_partido, "hora": hora_partido, "grupo": grupo_partido, "goles1": "", "goles2": "", "jugado": 0}])
                    df_partidos_completo = pd.concat([df_partidos_completo, nueva_fila], ignore_index=True)
                    conn.update(worksheet="partidos", data=df_partidos_completo)
                    st.cache_data.clear()
                    st.success("Partido añadido con éxito.")
                    st.rerun()
                    
        with tab3:
            st.subheader("Historial de Movimientos (Log)")
            try:
                df_log_view = leer_tabla("log_apuestas")
                if not df_log_view.empty:
                    st.dataframe(df_log_view.sort_index(ascending=False), use_container_width=True)
                else:
                    st.info("El log está vacío. Aparecerán datos cuando alguien guarde una apuesta.")
            except Exception:
                st.warning("No se ha encontrado la pestaña 'log_apuestas' en Google Sheets o está mal configurada.")
