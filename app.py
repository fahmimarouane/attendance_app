import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import warnings
import plotly.express as px
import json
from pathlib import Path

# Import authentication functions
from auth import check_authentication, show_login, show_user_management, logout


warnings.simplefilter("ignore", UserWarning)
pd.set_option('display.max_columns', None)

# Constants
CLASSES_DIR = "classes"  # New directory for class files
ABSENCE_DIR = "absences"
SETTINGS_FILE = "settings.json"

# Theme Configuration
THEME = {
    'primary': '#1E88E5',
    'secondary': '#FFC107',
    'background': '#121212',
    'surface': '#1E1E1E',
    'text': '#FFFFFF',
    'error': '#CF6679'
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)


def apply_custom_theme():
    """Apply custom theme to Streamlit interface"""
    st.markdown("""
    <style>
        .stApp {
            background-color: %(background)s;
            color: %(text)s;
        }
        
        .metric-card {
            background: linear-gradient(145deg, %(surface)s, %(background)s);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
            margin: 10px;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 8px 8px 20px rgba(0,0,0,0.3);
        }
        
        .metric-title {
            color: %(primary)s;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .metric-value {
            color: %(secondary)s;
            font-size: 1.5em;
            font-weight: 700;
        }
        
        .student-card {
            background: %(surface)s;
            border-radius: 10px;
            padding: 15px;
            margin: 5px;
            border-left: 4px solid %(primary)s;
        }
        
        .absent {
            border-left-color: %(error)s;
        }
        
        .stats-card {
            background: %(surface)s;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
    </style>
    """ % THEME, unsafe_allow_html=True)



def extract_students(file):
    try:
        df = pd.read_excel(file, engine="openpyxl")
        code_massar = df.iloc[16:, 2].reset_index(drop=True)
        nom = df.iloc[16:, 3].reset_index(drop=True)
        # Create DataFrame with Absence column initialized to False
        return pd.DataFrame({
            'Code Massar': code_massar,
            'Nom': nom,
            'Absence': False  # Initialize all students as present
        })
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des étudiants: {str(e)}")
        return None


def sanitize_filename(name):
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        name (str): Original filename
        
    Returns:
        str: Sanitized filename safe for filesystem
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Remove any other potentially problematic characters
    name = ''.join(c for c in name if c.isprintable())
    
    # Limit length to avoid potential issues
    return name[:100]


def save_attendance_data(df_students, class_name, date, time_slot):
    """
    Save attendance data to class-specific directory
    """
    try:
        # Get absent students
        absences = df_students[df_students['Absence']].copy()
        
        if len(absences) > 0:
            # Create class directory if it doesn't exist
            safe_class_name = sanitize_filename(class_name)
            class_dir = Path(ABSENCE_DIR) / safe_class_name
            class_dir.mkdir(exist_ok=True)
            
            # Create filename with date and time
            safe_date = date.strftime('%Y-%m-%d')
            safe_time = time_slot.replace(':', '_')
            filename = class_dir / f'absences_{safe_date}_{safe_time}.xlsx'
            
            # Add date and time information
            absences['Date'] = safe_date
            absences['Heure'] = time_slot
            absences['Classe'] = class_name
            
            # Save to Excel
            absences.to_excel(filename, index=False)
            st.success(f"✅ Absences enregistrées dans {filename}")
        else:
            st.info("ℹ️ Aucune absence à enregistrer")
            
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement des absences: {str(e)}")


def init_directories():
    """Initialize necessary directories"""
    for directory in [CLASSES_DIR, ABSENCE_DIR]:
        Path(directory).mkdir(exist_ok=True)

def save_class_file(uploaded_file, class_name):
    """Save uploaded class file with sanitized name"""
    safe_class_name = sanitize_filename(class_name)
    file_path = Path(CLASSES_DIR) / f"{safe_class_name}.xlsx"
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getvalue())
    return file_path

def get_available_classes():
    """Get list of available class files"""
    return [f.stem for f in Path(CLASSES_DIR).glob('*.xlsx')]

def extract_general_info(file):
    try:
        df_annee = pd.read_excel(file, skiprows=12, engine="openpyxl")
        df_semestre = pd.read_excel(file, skiprows=10, engine="openpyxl")
        df_matiere = pd.read_excel(file, skiprows=10, engine="openpyxl")
        df_academie = pd.read_excel(file, skiprows=6, engine="openpyxl")
        df_province = pd.read_excel(file, skiprows=6, engine="openpyxl")
        df_ecole = pd.read_excel(file, skiprows=6, engine="openpyxl")
        df_niveau = pd.read_excel(file, skiprows=8, engine="openpyxl")
        df_professeur = pd.read_excel(file, skiprows=8, engine="openpyxl")
        df_classe = pd.read_excel(file, skiprows=8, engine="openpyxl")

        return {
            'Année Scolaire': df_annee.columns[3],
            'Semestre': df_semestre.columns[3],
            'Matière': df_matiere.columns[14],
            'Académie': df_academie.columns[3],
            'Province': df_province.columns[8],
            'Ecole': df_ecole.columns[14],
            'Niveau': df_niveau.columns[3],
            'Professeur': df_professeur.columns[14],
            'Classe': df_classe.columns[8],
        }
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des informations: {str(e)}")
        return None

