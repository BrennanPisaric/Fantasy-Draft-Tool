import pandas as pd
import numpy as np
import random

class DraftOptimizer:
    def __init__(self, league_size=12, roster_spots=16):
        self.league_size = league_size
        self.roster_spots = roster_spots
        
        # Baseline ranks for VOR calculation (2 QB, 2 RB, 2 WR, 1 TE, 1 Flex)
        self.baseline_ranks = {
            'QB': 24, # 2 starting QBs * 12 teams
            'RB': 30, # 2 starting RBs + half of the flex spots
            'WR': 30, # 2 starting WRs + half of the flex spots
            'TE': 12, # 1 starting TE
            'K': 12,
            'D/ST': 12
        }

    def calculate_vor(self, players_df):
        """
        Calculates Value Over Replacement (VOR) for all players.
        players_df must have columns: 'name', 'position', 'projected_points'
        """
        # Calculate baseline points for each position
        baselines = {}
        for pos, rank in self.baseline_ranks.items():
            pos_players = players_df[players_df['position'] == pos].sort_values(by='projected_points', ascending=False)
            if len(pos_players) >= rank:
                baselines[pos] = pos_players.iloc[rank - 1]['projected_points']
            elif len(pos_players) > 0:
                baselines[pos] = pos_players.iloc[-1]['projected_points']
            else:
                baselines[pos] = 0

        # Calculate VOR
        players_df['vor'] = players_df.apply(
            lambda row: row['projected_points'] - baselines.get(row['position'], 0), axis=1
        )
        
        return players_df.sort_values(by='vor', ascending=False)

    def monte_carlo_survival(self, available_players, my_next_pick_in_x_turns, iterations=1000):
        """
        Simulates the draft between current pick and the user's next pick
        to calculate the probability a player survives.
        """
        # available_players is sorted by some metric (e.g., ADP or VOR)
        # We will assume opponents pick based on a mix of ADP and randomness
        
        n_players = len(available_players)
        survival_counts = {player['name']: 0.0 for _, player in available_players.iterrows()}
        
        # For simulation, convert to list of names ordered by ADP/Rank for fast sampling
        names = available_players['name'].tolist()
        
        for _ in range(iterations):
            drafted_this_sim = set()
            for _ in range(my_next_pick_in_x_turns):
                # Opponent picks the highest ranked available player with some randomness
                # E.g., they look at top 5 available and pick one
                available_pool = [n for n in names if n not in drafted_this_sim]
                if not available_pool:
                    break
                
                # Pick from top 3 with decreasing probability (60%, 30%, 10%)
                pool_size = min(3, len(available_pool))
                pick_idx = random.choices(range(pool_size), weights=[0.6, 0.3, 0.1][:pool_size], k=1)[0]
                drafted_this_sim.add(available_pool[pick_idx])
            
            # Record who survived
            for name in names:
                if name not in drafted_this_sim:
                    survival_counts[name] += 1
                    
        # Calculate probabilities
        for name in names:
            survival_counts[name] /= iterations
            
        available_players['survival_prob'] = available_players['name'].map(survival_counts)
        return available_players

    def get_recommendations(self, available_players, my_next_pick_in_x_turns, my_roster=None):
        """
        Combines VOR and survival probability to recommend a pick.
        Optionally takes my_roster (list of dictionaries with 'position' key) 
        to penalize drafting too many players at one position.
        """
        # Calculate VOR
        df = self.calculate_vor(available_players.copy())
        
        # Calculate survival probability
        if my_next_pick_in_x_turns > 0:
            df = self.monte_carlo_survival(df, my_next_pick_in_x_turns)
        else:
            df['survival_prob'] = 1.0 # If I have back-to-back picks
            
        # Optimization metric
        df['adjusted_value'] = df['vor'] * (1 - df['survival_prob'].clip(upper=0.95))
        
        # --- Roster Needs Penalty ---
        if my_roster:
            # Count positions currently on my roster
            pos_counts = {}
            for p in my_roster:
                if isinstance(p, dict):
                    pos = p.get('position')
                    if pos:
                        pos_counts[pos] = pos_counts.get(pos, 0) + 1
                
            # Soft caps for typical starting rosters (adjust as needed for flex spots)
            roster_soft_caps = {
                'QB': 3,
                'RB': 4,
                'WR': 4,
                'TE': 2,
                'K': 1,
                'D/ST': 1
            }
            
            # Apply penalties
            def apply_penalty(row):
                pos = row['position']
                count = pos_counts.get(pos, 0)
                cap = roster_soft_caps.get(pos, 1)
                
                value = row['adjusted_value']
                
                # If we've met or exceeded the soft cap, heavily penalize further picks at this position
                if count >= cap:
                    # Penalize more for every player over the cap
                    penalty_factor = 0.2 ** ((count - cap) + 1)
                    if value > 0:
                        value = value * penalty_factor
                    else:
                        value = value * (1 / penalty_factor) # Make negative values even worse
                        
                # Absolute hard caps to prevent stupid recommendations
                if pos in ['K', 'D/ST'] and count >= 1:
                    value = -999 # Never draft a 2nd kicker or defense
                if pos == 'QB' and count >= 4:
                    value = -999 # Rarely need a 5th QB in a 2QB league
                    
                return value
                
            df['adjusted_value'] = df.apply(apply_penalty, axis=1)
        
        return df.sort_values(by='adjusted_value', ascending=False)
