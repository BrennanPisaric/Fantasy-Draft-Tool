import os
from espn_api.football import League

class ESPNFantasyClient:
    def __init__(self, league_id: int, year: int, espn_s2: str, swid: str):
        self.league_id = league_id
        self.year = year
        self.espn_s2 = espn_s2
        self.swid = swid
        
        try:
            self.league = League(
                league_id=self.league_id, 
                year=self.year, 
                espn_s2=self.espn_s2, 
                swid=self.swid
            )
            print(f"Successfully connected to league: {self.league.settings.name}")
        except Exception as e:
            print(f"Failed to connect to ESPN: {e}")
            raise

    def get_league_settings(self):
        """Returns relevant league settings."""
        settings = self.league.settings
        
        # ESPN API versions handle roster differently, so we omit it here 
        # since the UI only needs the league name and team count currently.
        return {
            "name": getattr(settings, 'name', 'Unknown League'),
            "team_count": getattr(settings, 'team_count', 12),
            "scoring_format": "PPR"
        }
        
    def get_teams(self):
        """Returns a list of teams in the league."""
        return self.league.teams

    def get_draft_order(self):
        """Attempts to retrieve the draft order if available."""
        # ESPN API draft info
        try:
            return self.league.draft
        except Exception as e:
            print(f"Draft info not yet available: {e}")
            return []
            
    def get_available_players(self):
        """Fetches available free agents (bypassing espn_api cache with a raw HTTP request)."""
        import requests
        import json
        from espn_api.football.constant import PRO_TEAM_MAP, POSITION_MAP
        
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{self.year}/segments/0/leagues/{self.league_id}"
        
        x_fantasy_filter = {
            "players": {
                "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
                "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "STANDARD"},
                "limit": 300
            }
        }
        
        headers = {
            "X-Fantasy-Filter": json.dumps(x_fantasy_filter)
        }
        
        cookies = {
            "swid": self.swid,
            "espn_s2": self.espn_s2
        }
        
        params = {
            "view": "kona_player_info"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, cookies=cookies)
            response.raise_for_status()
            data = response.json()
            
            class RawPlayer:
                def __init__(self):
                    self.name = ""
                    self.position = ""
                    self.proTeam = ""
                    self.projected_total_points = 0.0
                
            available = []
            for player_data in data.get("players", []):
                # The crucial filter: drops anyone who has an onTeamId > 0 (meaning drafted)
                if player_data.get("onTeamId", 0) > 0:
                    continue
                    
                p = player_data.get("player", {})
                obj = RawPlayer()
                obj.name = p.get("fullName", "Unknown")
                obj.position = str(POSITION_MAP.get(p.get("defaultPositionId", 0), "UNK"))
                obj.proTeam = PRO_TEAM_MAP.get(p.get("proTeamId", 0), "UNK")
                
                obj.projected_total_points = 0.0
                for stat in p.get("stats", []):
                    # We are looking for projections (statSourceId == 1) for the current year
                    if stat.get("statSourceId") == 1 and stat.get("statSplitTypeId") == 0 and stat.get("seasonId") == self.year:
                        obj.projected_total_points = stat.get("appliedTotal", 0.0)
                        break
                        
                available.append(obj)
                
            return available
        except Exception as e:
            print(f"Failed to fetch raw players: {e}")
            # Fallback to espn-api if the raw request fails
            return self.league.free_agents(size=300)

if __name__ == "__main__":
    # Test the client
    # Using the credentials provided by the user
    league_id = 803870052
    espn_s2 = "AEAVJQtQ1ZSxkqE0HlvjgLmEm%2BVkLgCTrpnHsyk%2F29vNWoPizh9L7A3jeKrEtTnQwcJQR%2F3MfnnlIfbKVkZQrLrcqZlyRU2Sic5w7J65G4Qrxh4kV49QSlCXuhoMo7Hv%2FOCdbYpqobm79jQFQCkrWjoYgKLnKX%2FIfCzIF9BSesja09288Gx7AExZZi30h9Kr3HM9odgtFBDbVbXFuCR%2BNORmvpg34pfbpBPaZl7z112D0jQD9qjlaa7UykMeoTUr%2FwNP4DMtKtLKd2sT3mVlKqzIHfJ6dAAeIrZR1SMdiBUWUg%3D%3D"
    swid = "{6B2D746A-01F8-423E-A1B9-DB4FB55F5BEC}"
    year = 2026 # Current fantasy football year
    
    client = ESPNFantasyClient(league_id, year, espn_s2, swid)
    print(client.get_league_settings())