def show_class_management():
    """New function to handle class file uploads"""
    st.subheader("📚 Gestion des Classes")
    
    uploaded_file = st.file_uploader("📂 Importer un nouveau fichier de classe", type=["xlsx"])
    
    if uploaded_file:
        general_info = extract_general_info(uploaded_file)
        if general_info:
            st.success("✅ Informations de classe extraites avec succès")
            
            # Show class information
            with st.expander("🏫 Informations de la Classe", expanded=True):
                cols = st.columns(3)
                for i, (label, value) in enumerate(general_info.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{value}</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            if st.button("💾 Enregistrer la Classe"):
                try:
                    file_path = save_class_file(uploaded_file, general_info['Classe'])
                    st.success(f"✅ Classe enregistrée avec succès: {file_path}")
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement: {str(e)}")
    
    # Show existing classes
    st.subheader("📋 Classes Existantes")
    existing_classes = get_available_classes()
    if existing_classes:
        for class_name in existing_classes:
            st.info(f"📚 {class_name}")
    else:
        st.info("Aucune classe enregistrée")

def show_attendance_management():
    """Modified attendance management with class selection"""
    st.subheader("📝 Gestion des Présences")
    
    # Class selection
    available_classes = get_available_classes()
    if not available_classes:
        st.warning("⚠️ Aucune classe disponible. Veuillez d'abord importer des classes.")
        return
        
    selected_class = st.selectbox("Sélectionner une classe", available_classes)
    
    # Load selected class file
    try:
        file_path = Path(CLASSES_DIR) / f"{selected_class}.xlsx"
        class_info = extract_general_info(file_path)
        students_df = extract_students(file_path)
        
        if class_info and students_df is not None:
            # Display class info
            with st.expander("🏫 Informations de la Classe", expanded=True):
                cols = st.columns(3)
                for i, (label, value) in enumerate(class_info.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{value}</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            # Date and Time Selection
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input(
                    "Date",
                    value=datetime.today(),
                    min_value=datetime.today() - timedelta(days=7),
                    max_value=datetime.today() + timedelta(days=1)
                )
            
            with col2:
                time_slot = st.selectbox(
                    "Heure",
                    ["8h30-9h30", "9h30-10h30", "10h30-11h30", "11h30-12h30",
                     "13h30-14h30", "14h30-15h30", "15h30-16h30", "16h30-17h30"]
                )
            
            # Attendance Management
            show_attendance_interface(students_df, class_info['Classe'], date, time_slot)
            
    except Exception as e:
        st.error(f"Erreur lors du chargement de la classe: {str(e)}")

def show_attendance_interface(df_students, class_name, date, time_slot):
    """Separated attendance interface logic"""
    st.subheader("👨‍🎓 Gestion des Présences")
    
    # Quick Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Marquer tous présents"):
            df_students['Absence'] = False
    with col2:
        if st.button("❌ Marquer tous absents"):
            df_students['Absence'] = True
    
    # Student Cards
    for i in range(0, len(df_students), 5):
        cols = st.columns(5)
        for j, col in enumerate(cols):
            if i + j < len(df_students):
                student = df_students.iloc[i + j]
                with col:
                    is_absent = st.checkbox(
                        f"Absent - {student['Nom']}",
                        key=f"absent_{student['Code Massar']}"
                    )
                    df_students.loc[df_students.index[i + j], 'Absence'] = is_absent
                    
                    st.markdown(f"""
                        <div class="student-card {'absent' if is_absent else ''}">
                            <div class="metric-title">{student['Nom']}</div>
                            <div class="metric-value">{'Absent' if is_absent else 'Présent'}</div>
                        </div>
                    """, unsafe_allow_html=True)
    
    # Save Absences
    if st.button("💾 Enregistrer les Absences", type="primary"):
        save_attendance_data(df_students, class_name, date, time_slot)


def show_statistics():
    """Enhanced statistics view with monthly reports"""
    st.subheader("📊 Statistiques des Absences")
    
    try:
        # Class selection
        classes = get_available_classes()
        if not classes:
            st.info("Aucune donnée d'absence disponible")
            return
            
        selected_class = st.selectbox("Sélectionner une classe", classes)
        
        # Month selection
        current_date = datetime.now()
        selected_month = st.selectbox(
            "Sélectionner un mois",
            range(1, 13),
            index=current_date.month - 1,
            format_func=lambda x: datetime(2024, x, 1).strftime('%B')
        )
        
        # Get statistics for selected month
        df_stats = get_monthly_statistics(selected_class, selected_month)
        
        # Check if DataFrame is empty before proceeding
        if df_stats is None or df_stats.empty:
            st.info("Aucune donnée pour cette période")
            return
        
        # Display statistics only if we have data
        show_monthly_statistics(df_stats)
        
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")
        
def get_monthly_statistics(class_name, month):
    """Get statistics for a specific month"""
    try:
        folder_path = Path(ABSENCE_DIR) / sanitize_filename(class_name)
        if not folder_path.exists():
            return pd.DataFrame()
        
        all_absences = []
        for file in folder_path.glob('*.xlsx'):
            try:
                df = pd.read_excel(file)
                if 'Date' not in df.columns:
                    continue
                    
                # Ensure Date column is datetime
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                # Remove rows with invalid dates
                df = df.dropna(subset=['Date'])
                
                # Filter for selected month
                df = df[df['Date'].dt.month == month]
                
                if not df.empty:
                    all_absences.append(df)
                    
            except Exception as e:
                st.warning(f"Impossible de lire le fichier {file.name}: {str(e)}")
                continue
        
        if not all_absences:
            return pd.DataFrame()
        
        result_df = pd.concat(all_absences, ignore_index=True)
        
        # Ensure required columns exist
        required_columns = ['Code Massar', 'Nom', 'Date']
        if not all(col in result_df.columns for col in required_columns):
            st.error("Les données ne contiennent pas toutes les colonnes requises")
            return pd.DataFrame()
            
        return result_df
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return pd.DataFrame()

def show_monthly_statistics(df_stats):
    """Display monthly statistics"""
    try:
        # Overall metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_absences = len(df_stats) if not df_stats.empty else 0
            st.metric("Total des absences", total_absences)
            
        with col2:
            unique_students = df_stats['Code Massar'].nunique() if not df_stats.empty else 0
            st.metric("Étudiants uniques absents", unique_students)
            
        with col3:
            unique_days = df_stats['Date'].nunique() if not df_stats.empty else 0
            st.metric("Jours avec absences", unique_days)
        
        if df_stats.empty:
            return
            
        # Student-wise absence count
        student_absences = df_stats.groupby(['Code Massar', 'Nom'], as_index=False).size()
        student_absences.columns = ['Code Massar', 'Nom', "Nombre d'absences"]
        student_absences = student_absences.sort_values("Nombre d'absences", ascending=False)
        
        # Display detailed student statistics
        st.subheader("Détail des absences par élève")
        st.dataframe(student_absences, use_container_width=True)
        
        # Absence trend visualization
        if len(student_absences) > 0:
            fig = px.bar(
                student_absences, 
                x='Nom', 
                y="Nombre d'absences",
                title="Nombre d'absences par élève",
                labels={"Nom": "Nom de l'élève", "Nombre d'absences": "Nombre d'absences"}
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erreur lors de l'affichage des statistiques: {str(e)}")


def show_settings():
    st.subheader("⚙️ Paramètres")
    
    settings = load_settings()
    
    # Notification Settings
    st.subheader("Notifications")
    settings['email_notifications'] = st.toggle(
        "Activer les notifications par email",
        value=settings.get('email_notifications', False)
    )
    
    if settings['email_notifications']:
        settings['email'] = st.text_input(
            "Email pour les notifications",
            value=settings.get('email', '')
        )
    
    # Data Retention
    st.subheader("Conservation des données")
    settings['data_retention_days'] = st.number_input(
        "Nombre de jours de conservation des données",
        min_value=30,
        value=settings.get('data_retention_days', 365)
    )
    
    # Save Settings
    if st.button("Sauvegarder les paramètres"):
        save_settings(settings)
        st.success("Paramètres sauvegardés avec succès!")




def main():
    st.set_page_config(
        page_title="Système de Gestion des Présences",
        page_icon="📚",
        layout="wide"
    )
    
    init_directories()
    apply_custom_theme()

        # Check authentication
    if not check_authentication():
        show_login()
        return
    
    # Show logout button in sidebar
    st.sidebar.write(f"👤 Connected as: {st.session_state.user_name}")
    logout()
    
    
    st.title("📚 Système de Gestion des Présences")
    
    # Enhanced navigation
    #menu = st.sidebar.selectbox(
     #   "Navigation",
      #  ["Gestion des Classes", "Gestion des Présences", "Statistiques", "Paramètres"]
    #)
    
    #if menu == "Gestion des Classes":
     #   show_class_management()
    #elif menu == "Gestion des Présences":
     #   show_attendance_management()
    #elif menu == "Statistiques":
     #   show_statistics()
    #else:
     #   show_settings()


    # Enhanced navigation with role-based access
    menu_options = ["Gestion des Classes", "Gestion des Présences", "Statistiques"]
    if st.session_state.user_role == "admin":
        menu_options.append("Gestion des Utilisateurs")
        menu_options.append("Paramètres")
    
    menu = st.sidebar.selectbox("Navigation", menu_options)
    
    if menu == "Gestion des Classes":
        show_class_management()
    elif menu == "Gestion des Présences":
        show_attendance_management()
    elif menu == "Statistiques":
        show_statistics()
    elif menu == "Gestion des Utilisateurs" and st.session_state.user_role == "admin":
        show_user_management()
    elif menu == "Paramètres" and st.session_state.user_role == "admin":
        show_settings()

if __name__ == "__main__":
    main()