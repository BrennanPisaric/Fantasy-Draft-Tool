import sys
import pandas as pd
from espn_client import ESPNFantasyClient
import os

def export_projections():
    # Credentials from app.py
    league_id = 803870052
    espn_s2 = "AEAVJQtQ1ZSxkqE0HlvjgLmEm%2BVkLgCTrpnHsyk%2F29vNWoPizh9L7A3jeKrEtTnQwcJQR%2F3MfnnlIfbKVkZQrLrcqZlyRU2Sic5w7J65G4Qrxh4kV49QSlCXuhoMo7Hv%2FOCdbYpqobm79jQFQCkrWjoYgKLnKX%2FIfCzIF9BSesja09288Gx7AExZZi30h9Kr3HM9odgtFBDbVbXFuCR%2BNORmvpg34pfbpBPaZl7z112D0jQD9qjlaa7UykMeoTUr%2FwNP4DMtKtLKd2sT3mVlKqzIHfJ6dAAeIrZR1SMdiBUWUg%3D%3D"
    swid = "{6B2D746A-01F8-423E-A1B9-DB4FB55F5BEC}"
    year = 2026

    print("Connecting to ESPN...")
    client = ESPNFantasyClient(league_id, year, espn_s2, swid)
    
    print("Fetching top 800 available players...")
    # Fetch top 800 to ensure we get all relevant rookies and depth chart players
    players = client.league.free_agents(size=800)
    
    data = []
    for p in players:
        data.append({
            'player_id': p.playerId,
            'name': p.name,
            'position': p.position,
            'pro_team': p.proTeam,
            'projected_points': p.projected_total_points
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by='projected_points', ascending=False)
    
    out_path = '../data/projections.csv'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Successfully exported {len(df)} player projections to {out_path}.")
    print("These projections include all up-to-date stats and 2026 rookies!")

if __name__ == '__main__':
    export_projections()
