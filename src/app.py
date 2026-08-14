import streamlit as st
import pandas as pd
import os
from espn_client import ESPNFantasyClient
from draft_optimizer import DraftOptimizer

# --- UI Configuration ---
st.set_page_config(page_title="Draft Optimizer 🏈", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Premium Design ---
st.markdown("""
    <style>
    /* Dark theme overrides and vibrant colors */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: rgba(33, 38, 45, 0.7);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #58a6ff;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2ea043;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/43/ESPN_Fantasy_Sports_logo.svg", width=150)
st.sidebar.title("Settings")

mode = st.sidebar.radio("Draft Mode", ["Mock Draft (Manual)", "ESPN Live Sync"])

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

# Initialize variables to avoid "may be uninitialized" warnings
league_size = 12
my_draft_position = 1

if mode == "ESPN Live Sync":
    st.sidebar.subheader("Live Draft Settings")
    league_size = st.sidebar.number_input("League Size", min_value=4, max_value=32, value=12)
    my_draft_position = st.sidebar.number_input("My Draft Position", min_value=1, max_value=league_size, value=1)
    
    if 'client' in st.session_state:
        # Try to automatically determine current pick by counting drafted players
        try:
            drafted_count = sum([len(team.roster) for team in st.session_state['client'].get_teams()])
            default_pick = max(1, drafted_count + 1)
        except:
            default_pick = 1
    else:
        default_pick = 1
        
    current_pick = st.sidebar.number_input("Current Overall Pick", min_value=1, max_value=500, value=default_pick)
    my_pick = calculate_turns_until_pick(league_size, my_draft_position, current_pick)
    st.sidebar.markdown(f"**Calculated:** Next pick is in **{my_pick}** turn(s).")
    
    if st.sidebar.checkbox("Auto-Refresh Board (10s)", value=True):
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, limit=None, key="espn_refresh")
else:
    league_size = st.sidebar.number_input("League Size", min_value=4, max_value=32, value=12)
    my_draft_position = st.sidebar.number_input("My Draft Position", min_value=1, max_value=league_size, value=1)
    
    # We will compute my_pick dynamically in the Mock Draft section
    my_pick = 0 # Default placeholder

st.sidebar.markdown("---")

if mode == "ESPN Live Sync":
    st.sidebar.subheader("ESPN Credentials")
    league_id = st.sidebar.text_input("League ID", value="803870052")
    year = st.sidebar.number_input("Year", min_value=2000, max_value=2030, value=2026)
    espn_s2 = st.sidebar.text_input("espn_s2 Cookie", type="password")
    swid = st.sidebar.text_input("SWID Cookie", type="password")
    
    if st.sidebar.button("Connect to ESPN"):
        try:
            with st.spinner("Authenticating..."):
                client = ESPNFantasyClient(int(league_id), year, espn_s2, swid)
                st.session_state['client'] = client
                st.session_state['league_settings'] = client.get_league_settings()
                st.sidebar.success(f"Connected: {st.session_state['league_settings']['name']}")
        except Exception as e:
            st.sidebar.error(f"Connection Failed: {e}")
else:
    # Mock Draft Mode
    st.sidebar.subheader("Mock Draft Settings")
    if st.sidebar.button("Reset Mock Draft"):
        if 'mock_available' in st.session_state:
            del st.session_state['mock_available']
        if 'my_team' in st.session_state:
            del st.session_state['my_team']

# --- Main Dashboard ---
st.title("🏈 Fantasy Football Draft Optimizer")
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
        <div class="metric-card" style="margin-bottom: 30px; background: linear-gradient(145deg, #1f2937, #111827);">
            <div style="font-size: 1.2rem; color: #9ca3af; margin-bottom: 10px;">⭐ Optimal Next Pick</div>
            <div style="font-size: 3rem; font-weight: 800; color: #60a5fa; margin-bottom: 5px;">{top_pick['name']}</div>
            <div style="font-size: 1.5rem; color: #34d399;">{top_pick['position']} - {top_pick['pro_team']}</div>
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 20px;">
                <div>
                    <div class="metric-value">{top_pick['projected_points']:.1f}</div>
                    <div class="metric-label">AI Proj Pts</div>
                </div>
                <div>
                    <div class="metric-value">{top_pick['vor']:.1f}</div>
                    <div class="metric-label">VOR</div>
                </div>
                <div>
                    <div class="metric-value">{top_pick['survival_prob']*100:.0f}%</div>
                    <div class="metric-label">Survival Prob</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # --- Detailed Board ---
    st.markdown("### 📋 Top Available Players")
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

if mode == "ESPN Live Sync":
    if 'client' in st.session_state:
        header_col, btn_col = st.columns([3, 1])
        with header_col:
            st.markdown("### 📊 Live Draft Board Insights")
        with btn_col:
            refresh_clicked = st.button("🔄 Refresh Data", width="stretch")
            
        # Automatically fetch fresh data on every auto-refresh or manual click
        # so that league.teams and draft pick counts actually update!
        old_client = st.session_state['client']
        try:
            fresh_client = ESPNFantasyClient(
                old_client.league_id, 
                old_client.year, 
                old_client.espn_s2, 
                old_client.swid
            )
            st.session_state['client'] = fresh_client
        except Exception:
            st.warning("⚠️ Could not fetch latest ESPN data. The draft may have concluded.")
        
        current_client = st.session_state['client']
        
        # Determine who has been drafted via the API
        drafted_names = set()
        
        # 1. From rosters (post-draft or keepers)
        for team in current_client.league.teams:
            for p in team.roster:
                drafted_names.add(p.name)
                
        # 2. From live draft picks (during active draft, rosters are often empty)
        try:
            draft_order = current_client.get_draft_order()
            for pick in draft_order:
                name = getattr(pick, 'playerName', getattr(pick, 'name', None))
                if name:
                    drafted_names.add(name)
        except Exception:
            draft_order = []

        # 3. From browser scraper sync file (local server)
        scraped_file = os.path.join(os.path.dirname(__file__), 'drafted_players.txt')
        scraped_texts = []
        my_roster_texts = []
        if os.path.exists(scraped_file):
            try:
                with open(scraped_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            if text.startswith("MY_ROSTER:"):
                                my_roster_texts.append(text.replace("MY_ROSTER:", ""))
                            else:
                                scraped_texts.append(text)
            except Exception:
                pass

        free_agents = current_client.get_available_players()
        
        # If any free agent's name appears anywhere in the scraped texts (or roster), they are drafted!
        new_drafted = set()
        for p in free_agents:
            if any(p.name in text for text in scraped_texts) or any(p.name in text for text in my_roster_texts):
                new_drafted.add(p.name)
        drafted_names.update(new_drafted)
        
        # Create a list of currently available names
        available_names = [p.name for p in free_agents if p.name not in drafted_names]
        
        if 'manually_drafted' not in st.session_state:
            st.session_state['manually_drafted'] = []
            
        st.markdown("#### ✍️ Manual Draft Override")
        st.caption("ESPN's API often lags during live drafts. Use this box to manually remove drafted players from the board.")
        
        # Ensure previously selected players remain in the options list
        options = sorted(list(set(available_names + st.session_state['manually_drafted'])))
        
        selected_manual = st.multiselect(
            "Mark Players as Drafted:",
            options=options,
            default=st.session_state['manually_drafted']
        )
        st.session_state['manually_drafted'] = selected_manual
        
        player_data = []
        for p in free_agents:
            if p.name not in drafted_names and p.name not in st.session_state['manually_drafted']:
                player_data.append({
                    'name': p.name, 
                    'position': p.position, 
                    'pro_team': p.proTeam, 
                    'projected_points': p.projected_total_points
                })
        
        # Find my current roster for penalties so the optimizer knows my positional needs!
        my_team_roster = []
        
        # Build roster from scraped MY_ROSTER texts first!
        for p in free_agents:
            if any(p.name in text for text in my_roster_texts):
                my_team_roster.append({'name': p.name, 'position': p.position})
                
        try:
            # If nothing scraped, fallback to finding the user's team by checking pick order in Round 1
            if not my_team_roster and draft_order and len(draft_order) >= my_draft_position:
                my_team = draft_order[my_draft_position - 1].team
                
                # Check team.roster first (post-draft)
                for p in my_team.roster:
                    my_team_roster.append({'name': p.name, 'position': p.position})
                    
                # If team.roster is empty, extract from draft_order (during draft)
                if not my_team_roster:
                    for pick in draft_order:
                        if pick.team == my_team:
                            name = getattr(pick, 'playerName', getattr(pick, 'name', 'Unknown'))
                            # Find position from free_agents pool
                            pos = 'UNK'
                            for p in free_agents:
                                if p.name == name:
                                    pos = p.position
                                    break
                            my_team_roster.append({'name': name, 'position': pos})
            elif not my_team_roster:
                # Fallback: Just guess the team based on index if draft order isn't fully loaded
                teams = current_client.get_teams()
                if len(teams) >= my_draft_position:
                    my_team = teams[my_draft_position - 1]
                    for p in my_team.roster:
                        my_team_roster.append({'name': p.name, 'position': p.position})
        except Exception as e:
            pass
            
        render_board(pd.DataFrame(player_data), my_roster=my_team_roster)
    else:
        st.info("👈 Enter your ESPN credentials in the sidebar and click 'Connect to ESPN' to load your league.")

elif mode == "Mock Draft (Manual)":
    # Initialize Mock State
    if 'mock_available' not in st.session_state:
        try:
            projections_df = pd.read_csv('../data/projections.csv')
            # Deduplicate by name just in case
            projections_df = projections_df.drop_duplicates(subset=['name'])
            st.session_state['mock_available'] = projections_df
            st.session_state['mock_initial_size'] = len(projections_df)
            st.session_state['my_team'] = []
        except FileNotFoundError:
            st.error("Projections file not found. Please run the ML model training first.")
            st.stop()
            
    available_df = st.session_state['mock_available']
    
    # Calculate current pick number
    current_pick_number = st.session_state['mock_initial_size'] - len(available_df) + 1
    my_pick = calculate_turns_until_pick(league_size, my_draft_position, current_pick_number)
    
    st.markdown(f"**Draft Info:** Currently on pick **#{current_pick_number}**. Your next turn is in **{my_pick}** pick(s).")
    
    # Manual Draft UI
    st.markdown("### ✍️ Manual Draft Action")
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
            if st.button("Drafted by Me 🟢", width="stretch"):
                st.session_state['my_team'].append({'name': selected_name, 'position': selected_pos})
                st.session_state['mock_available'] = available_df[available_df['name'] != selected_name]
                st.rerun()
                
        with col3:
            if st.button("Drafted by Opponent 🔴", width="stretch"):
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
