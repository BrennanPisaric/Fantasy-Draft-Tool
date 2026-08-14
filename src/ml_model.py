import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pickle
import os

class FantasyProjectionsModel:
    def __init__(self):
        self.models = {} # We will train a separate model for each position
        self.features_used = {}
        
    def train(self, data_path='../data/historical_stats.csv'):
        """Trains the Random Forest models for each position."""
        if not os.path.exists(data_path):
            print(f"Data file not found at {data_path}. Please run data_pipeline.py first.")
            return False
            
        df = pd.read_csv(data_path)
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']
        for pos in positions:
            pos_df = df[df['position'] == pos].copy()
            if pos_df.empty:
                continue
                
            # Features are stats from Year N. Target is points from Year N+1
            features = pos_df.drop(columns=['player_id', 'player_name', 'season', 'position', 'fantasy_points_ppr', 'target_next_year_points'], errors='ignore')
            features = features.select_dtypes(include=[np.number]).fillna(0)
            
            if 'target_next_year_points' not in pos_df.columns:
                print(f"Target 'target_next_year_points' missing for {pos}")
                continue
                
            target = pos_df['target_next_year_points'].fillna(0)
            self.features_used[pos] = list(features.columns)
            
            X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
            
            model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
            model.fit(X_train, y_train)
            
            preds = model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            print(f"{pos} Model Trained. RMSE: {rmse:.2f}")
            
            self.models[pos] = model
            
        self.save_models()
        return True
        
    def generate_projections(self, inference_path='../data/inference_stats.csv', out_path='../data/projections.csv'):
        """Generates next year's projections using the trained models."""
        if not self.models:
            print("Models not loaded. Loading now...")
            if not self.load_models():
                return False
                
        if not os.path.exists(inference_path):
            print(f"Inference data not found at {inference_path}")
            return False
            
        df = pd.read_csv(inference_path)
        predictions = []
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']
        for pos in positions:
            if pos not in self.models:
                continue
            pos_df = df[df['position'] == pos].copy()
            if pos_df.empty:
                continue
                
            features = pos_df[self.features_used[pos]].fillna(0)
            
            # Predict
            pos_df['projected_points'] = self.models[pos].predict(features)
            
            # Keep only necessary columns for the Mock Draft UI
            result = pos_df[['player_id', 'player_name', 'position', 'projected_points']].copy()
            # Rename for compatibility with the UI
            result = result.rename(columns={'player_name': 'name'})
            # We don't have team easily right now, mock it as FA for now
            result['pro_team'] = 'FA'
            
            predictions.append(result)
            
        if predictions:
            final_projections = pd.concat(predictions, ignore_index=True)
            final_projections = final_projections.sort_values(by='projected_points', ascending=False)
            final_projections.to_csv(out_path, index=False)
            print(f"Generated {len(final_projections)} projections saved to {out_path}")
            return True
        return False
        
    def save_models(self, dir_path='../data'):
        os.makedirs(dir_path, exist_ok=True)
        with open(f'{dir_path}/xgboost_models.pkl', 'wb') as f:
            pickle.dump({'models': self.models, 'features': self.features_used}, f)
        print("Models saved successfully.")
        
    def load_models(self, dir_path='../data'):
        try:
            with open(f'{dir_path}/xgboost_models.pkl', 'rb') as f:
                data = pickle.load(f)
                self.models = data['models']
                self.features_used = data['features']
            return True
        except Exception as e:
            print(f"Failed to load models: {e}")
            return False

if __name__ == "__main__":
    model = FantasyProjectionsModel()
    model.train()
    model.generate_projections()
