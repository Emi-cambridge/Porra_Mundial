import streamlit as st
import pandas as pd
import requests

# Configuración de la página web
st.set_page_config(page_title="Porra Mundial Familiar", page_icon="⚽", layout="centered")

# --- CONFIGURACIÓN DE TU GOOGLE SHEET (CONEXIÓN NATIVA REFORZADA) ---
# Extraemos el ID único de tu hoja de cálculo
SPREADSHEET_ID = "1Tc-Hm2tlU1_1w77AVDaPyD_tmopg22u-a5ov2zBm8gQ"

def leer_tabla_nativa(pestana):
    """Lee datos en tiempo real directamente convirtiendo el Google Sheet en un CSV público/accesible."""
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana}"
    try:
        # Añadimos un parámetro aleatorio para saltarnos la caché de Streamlit y leer datos frescos
        df = pd.read_csv(f"{url}&cache_bust={st.runtime.scriptrunner.script_run_context.get_script_run_ctx().session_id if st.runtime.scriptrunner.script_run_context.get_script_run_ctx() else 0}", sep=',')
        # Limpiar columnas vacías si las hay
        df = df.dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la pestaña {pestana}: {e}")
        return pd.DataFrame()

def guardar_apuesta_nativa(usuario_id, partido_id, goles1, goles2):
    """Envía la apuesta de vuelta utilizando un formulario o webhook. 
    Para entornos sencillos sin st.connection, puedes gestionar las actualizaciones mediante API."""
    st.info("Para escribir datos directamente usando este método nativo simplificado, utilizaremos la URL de edición.")

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
    """Calcula el ranking dinámico leyendo directamente de las pestañas del Google Sheet."""
    df_usuarios = leer_tabla_nativa("usuarios")
    df_partidos = leer_tabla_nativa("partidos")
    df_apuestas = leer_tabla_nativa("apuestas")
    
    if df_usuarios.empty or df_partidos.empty:
        return pd.DataFrame()
        
    # Filtrar usuarios que no son admin
    usuarios = df_usuarios[df_usuarios['es_admin'] == 0]
    # Partidos que ya se jugaron
    partidos_jugados = df_partidos[df_partidos['jugado'] == 1]
    
    # Mapear apuestas para búsqueda rápida: (usuario_id, partido_id) -> (goles1, goles2)
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
            df_usuarios = leer_tabla_nativa("usuarios")
            if not df_usuarios.empty:
                # Normalizar columnas para evitar fallos de mayúsculas
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
                st.error("Error al conectar con la base de datos central en Google Sheets.")
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
            st.info("Aún no hay puntos calculados o la hoja está vacía. ¡Los puntos aparecerán cuando arranquen los partidos!")

    # --- PANTALLA: MIS APUESTAS ---
    elif menu == "📝 Mis Apuestas":
        st.title("📝 Tus Pronósticos")
        st.write("Para asegurar la máxima estabilidad sin errores de dependencias, introduce tus apuestas y envíalas directamente.")
        
        df_partidos = leer_tabla_nativa("partidos")
        if df_partidos.empty:
            st.warning("No se ha podido cargar el calendario de partidos.")
        else:
            partidos_activos = df_partidos[df_partidos['jugado'] == 0]
            if partidos_activos.empty:
                st.info("No hay partidos abiertos para apostar en este momento.")
            else:
                for _, p in partidos_activos.iterrows():
                    p_id = int(p['id'])
                    with st.container(border=True):
                        st.write(f"**{p['equipo1']} vs {p['equipo2']}**")
                        st.caption(f"📅 {p['fecha']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=20, value=0, key=f"g1_{p_id}")
                        with col2:
                            st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=20, value=0, key=f"g2_{p_id}")
                        
                        # Enlace directo para interactuar si fuera necesario
                        st.link_button("Modificar directamente en la Hoja Central", f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit", use_container_width=True)
