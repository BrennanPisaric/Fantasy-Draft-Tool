import nfl_data_py as nfl
import pandas as pd
import os

def fetch_historical_data():
    """
    Fetches historical play-by-play data and aggregates it to season-level
    player stats for the ML model (2020-2024).
    """
    years = [2020, 2021, 2022, 2023, 2024]
    print(f"Fetching data for years: {years}...")
    
    try:
        seasonal_data = pd.DataFrame(nfl.import_seasonal_data(years))
        weekly_data = pd.DataFrame(nfl.import_weekly_data(years))
        rosters = pd.DataFrame(nfl.import_seasonal_rosters(years))
        
        # Calculate custom points from weekly data to catch game-level bonuses
        def calc_custom_pts(row):
            pts = 0.0
            # Passing (1 pt per 20 yds)
            pts += row.get('passing_yards', 0) * 0.05
            pts += row.get('passing_tds', 0) * 4.0
            pts += row.get('interceptions', 0) * -2.0
            if row.get('passing_yards', 0) >= 400:
                pts += 3.0
                
            # Rushing (1 pt per 10 yds)
            pts += row.get('rushing_yards', 0) * 0.1
            pts += row.get('rushing_tds', 0) * 6.0
            if row.get('rushing_yards', 0) >= 200:
                pts += 5.0
                
            # Receiving (1 pt per 10 yds, 1 pt PPR)
            pts += row.get('receiving_yards', 0) * 0.1
            pts += row.get('receptions', 0) * 1.0
            pts += row.get('receiving_tds', 0) * 6.0
            if row.get('receiving_yards', 0) >= 200:
                pts += 3.0
                
            # Fumbles
            fumbles_lost = row.get('sack_fumbles_lost', 0) + row.get('rushing_fumbles_lost', 0) + row.get('receiving_fumbles_lost', 0)
            pts += fumbles_lost * -2.0
            
            return pts
            
        weekly_data['custom_pts'] = weekly_data.apply(calc_custom_pts, axis=1)
        
        # Group custom points by player and season
        custom_seasonal = weekly_data.groupby(['player_id', 'season'])['custom_pts'].sum().reset_index()
        
        # Merge stats with roster to get player names and positions
        rosters_subset = rosters.drop_duplicates(subset=['player_id', 'season'])[['player_id', 'player_name', 'position', 'season']]
        merged = seasonal_data.merge(rosters_subset, on=['player_id', 'season'], how='left')
        
        # Merge our custom offensive points
        merged = merged.merge(custom_seasonal, on=['player_id', 'season'], how='left')
        
        # Use custom points for offensive positions, default points for K and D/ST
        def resolve_points(row):
            if row['position'] in ['K', 'D/ST'] or pd.isna(row.get('custom_pts')):
                return row.get('fantasy_points_ppr', 0)
            return row['custom_pts']
            
        merged['fantasy_points_ppr_new'] = merged.apply(resolve_points, axis=1)
        merged = merged.drop(columns=['fantasy_points_ppr', 'custom_pts'])
        merged = merged.rename(columns={'fantasy_points_ppr_new': 'fantasy_points_ppr'})
        
        # Filter for fantasy relevant positions
        relevant_positions = ['QB', 'WR', 'RB', 'TE', 'K', 'D/ST']
        filtered = merged[merged['position'].isin(relevant_positions)].copy()
        
        # Clean data
        filtered = filtered.fillna(0)
        
        # --- Align Data for Next-Year Prediction ---
        # We want to predict Year N+1 fantasy points using Year N stats
        # We need to shift the target variable
        target_df = filtered[['player_id', 'season', 'fantasy_points_ppr']].copy()
        target_df['season'] = target_df['season'] - 1 # Shift so Year N matches Year N+1's points
        target_df = target_df.rename(columns={'fantasy_points_ppr': 'target_next_year_points'})
        
        # Merge target back into the main dataset
        training_set = filtered.merge(target_df, on=['player_id', 'season'], how='inner')
        
        # Data for 2024 will be used to generate projections for 2026 (assuming 2025 doesn't exist)
        inference_set = filtered[filtered['season'] == 2024].copy()
        
        # Save to disk
        os.makedirs('../data', exist_ok=True)
        training_set.to_csv('../data/historical_stats.csv', index=False)
        inference_set.to_csv('../data/inference_stats.csv', index=False)
        
        print(f"Saved {len(training_set)} training records and {len(inference_set)} inference records.")
        return True
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return False

if __name__ == "__main__":
    fetch_historical_data()
