-- Enable Row Level Security (RLS) for all tables flagged by the Supabase linter

-- Core operational tables
ALTER TABLE public.routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vessels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vessel_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.port_status ENABLE ROW LEVEL SECURITY;

-- Analytics & Risk tables
ALTER TABLE public.risk_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.route_transits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.historical_disruptions ENABLE ROW LEVEL SECURITY;

-- Collected external data tables
ALTER TABLE public.weather_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weather_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collected_weather ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.geopolitical_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collected_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collected_economics ENABLE ROW LEVEL SECURITY;

-- Manual input/override tables
ALTER TABLE public.port_congestion ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.manual_port_congestion ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.manual_shipping_rates ENABLE ROW LEVEL SECURITY;

-- Kaggle/Imported dataset tables
ALTER TABLE public.kaggle_port_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kaggle_logistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kaggle_supply_chain ENABLE ROW LEVEL SECURITY;

-- Note on Policies:
-- Enabling RLS blocks ALL access to these tables from the Supabase Data API (PostgREST)
-- unless explicit policies are created. 
-- Since the backend uses the service_role key (which bypasses RLS), 
-- the application will continue to work normally, but direct public API access is now secured.
