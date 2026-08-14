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
        rosters = pd.DataFrame(nfl.import_seasonal_rosters(years))
        
        # Merge stats with roster to get player names and positions
        rosters_subset = rosters.drop_duplicates(subset=['player_id', 'season'])[['player_id', 'player_name', 'position', 'season']]
        merged = seasonal_data.merge(rosters_subset, on=['player_id', 'season'], how='left')
        
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
        
        # Data for 2024 will be used to generate projections for 2025 (or current mock draft)
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
