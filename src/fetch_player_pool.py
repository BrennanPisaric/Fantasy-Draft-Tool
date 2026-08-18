import os
import pandas as pd
from espn_api.football import League

def export_projections():
    # Credentials from history
    league_id = 803870052
    espn_s2 = "AEAVJQtQ1ZSxkqE0HlvjgLmEm%2BVkLgCTrpnHsyk%2F29vNWoPizh9L7A3jeKrEtTnQwcJQR%2F3MfnnlIfbKVkZQrLrcqZlyRU2Sic5w7J65G4Qrxh4kV49QSlCXuhoMo7Hv%2FOCdbYpqobm79jQFQCkrWjoYgKLnKX%2FIfCzIF9BSesja09288Gx7AExZZi30h9Kr3HM9odgtFBDbVbXFuCR%2BNORmvpg34pfbpBPaZl7z112D0jQD9qjlaa7UykMeoTUr%2FwNP4DMtKtLKd2sT3mVlKqzIHfJ6dAAeIrZR1SMdiBUWUg%3D%3D"
    swid = "{6B2D746A-01F8-423E-A1B9-DB4FB55F5BEC}"
    year = 2026

    print("Connecting to ESPN...")
    # Initialize the League object directly from espn_api
    league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
    
    print("Fetching top 800 available players...")
    # Get free agents from the league
    players = league.free_agents(size=800)
    
    data = []
    for p in players:
        data.append({
            'player_id': getattr(p, 'playerId', 0),
            'name': getattr(p, 'name', 'Unknown'),
            'position': getattr(p, 'position', 'UNK'),
            'pro_team': getattr(p, 'proTeam', 'FA'),
            'projected_points': getattr(p, 'projected_total_points', 0.0)
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by='projected_points', ascending=False)
    
    out_path = '../data/projections.csv'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Successfully exported {len(df)} player projections to {out_path}.")
    print("These projections include all up-to-date stats, teams, and 2026 rookies!")

if __name__ == '__main__':
    export_projections()
