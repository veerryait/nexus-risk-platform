"""
Kaggle Data Loader and Processor
Loads downloaded Kaggle datasets and filters for Taiwan → US West Coast routes
"""

import os
import csv
import json
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class KaggleDataLoader:
    """Loads and processes Kaggle maritime datasets"""
    
    # Taiwan and US West Coast port names/countries to filter
    TAIWAN_IDENTIFIERS = ["Taiwan", "TW", "TWN", "Kaohsiung", "Taipei", "Taichung", "Keelung"]
    US_WEST_COAST_IDENTIFIERS = ["Los Angeles", "Long Beach", "Oakland", "Seattle", "LA", "US", "USA", "United States"]
    ASIA_PACIFIC_COUNTRIES = ["Taiwan", "China", "Japan", "Korea", "Singapore", "Vietnam", "Thailand", "CN", "JP", "KR", "SG"]
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.raw_dir = os.path.join(base, "data", "raw")
            self.processed_dir = os.path.join(base, "data", "processed")
        else:
            self.raw_dir = os.path.join(data_dir, "raw")
            self.processed_dir = os.path.join(data_dir, "processed")
        
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def load_port_activity(self) -> pd.DataFrame:
        """Load and filter Daily Port Activity dataset"""
        filepath = os.path.join(self.raw_dir, "Daily_Port_Activity_Data_and_Trade_Estimates.csv")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return pd.DataFrame()
        
        print(f"Loading Port Activity data from {filepath}...")
        
        # Load in chunks due to large size
        chunks = []
        chunk_size = 100000
        
        for chunk in pd.read_csv(filepath, chunksize=chunk_size, low_memory=False):
            # Filter for Taiwan and US West Coast ports
            mask = (
                chunk['country'].isin(['Taiwan', 'Taiwan, Province of China', 'United States']) |
                chunk['portname'].str.contains('|'.join(self.TAIWAN_IDENTIFIERS), case=False, na=False) |
                chunk['portname'].str.contains('|'.join(['Los Angeles', 'Long Beach', 'Oakland', 'Seattle']), case=False, na=False)
            )
            filtered = chunk[mask]
            if not filtered.empty:
                chunks.append(filtered)
        
        if chunks:
            df = pd.concat(chunks, ignore_index=True)
            print(f"  Filtered to {len(df)} records for Taiwan/US ports")
            return df
        
        return pd.DataFrame()
    
    def load_supply_chain_disruption(self) -> pd.DataFrame:
        """Load and filter Supply Chain Disruption dataset"""
        filepath = os.path.join(self.raw_dir, "global_supply_chain_disruption_v1.csv")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return pd.DataFrame()
        
        print(f"Loading Supply Chain Disruption data...")
        df = pd.read_csv(filepath)
        
        # Filter for Asia → US routes (Pacific routes similar to Taiwan)
        mask = (
            (df['Origin_City'].str.contains('|'.join(['CN', 'JP', 'TW', 'KR', 'SG', 'Shanghai', 'Tokyo', 'Taipei']), case=False, na=False)) &
            (df['Destination_City'].str.contains('|'.join(['US', 'Los Angeles', 'Long Beach', 'Seattle']), case=False, na=False))
        )
        
        filtered = df[mask].copy()
        print(f"  Filtered to {len(filtered)} Pacific route records")
        return filtered
    
    def load_port_performance(self) -> pd.DataFrame:
        """Load Maritime Port Performance dataset"""
        filepath = os.path.join(self.raw_dir, "Maritime Port Performance Project Dataset.csv")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return pd.DataFrame()
        
        print(f"Loading Port Performance data...")
        df = pd.read_csv(filepath)
        print(f"  Loaded {len(df)} port performance records")
        return df
    
    def load_logistics_data(self) -> pd.DataFrame:
        """Load Logistics Supply Chain dataset"""
        filepath = os.path.join(self.raw_dir, "dynamic_supply_chain_logistics_dataset.csv")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return pd.DataFrame()
        
        print(f"Loading Logistics data...")
        df = pd.read_csv(filepath)
        
        # This dataset has port congestion, delay probability, risk scores
        # Select relevant columns
        if 'port_congestion_level' in df.columns:
            df = df[['timestamp', 'port_congestion_level', 'lead_time_days', 
                     'delay_probability', 'risk_classification', 'delivery_time_deviation',
                     'disruption_likelihood_score', 'weather_condition_severity']].copy()
        
        print(f"  Loaded {len(df)} logistics records")
        return df
    
    def process_all(self) -> Dict:
        """Process all datasets and save filtered versions"""
        results = {
            "port_activity": None,
            "supply_chain": None,
            "port_performance": None,
            "logistics": None,
        }
        
        # Port Activity
        port_df = self.load_port_activity()
        if not port_df.empty:
            output_path = os.path.join(self.processed_dir, "filtered_port_activity.csv")
            port_df.to_csv(output_path, index=False)
            results["port_activity"] = {
                "records": len(port_df),
                "path": output_path,
                "ports": port_df['portname'].unique().tolist()[:20],
            }
        
        # Supply Chain Disruption
        sc_df = self.load_supply_chain_disruption()
        if not sc_df.empty:
            output_path = os.path.join(self.processed_dir, "filtered_supply_chain.csv")
            sc_df.to_csv(output_path, index=False)
            
            # Calculate statistics
            delay_stats = {
                "avg_delay_days": round(sc_df['Delay_Days'].mean(), 2),
                "max_delay_days": int(sc_df['Delay_Days'].max()),
                "on_time_rate": round((sc_df['Delay_Days'] == 0).mean(), 3),
            }
            
            results["supply_chain"] = {
                "records": len(sc_df),
                "path": output_path,
                "delay_stats": delay_stats,
                "routes": sc_df[['Origin_City', 'Destination_City']].drop_duplicates().head(10).to_dict('records'),
            }
        
        # Port Performance
        perf_df = self.load_port_performance()
        if not perf_df.empty:
            output_path = os.path.join(self.processed_dir, "port_performance.csv")
            perf_df.to_csv(output_path, index=False)
            results["port_performance"] = {
                "records": len(perf_df),
                "path": output_path,
            }
        
        # Logistics
        log_df = self.load_logistics_data()
        if not log_df.empty:
            output_path = os.path.join(self.processed_dir, "logistics_data.csv")
            log_df.to_csv(output_path, index=False)
            results["logistics"] = {
                "records": len(log_df),
                "path": output_path,
                "avg_delay_probability": round(log_df['delay_probability'].mean(), 3) if 'delay_probability' in log_df.columns else None,
            }
        
        # Save summary
        summary_path = os.path.join(self.processed_dir, "kaggle_data_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n=== Processing Complete ===")
        print(f"Summary saved to: {summary_path}")
        
        return results
    
    def get_taiwan_us_statistics(self) -> Dict:
        """Get statistics specifically for Taiwan-US routes"""
        sc_df = self.load_supply_chain_disruption()
        
        if sc_df.empty:
            return {"error": "No supply chain data loaded"}
        
        # Group by route
        route_stats = sc_df.groupby(['Origin_City', 'Destination_City']).agg({
            'Delay_Days': ['mean', 'max', 'count'],
            'Geopolitical_Risk_Index': 'mean',
            'Weather_Severity_Index': 'mean',
            'Shipping_Cost_USD': 'mean',
        }).round(2)
        
        return {
            "total_shipments": len(sc_df),
            "avg_delay": round(sc_df['Delay_Days'].mean(), 2),
            "on_time_rate": round((sc_df['Delay_Days'] == 0).mean() * 100, 1),
            "disruption_events": sc_df['Disruption_Event'].value_counts().to_dict(),
            "transport_modes": sc_df['Transportation_Mode'].value_counts().to_dict(),
        }


def main():
    """Process all Kaggle datasets"""
    loader = KaggleDataLoader()
    results = loader.process_all()
    
    print("\n=== Summary ===")
    for name, data in results.items():
        if data:
            print(f"{name}: {data.get('records', 'N/A')} records")
        else:
            print(f"{name}: No data")


if __name__ == "__main__":
    main()
