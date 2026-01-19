#!/usr/bin/env python3
"""
Step 4.1: Train ML Models Locally
Models: Logistic Regression, Random Forest, XGBoost
Target: Delay prediction (classification + regression)
"""

import pandas as pd
import numpy as np
import joblib
import time
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report, confusion_matrix
)

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️ XGBoost not installed, skipping XGBoost models")


def load_data():
    """Load training dataset"""
    data_path = Path(__file__).parent.parent / "data" / "training" / "training_dataset.parquet"
    if not data_path.exists():
        data_path = Path(__file__).parent.parent / "data" / "processed" / "engineered_features.csv"
    
    df = pd.read_csv(data_path) if data_path.suffix == '.csv' else pd.read_parquet(data_path)
    return df


def prepare_features(df):
    """Prepare features and target variables"""
    # Feature columns (exclude ID and targets)
    feature_cols = [c for c in df.columns if c not in ['transit_id', 'target_on_time', 'actual_delay_days']]
    
    X = df[feature_cols].fillna(0)
    y_class = df['target_on_time'].fillna(1).astype(int)  # Classification: on-time (1) or delayed (0)
    y_reg = df['actual_delay_days'].fillna(0)  # Regression: delay days
    
    return X, y_class, y_reg, feature_cols


def train_and_evaluate():
    """Train all models and evaluate"""
    print("="*60)
    print("🤖 MODEL TRAINING - Step 4.1")
    print("="*60)
    
    # Load data
    print("\n📥 Loading training data...")
    df = load_data()
    print(f"  ✓ Loaded {len(df)} samples")
    
    # Prepare features
    X, y_class, y_reg, feature_cols = prepare_features(df)
    print(f"  ✓ {len(feature_cols)} features prepared")
    
    # Split data
    X_train, X_test, y_class_train, y_class_test = train_test_split(
        X, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    _, _, y_reg_train, y_reg_test = train_test_split(
        X, y_reg, test_size=0.2, random_state=42
    )
    print(f"  ✓ Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    results = {}
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    # ==================== CLASSIFICATION MODELS ====================
    print("\n" + "="*60)
    print("📊 CLASSIFICATION: Predict On-Time vs Delayed")
    print("="*60)
    
    # 1. Logistic Regression (baseline)
    print("\n1️⃣ Logistic Regression...")
    start = time.time()
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_class_train)
    lr_time = time.time() - start
    
    y_pred_lr = lr.predict(X_test_scaled)
    results['logistic_regression'] = {
        'accuracy': accuracy_score(y_class_test, y_pred_lr),
        'precision': precision_score(y_class_test, y_pred_lr),
        'recall': recall_score(y_class_test, y_pred_lr),
        'f1': f1_score(y_class_test, y_pred_lr),
        'time': lr_time
    }
    print(f"  ✓ Trained in {lr_time:.2f}s")
    print(f"  Accuracy: {results['logistic_regression']['accuracy']:.4f}")
    print(f"  F1 Score: {results['logistic_regression']['f1']:.4f}")
    
    # 2. Random Forest
    print("\n2️⃣ Random Forest...")
    start = time.time()
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1  # Use all cores
    )
    rf.fit(X_train, y_class_train)
    rf_time = time.time() - start
    
    y_pred_rf = rf.predict(X_test)
    results['random_forest'] = {
        'accuracy': accuracy_score(y_class_test, y_pred_rf),
        'precision': precision_score(y_class_test, y_pred_rf),
        'recall': recall_score(y_class_test, y_pred_rf),
        'f1': f1_score(y_class_test, y_pred_rf),
        'time': rf_time
    }
    print(f"  ✓ Trained in {rf_time:.2f}s")
    print(f"  Accuracy: {results['random_forest']['accuracy']:.4f}")
    print(f"  F1 Score: {results['random_forest']['f1']:.4f}")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\n  Top 5 Features:")
    for i, row in importance.head(5).iterrows():
        print(f"    {row['feature']}: {row['importance']:.4f}")
    
    # 3. XGBoost
    if HAS_XGBOOST:
        print("\n3️⃣ XGBoost...")
        start = time.time()
        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        xgb.fit(X_train, y_class_train)
        xgb_time = time.time() - start
        
        y_pred_xgb = xgb.predict(X_test)
        results['xgboost'] = {
            'accuracy': accuracy_score(y_class_test, y_pred_xgb),
            'precision': precision_score(y_class_test, y_pred_xgb),
            'recall': recall_score(y_class_test, y_pred_xgb),
            'f1': f1_score(y_class_test, y_pred_xgb),
            'time': xgb_time
        }
        print(f"  ✓ Trained in {xgb_time:.2f}s")
        print(f"  Accuracy: {results['xgboost']['accuracy']:.4f}")
        print(f"  F1 Score: {results['xgboost']['f1']:.4f}")
    
    # ==================== REGRESSION MODEL ====================
    print("\n" + "="*60)
    print("📈 REGRESSION: Predict Delay Days")
    print("="*60)
    
    print("\n4️⃣ Random Forest Regressor...")
    start = time.time()
    rf_reg = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf_reg.fit(X_train, y_reg_train)
    rf_reg_time = time.time() - start
    
    y_pred_reg = rf_reg.predict(X_test)
    results['rf_regressor'] = {
        'mae': mean_absolute_error(y_reg_test, y_pred_reg),
        'rmse': np.sqrt(mean_squared_error(y_reg_test, y_pred_reg)),
        'r2': r2_score(y_reg_test, y_pred_reg),
        'time': rf_reg_time
    }
    print(f"  ✓ Trained in {rf_reg_time:.2f}s")
    print(f"  MAE: {results['rf_regressor']['mae']:.4f} days")
    print(f"  RMSE: {results['rf_regressor']['rmse']:.4f} days")
    print(f"  R²: {results['rf_regressor']['r2']:.4f}")
    
    # ==================== SAVE BEST MODEL ====================
    print("\n" + "="*60)
    print("💾 SAVING BEST MODEL")
    print("="*60)
    
    # Find best classification model
    class_models = {k: v for k, v in results.items() if 'f1' in v}
    best_name = max(class_models, key=lambda k: class_models[k]['f1'])
    best_model = {'logistic_regression': lr, 'random_forest': rf, 'xgboost': xgb if HAS_XGBOOST else None}[best_name]
    
    # Save models
    joblib.dump(scaler, models_dir / 'scaler.joblib')
    joblib.dump(rf, models_dir / 'random_forest_classifier.joblib')
    joblib.dump(rf_reg, models_dir / 'random_forest_regressor.joblib')
    if HAS_XGBOOST:
        joblib.dump(xgb, models_dir / 'xgboost_classifier.joblib')
    
    # Save feature names
    with open(models_dir / 'feature_names.txt', 'w') as f:
        f.write('\n'.join(feature_cols))
    
    print(f"\n✅ Models saved to: {models_dir}")
    for f in models_dir.glob('*.joblib'):
        size = f.stat().st_size / 1024 / 1024
        print(f"  - {f.name} ({size:.2f} MB)")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*60)
    print("📊 MODEL COMPARISON SUMMARY")
    print("="*60)
    
    print("\nClassification Models:")
    print(f"{'Model':<25} {'Accuracy':>10} {'F1':>10} {'Time':>10}")
    print("-"*55)
    for name in ['logistic_regression', 'random_forest', 'xgboost']:
        if name in results:
            r = results[name]
            print(f"{name:<25} {r['accuracy']:>10.4f} {r['f1']:>10.4f} {r['time']:>9.2f}s")
    
    print(f"\n🏆 Best Model: {best_name} (F1: {results[best_name]['f1']:.4f})")
    
    print("\nRegression Model:")
    print(f"  MAE: {results['rf_regressor']['mae']:.4f} days")
    print(f"  RMSE: {results['rf_regressor']['rmse']:.4f} days")
    
    return results, rf, rf_reg, scaler, feature_cols


if __name__ == "__main__":
    results, classifier, regressor, scaler, features = train_and_evaluate()
