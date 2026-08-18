import streamlit as st
import pandas as pd
import os
from draft_optimizer import DraftOptimizer

# --- UI Configuration ---
st.set_page_config(page_title="Draft Optimizer", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Modern Light Design ---
st.markdown("""
    <style>
    /* Clean, Cohesive Blue & Slate Palette */
    .stApp {
        background-color: #f8fafc;
        color: #334155;
    }
    h1, h2, h3 {
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1d4ed8; /* Cohesive deep blue */
    }
    .metric-label {
        font-size: 0.95rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
    }
    /* Hero section specific styles */
    .hero-card {
        background: linear-gradient(135deg, #1e3a8a, #2563eb); /* Sleek blue gradient */
        border: none;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        text-align: center;
        color: #ffffff;
    }
    .hero-card .hero-title {
        font-size: 1.2rem;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 2px;
        color: #bfdbfe;
        margin-bottom: 8px;
    }
    .hero-card .hero-name {
        font-size: 3.5rem;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 4px;
        line-height: 1.1;
    }
    .hero-card .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 600;
        color: #93c5fd;
    }
    .hero-card .hero-metric-value {
        font-size: 2.2rem;
        font-weight: 900;
        color: #ffffff;
    }
    .hero-card .hero-metric-label {
        font-size: 0.9rem;
        color: #bfdbfe;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/43/ESPN_Fantasy_Sports_logo.svg", width=150)
st.sidebar.title("Settings")

# Helper to calculate snake draft turns
def calculate_turns_until_pick(league_size, my_pos, current_pick):
    turns = 0
    pick = current_pick
    
    while True:
        round_num = (pick - 1) // league_size + 1
        if round_num % 2 != 0:
            team_on_clock = ((pick - 1) % league_size) + 1
        else:
            team_on_clock = league_size - ((pick - 1) % league_size)
            
        if team_on_clock == my_pos:
            return turns
        turns += 1
        pick += 1

league_size = st.sidebar.number_input("League Size", min_value=4, max_value=32, value=12)
my_draft_position = st.sidebar.number_input("My Draft Position", min_value=1, max_value=league_size, value=1)
    
# We will compute my_pick dynamically
my_pick = 0 # Default placeholder

st.sidebar.markdown("---")

st.sidebar.subheader("Draft Settings")
if st.sidebar.button("Reset Draft"):
    if 'mock_available' in st.session_state:
        del st.session_state['mock_available']
    if 'my_team' in st.session_state:
        del st.session_state['my_team']

# --- Main Dashboard ---
st.title("Fantasy Football Draft Optimizer")
st.markdown("Leverage Machine Learning and Monte Carlo simulations to make the optimal pick.")

# Helper to render the recommendation board
def render_board(df, my_roster=None):
    if df.empty:
        st.warning("No players available to recommend.")
        return
        
    optimizer = DraftOptimizer()
    recommendations = optimizer.get_recommendations(df, my_next_pick_in_x_turns=my_pick, my_roster=my_roster)
    top_pick = recommendations.iloc[0]
    
    # --- Hero Section: Top Recommendation ---
    st.markdown(f"""
        <div class="hero-card" style="margin-bottom: 40px;">
            <div class="hero-title">Optimal Next Pick</div>
            <div class="hero-name">{top_pick['name']}</div>
            <div class="hero-subtitle">{top_pick['position']} - {top_pick['pro_team']}</div>
            <div style="display: flex; justify-content: center; gap: 40px; margin-top: 24px;">
                <div>
                    <div class="hero-metric-value">{top_pick['projected_points']:.1f}</div>
                    <div class="hero-metric-label">AI Proj Pts</div>
                </div>
                <div>
                    <div class="hero-metric-value">{top_pick['vor']:.1f}</div>
                    <div class="hero-metric-label">VOR</div>
                </div>
                <div>
                    <div class="hero-metric-value">{top_pick['survival_prob']*100:.0f}%</div>
                    <div class="hero-metric-label">Survival Prob</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # --- Detailed Board ---
    st.markdown("### Top Available Players")
    display_df = recommendations[['name', 'position', 'pro_team', 'projected_points', 'vor', 'survival_prob', 'adjusted_value']].head(20)
    display_df['survival_prob'] = (display_df['survival_prob'] * 100).map('{:.1f}%'.format)
    display_df['projected_points'] = display_df['projected_points'].map('{:.1f}'.format)
    display_df['vor'] = display_df['vor'].map('{:.1f}'.format)
    display_df['adjusted_value'] = display_df['adjusted_value'].map('{:.1f}'.format)
    
    st.dataframe(
        display_df,
        column_config={
            "name": "Player Name",
            "position": "Position",
            "pro_team": "Team",
            "projected_points": "AI Proj. Points",
            "vor": "VOR",
            "survival_prob": "Survival %",
            "adjusted_value": "Value Score"
        },
        hide_index=True,
        width="stretch"
    )

# Initialize State
if 'mock_available' not in st.session_state:
    try:
        projections_df = pd.read_csv('../data/projections.csv')
        # Deduplicate by name just in case
        projections_df = projections_df.drop_duplicates(subset=['name'])
        st.session_state['mock_available'] = projections_df
        st.session_state['mock_initial_size'] = len(projections_df)
        st.session_state['my_team'] = []
    except FileNotFoundError:
        st.error("Projections file not found. Please run 'python src/fetch_player_pool.py' first.")
        st.stop()
        
available_df = st.session_state['mock_available']

# Calculate current pick number
current_pick_number = st.session_state['mock_initial_size'] - len(available_df) + 1
my_pick = calculate_turns_until_pick(league_size, my_draft_position, current_pick_number)

st.markdown(f"**Draft Info:** Currently on pick **#{current_pick_number}**. Your next turn is in **{my_pick}** pick(s).")

# Manual Draft UI
st.markdown("### Manual Draft Action")
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    # Create a nice display name for the dropdown
    options = available_df['name'] + " (" + available_df['position'] + ") - Proj: " + available_df['projected_points'].round(1).astype(str)
    selected_display = st.selectbox("Select Player Drafted", options=options, index=None, placeholder="Search for a player...")

if selected_display:
    # Extract just the name from the display string, stripping any trailing spaces
    selected_name = selected_display.split(" (")[0].strip()
    selected_pos = available_df[available_df['name'] == selected_name]['position'].iloc[0]
    
    with col2:
        if st.button("Drafted by Me", width="stretch"):
            st.session_state['my_team'].append({'name': selected_name, 'position': selected_pos})
            st.session_state['mock_available'] = available_df[available_df['name'] != selected_name]
            st.rerun()
            
    with col3:
        if st.button("Drafted by Opponent", width="stretch"):
            st.session_state['mock_available'] = available_df[available_df['name'] != selected_name]
            st.rerun()
            
st.markdown("---")

# Show my team
if st.session_state['my_team']:
    team_display = []
    for p in st.session_state['my_team']:
        if isinstance(p, dict):
            team_display.append(f"{p['name']} ({p['position']})")
        else:
            team_display.append(str(p))
    st.markdown(f"**My Team:** {', '.join(team_display)}")
    
render_board(st.session_state['mock_available'], my_roster=st.session_state['my_team'])
