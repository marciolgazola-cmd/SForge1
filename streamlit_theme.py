"""
Streamlit Theme Configuration and Custom Styling
Configuração de tema e estilo personalizado para Streamlit
"""

import streamlit as st

def apply_custom_theme():
    """
    Aplica tema personalizado ao Streamlit com melhorias visuais.
    Apply custom theme to Streamlit with visual improvements.
    """
    st.set_page_config(
        page_title="CognitoLink - Synapse Forge Command Center",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado para melhorar a interface
    custom_css = """
    <style>
    /* ====== CORES E VARIÁVEIS ====== */
    :root {
        --primary-color: #1081BA;
        --primary-dark: #0E6DA0;
        --primary-light: #1AA4FF;
        --accent-color: #FF6B6B;
        --success-color: #51CF66;
        --warning-color: #FFD43B;
        --bg-dark: #16171C;
        --bg-secondary: #2D3038;
        --text-light: #AFB1B0;
        --text-primary: #FFFFFF;
    }

    /* ====== MAIN CONTENT ====== */
    .main {
        background: linear-gradient(135deg, #16171C 0%, #1a1b22 100%);
        color: #AFB1B0;
    }

    /* ====== SIDEBAR ====== */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #16171C 0%, #2D3038 100%);
    }

    /* ====== HEADERS E TÍTULOS ====== */
    h1 {
        color: #1AA4FF !important;
        font-size: 2.5em !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(16, 129, 186, 0.2);
        letter-spacing: 1px;
    }

    h2 {
        color: #1AA4FF !important;
        font-size: 1.8em !important;
        font-weight: 600 !important;
        border-left: 4px solid #1AA4FF;
        padding-left: 15px;
        margin-top: 20px;
    }

    h3 {
        color: #FFFFFF !important;
        font-size: 1.3em !important;
        font-weight: 500 !important;
    }

    /* ====== BOTÕES DO STREAMLIT ====== */
    .stButton > button {
        background: linear-gradient(135deg, #1081BA 0%, #0E6DA0 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #1AA4FF !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        cursor: pointer;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(16, 129, 186, 0.2) !important;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1AA4FF 0%, #1081BA 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 129, 186, 0.4) !important;
        border-color: #1AA4FF !important;
    }

    /* ====== INPUTS E TEXT AREAS ====== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        background-color: #2D3038 !important;
        color: #FFFFFF !important;
        border: 2px solid #0E6DA0 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #1AA4FF !important;
        box-shadow: 0 0 10px rgba(26, 164, 255, 0.3) !important;
        background-color: #35394a !important;
    }

    /* ====== LABELS ====== */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stSlider > label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    /* ====== EXPANDERS (ABAS COLAPSÁVEIS) ====== */
    .streamlit-expanderHeader {
        background-color: #2D3038 !important;
        border-radius: 8px !important;
        border: 2px solid #0E6DA0 !important;
        color: #1AA4FF !important;
        font-weight: 600 !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #35394a !important;
        border-color: #1AA4FF !important;
    }

    /* ====== TABS ====== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #2D3038 !important;
        border-radius: 8px !important;
        border: 2px solid #0E6DA0 !important;
        color: #AFB1B0 !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        transition: all 0.3s ease !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1081BA !important;
        border-color: #1AA4FF !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(16, 129, 186, 0.3) !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #35394a !important;
        border-color: #1AA4FF !important;
    }

    /* ====== MÉTRICAS ====== */
    [data-testid="metric-container"] {
        background-color: #2D3038 !important;
        border: 2px solid #0E6DA0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #AFB1B0 !important;
        font-size: 14px !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1AA4FF !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }

    /* ====== ALERTAS E NOTIFICAÇÕES ====== */
    [data-testid="stAlert"] {
        background-color: rgba(26, 164, 255, 0.1) !important;
        border: 2px solid #1AA4FF !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        padding: 15px !important;
    }

    /* Success Alert */
    .streamlit-success {
        background-color: rgba(81, 207, 102, 0.1) !important;
        border-color: #51CF66 !important;
        color: #51CF66 !important;
    }

    /* Error Alert */
    .streamlit-error {
        background-color: rgba(255, 107, 107, 0.1) !important;
        border-color: #FF6B6B !important;
        color: #FF6B6B !important;
    }

    /* Warning Alert */
    .streamlit-warning {
        background-color: rgba(255, 212, 59, 0.1) !important;
        border-color: #FFD43B !important;
        color: #FFD43B !important;
    }

    /* Info Alert */
    .streamlit-info {
        background-color: rgba(26, 164, 255, 0.1) !important;
        border-color: #1AA4FF !important;
        color: #1AA4FF !important;
    }

    /* ====== DIVIDERS ====== */
    .element-container > hr {
        border-color: #0E6DA0 !important;
        border-width: 2px !important;
        margin: 20px 0 !important;
    }

    /* ====== MARKDOWN ====== */
    .markdown-text-container {
        color: #AFB1B0 !important;
    }

    .markdown-text-container p {
        line-height: 1.6;
    }

    .markdown-text-container code {
        background-color: #35394a !important;
        color: #1AA4FF !important;
        border-radius: 4px;
        padding: 2px 6px;
        font-family: 'Courier New', monospace;
    }

    .markdown-text-container pre {
        background-color: #35394a !important;
        border: 2px solid #0E6DA0 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        color: #1AA4FF !important;
    }

    /* ====== PROGRESS BARS ====== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1081BA 0%, #1AA4FF 100%) !important;
        border-radius: 8px !important;
    }

    /* ====== CHECKBOX E RADIO ====== */
    .stCheckbox > label {
        color: #FFFFFF !important;
    }

    .stRadio > label {
        color: #FFFFFF !important;
    }

    /* ====== SLIDERS ====== */
    .stSlider > div > div > div > div {
        color: #1AA4FF !important;
    }

    /* ====== COLUMNS E CONTAINERS ====== */
    .element-container {
        transition: all 0.3s ease;
    }

    [data-testid="stVerticalBlock"] {
        gap: 20px;
    }

    /* ====== FORMS ====== */
    .element-container form {
        background-color: #2D3038;
        border: 2px solid #0E6DA0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    /* ====== SCROLLBAR ====== */
    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #16171C;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #1081BA 0%, #0E6DA0 100%);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #1AA4FF;
    }

    /* ====== ANIMAÇÕES ====== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .element-container {
        animation: fadeIn 0.3s ease;
    }

    /* ====== RESPONSIVE ====== */
    @media (max-width: 768px) {
        h1 {
            font-size: 2em !important;
        }

        h2 {
            font-size: 1.5em !important;
        }

        .stButton > button {
            font-size: 14px !important;
            padding: 10px 16px !important;
        }
    }

    /* ====== EFEITOS DE HOVER GERAL ====== */
    .element-container:hover {
        transition: all 0.3s ease;
    }

    /* ====== SIDEBAR ITEMS ====== */
    .nav-link {
        color: #AFB1B0 !important;
        transition: all 0.3s ease !important;
    }

    .nav-link:hover {
        color: #1AA4FF !important;
        background-color: rgba(26, 164, 255, 0.1) !important;
    }

    .nav-link-selected {
        color: #1AA4FF !important;
        background-color: rgba(26, 164, 255, 0.2) !important;
        border-left: 4px solid #1AA4FF !important;
    }
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)


def format_status(status: str) -> str:
    """
    Formata o status com emoji apropriado.
    Format status with appropriate emoji.
    
    Args:
        status: Status string
    
    Returns:
        Formatted status string with emoji
    """
    status_map = {
        "active": "🟢 Ativo",
        "on hold": "🟡 Em Pausa",
        "completed": "✅ Concluído",
        "cancelled": "⛔ Cancelado",
        "pending": "⏳ Pendente",
        "approved": "✅ Aprovado",
        "rejected": "❌ Rejeitado"
    }
    return status_map.get(status, f"❓ {status}")


def format_currency(value: float) -> str:
    """
    Formata valor como moeda brasileira.
    Format value as Brazilian currency.
    
    Args:
        value: Numeric value
    
    Returns:
        Formatted currency string
    """
    if value is None:
        return "R$ 0,00"
    try:
        return f"R$ {float(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def show_success_animation():
    """
    Mostra animação de sucesso.
    Show success animation.
    """
    st.markdown("""
    <div style="text-align: center; animation: fadeIn 0.3s ease;">
        <div style="font-size: 3em; margin: 20px 0;">✅</div>
        <p style="color: #51CF66; font-weight: bold; font-size: 1.2em;">Operação realizada com sucesso!</p>
    </div>
    """, unsafe_allow_html=True)


def show_error_animation():
    """
    Mostra animação de erro.
    Show error animation.
    """
    st.markdown("""
    <div style="text-align: center; animation: fadeIn 0.3s ease;">
        <div style="font-size: 3em; margin: 20px 0;">❌</div>
        <p style="color: #FF6B6B; font-weight: bold; font-size: 1.2em;">Ocorreu um erro!</p>
    </div>
    """, unsafe_allow_html=True)


def create_card(title: str, content: str, icon: str = "📋") -> None:
    """
    Cria um cartão visual personalizado.
    Create a custom visual card.
    
    Args:
        title: Card title
        content: Card content
        icon: Icon emoji
    """
    st.markdown(f"""
    <div style="
        background-color: #2D3038;
        border: 2px solid #0E6DA0;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #1081BA;
            padding-bottom: 10px;
        ">
            <span style="font-size: 2em; margin-right: 10px;">{icon}</span>
            <h3 style="color: #1AA4FF; margin: 0; font-size: 1.3em; font-weight: 600;">{title}</h3>
        </div>
        <p style="color: #AFB1B0; line-height: 1.6; margin: 0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)
