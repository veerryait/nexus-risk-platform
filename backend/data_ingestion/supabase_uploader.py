"""
Supabase Data Uploader
Uploads filtered Kaggle data to Supabase PostgreSQL database
"""

import os
import json
import pandas as pd
from datetime import datetime
from supabase import create_client, Client


class SupabaseUploader:
    """Uploads processed maritime data to Supabase"""
    
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        
        self.client: Client = create_client(self.url, self.key)
        
        # Data directory
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.processed_dir = os.path.join(base, "data", "processed")
    
    def create_tables(self):
        """Create tables if they don't exist using Supabase SQL"""
        # Note: For Supabase, tables should be created via Dashboard or migrations
        # This shows the expected structure
        
        table_schemas = {
            "kaggle_port_activity": """
                id SERIAL PRIMARY KEY,
                date TIMESTAMP,
                year INT,
                month INT,
                day INT,
                port_id VARCHAR(50),
                port_name VARCHAR(255),
                country VARCHAR(100),
                iso3 VARCHAR(10),
                portcalls_container INT,
                portcalls_cargo INT,
                portcalls_total INT,
                import_container FLOAT,
                import_total FLOAT,
                export_container FLOAT,
                export_total FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            """,
            "kaggle_supply_chain": """
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50),
                order_date DATE,
                origin_city VARCHAR(255),
                destination_city VARCHAR(255),
                route_type VARCHAR(50),
                transportation_mode VARCHAR(50),
                product_category VARCHAR(100),
                base_lead_time_days INT,
                scheduled_lead_time_days INT,
                actual_lead_time_days INT,
                delay_days INT,
                delivery_status VARCHAR(50),
                disruption_event VARCHAR(100),
                geopolitical_risk_index FLOAT,
                weather_severity_index FLOAT,
                shipping_cost_usd FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            """,
            "kaggle_port_performance": """
                id SERIAL PRIMARY KEY,
                economy_label VARCHAR(255),
                market_label VARCHAR(100),
                avg_vessel_age_years FLOAT,
                median_time_in_port_days FLOAT,
                avg_vessel_size_gt FLOAT,
                avg_cargo_capacity_dwt FLOAT,
                avg_container_capacity_teu FLOAT,
                period VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            """,
            "kaggle_logistics": """
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                port_congestion_level FLOAT,
                lead_time_days FLOAT,
                delay_probability FLOAT,
                risk_classification VARCHAR(50),
                delivery_time_deviation FLOAT,
                disruption_likelihood_score FLOAT,
                weather_condition_severity FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            """
        }
        
        print("Table schemas prepared. Create these in Supabase Dashboard if needed.")
        return table_schemas
    
    def upload_supply_chain_data(self, batch_size: int = 500) -> dict:
        """Upload supply chain disruption data"""
        filepath = os.path.join(self.processed_dir, "filtered_supply_chain.csv")
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        print(f"Loading supply chain data from {filepath}...")
        df = pd.read_csv(filepath)
        
        # Rename columns to match table schema
        column_mapping = {
            'Order_ID': 'order_id',
            'Order_Date': 'order_date',
            'Origin_City': 'origin_city',
            'Destination_City': 'destination_city',
            'Route_Type': 'route_type',
            'Transportation_Mode': 'transportation_mode',
            'Product_Category': 'product_category',
            'Base_Lead_Time_Days': 'base_lead_time_days',
            'Scheduled_Lead_Time_Days': 'scheduled_lead_time_days',
            'Actual_Lead_Time_Days': 'actual_lead_time_days',
            'Delay_Days': 'delay_days',
            'Delivery_Status': 'delivery_status',
            'Disruption_Event': 'disruption_event',
            'Geopolitical_Risk_Index': 'geopolitical_risk_index',
            'Weather_Severity_Index': 'weather_severity_index',
            'Shipping_Cost_USD': 'shipping_cost_usd',
        }
        
        df = df.rename(columns=column_mapping)
        
        # Select only mapped columns
        cols_to_upload = [c for c in column_mapping.values() if c in df.columns]
        df = df[cols_to_upload]
        
        # Convert to records
        records = df.to_dict('records')
        
        print(f"Uploading {len(records)} records in batches of {batch_size}...")
        
        uploaded = 0
        errors = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                response = self.client.table('kaggle_supply_chain').insert(batch).execute()
                uploaded += len(batch)
                print(f"  Uploaded {uploaded}/{len(records)}")
            except Exception as e:
                errors.append(str(e))
                print(f"  Error uploading batch: {e}")
        
        return {
            "table": "kaggle_supply_chain",
            "total_records": len(records),
            "uploaded": uploaded,
            "errors": errors[:5] if errors else None,
        }
    
    def upload_logistics_data(self, batch_size: int = 1000, limit: int = 10000) -> dict:
        """Upload logistics data (subset to avoid quota issues)"""
        filepath = os.path.join(self.processed_dir, "logistics_data.csv")
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        print(f"Loading logistics data from {filepath}...")
        df = pd.read_csv(filepath)
        
        # Limit records
        if len(df) > limit:
            df = df.head(limit)
            print(f"  Limited to {limit} records")
        
        # Convert to records
        records = df.to_dict('records')
        
        print(f"Uploading {len(records)} records...")
        
        uploaded = 0
        errors = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                response = self.client.table('kaggle_logistics').insert(batch).execute()
                uploaded += len(batch)
                print(f"  Uploaded {uploaded}/{len(records)}")
            except Exception as e:
                errors.append(str(e))
                print(f"  Error: {e}")
        
        return {
            "table": "kaggle_logistics",
            "total_records": len(records),
            "uploaded": uploaded,
            "errors": errors[:5] if errors else None,
        }
    
    def upload_port_performance(self) -> dict:
        """Upload port performance data"""
        filepath = os.path.join(self.processed_dir, "port_performance.csv")
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        print(f"Loading port performance data...")
        df = pd.read_csv(filepath)
        
        # Rename columns
        column_mapping = {
            'Economy_Label': 'economy_label',
            'CommercialMarket_Label': 'market_label',
            'Average_age_of_vessels_years_Value': 'avg_vessel_age_years',
            'Median_time_in_port_days_Value': 'median_time_in_port_days',
            'Average_size_GT_of_vessels_Value': 'avg_vessel_size_gt',
            'Average_cargo_carrying_capacity_dwt_per_vessel_Value': 'avg_cargo_capacity_dwt',
            'Average_container_carrying_capacity_TEU_per_container_ship_Value': 'avg_container_capacity_teu',
            'period': 'period',
        }
        
        df = df.rename(columns=column_mapping)
        cols = [c for c in column_mapping.values() if c in df.columns]
        df = df[cols]
        
        # Replace 'Not available' with None
        df = df.replace('Not available or not separately reported', None)
        
        # Convert numeric columns
        for col in ['avg_vessel_age_years', 'median_time_in_port_days', 'avg_vessel_size_gt', 
                    'avg_cargo_capacity_dwt', 'avg_container_capacity_teu']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        records = df.to_dict('records')
        
        print(f"Uploading {len(records)} records...")
        
        try:
            response = self.client.table('kaggle_port_performance').insert(records).execute()
            return {
                "table": "kaggle_port_performance",
                "uploaded": len(records),
                "success": True,
            }
        except Exception as e:
            return {
                "table": "kaggle_port_performance",
                "error": str(e),
            }
    
    def upload_all(self) -> dict:
        """Upload all datasets to Supabase"""
        results = {}
        
        print("=" * 50)
        print("UPLOADING KAGGLE DATA TO SUPABASE")
        print("=" * 50)
        
        # Upload supply chain first (most relevant)
        print("\n1. Supply Chain Disruption Data")
        results['supply_chain'] = self.upload_supply_chain_data()
        
        # Upload port performance
        print("\n2. Port Performance Data")
        results['port_performance'] = self.upload_port_performance()
        
        # Upload logistics (limited)
        print("\n3. Logistics Data (limited to 10K)")
        results['logistics'] = self.upload_logistics_data(limit=10000)
        
        print("\n" + "=" * 50)
        print("UPLOAD COMPLETE")
        print("=" * 50)
        
        for name, result in results.items():
            if 'error' in result:
                print(f"{name}: ERROR - {result['error']}")
            else:
                print(f"{name}: {result.get('uploaded', 'N/A')} records uploaded")
        
        return results


def main():
    """Upload all data to Supabase"""
    # Credentials
    url = "https://hssnbnsffqorupviykha.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"
    
    uploader = SupabaseUploader(url=url, key=key)
    
    # Show table schemas first
    print("\n=== Table Schemas (create these in Supabase Dashboard) ===")
    schemas = uploader.create_tables()
    for table, schema in schemas.items():
        print(f"\n-- {table}")
        print(f"CREATE TABLE {table} ({schema});")
    
    print("\n\n=== Ready to upload? ===")
    print("First, create these tables in your Supabase Dashboard.")
    print("Then run: python -c \"from data_ingestion.supabase_uploader import main; main()\"")


if __name__ == "__main__":
    main()
