#!/usr/bin/env python3
"""
Step 4.3: Model Evaluation & Selection
Comprehensive evaluation with risk categories
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report, confusion_matrix, roc_auc_score
)


def load_models():
    """Load trained models"""
    models_dir = Path(__file__).parent.parent / "models"
    
    models = {}
    for model_file in models_dir.glob("*.joblib"):
        name = model_file.stem
        models[name] = joblib.load(model_file)
        print(f"  ✓ Loaded {name}")
    
    # Load feature names
    features_file = models_dir / "feature_names.txt"
    if features_file.exists():
        with open(features_file) as f:
            feature_names = [line.strip() for line in f.readlines()]
    else:
        feature_names = []
    
    return models, feature_names


def load_test_data():
    """Load and prepare test data"""
    data_path = Path(__file__).parent.parent / "data" / "training" / "training_dataset.parquet"
    if not data_path.exists():
        data_path = Path(__file__).parent.parent / "data" / "processed" / "engineered_features.csv"
    
    df = pd.read_csv(data_path) if data_path.suffix == '.csv' else pd.read_parquet(data_path)
    
    # Feature columns
    feature_cols = [c for c in df.columns if c not in ['transit_id', 'target_on_time', 'actual_delay_days']]
    
    X = df[feature_cols].fillna(0)
    y_class = df['target_on_time'].fillna(1).astype(int)
    y_reg = df['actual_delay_days'].fillna(0)
    
    # Split (same seed as training)
    X_train, X_test, y_class_train, y_class_test = train_test_split(
        X, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    _, _, y_reg_train, y_reg_test = train_test_split(
        X, y_reg, test_size=0.2, random_state=42
    )
    
    return X_test, y_class_test, y_reg_test, feature_cols


def calculate_risk_category(delay_days):
    """Categorize risk based on delay days"""
    if delay_days == 0:
        return "Low"
    elif delay_days <= 2:
        return "Medium"
    elif delay_days <= 5:
        return "High"
    else:
        return "Critical"


def evaluate_models():
    """Run comprehensive model evaluation"""
    print("="*60)
    print("📊 MODEL EVALUATION - Step 4.3")
    print("="*60)
    
    # Load models
    print("\n📥 Loading trained models...")
    models, feature_names = load_models()
    
    # Load test data
    print("\n📥 Loading test data...")
    X_test, y_class_test, y_reg_test, feature_cols = load_test_data()
    print(f"  ✓ Test samples: {len(X_test)}")
    
    # Scale for logistic regression
    scaler = models.get('scaler', StandardScaler().fit(X_test))
    X_test_scaled = scaler.transform(X_test)
    
    results = {}
    
    # ==================== CLASSIFICATION EVALUATION ====================
    print("\n" + "="*60)
    print("📊 CLASSIFICATION EVALUATION")
    print("="*60)
    
    classifiers = {
        'random_forest_classifier': X_test,  # doesn't need scaling
        'xgboost_classifier': X_test,
    }
    
    for name, X_data in classifiers.items():
        if name in models:
            print(f"\n🔍 {name}:")
            model = models[name]
            y_pred = model.predict(X_data)
            y_prob = model.predict_proba(X_data)[:, 1] if hasattr(model, 'predict_proba') else y_pred
            
            acc = accuracy_score(y_class_test, y_pred)
            prec = precision_score(y_class_test, y_pred, zero_division=0)
            rec = recall_score(y_class_test, y_pred, zero_division=0)
            f1 = f1_score(y_class_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_class_test, y_prob) if len(np.unique(y_class_test)) > 1 else 0
            
            results[name] = {
                'type': 'classification',
                'accuracy': acc,
                'precision': prec,
                'recall': rec,
                'f1': f1,
                'auc': auc
            }
            
            print(f"  Accuracy:  {acc:.4f}")
            print(f"  Precision: {prec:.4f}")
            print(f"  Recall:    {rec:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
            print(f"  AUC-ROC:   {auc:.4f}")
            
            # Confusion Matrix
            cm = confusion_matrix(y_class_test, y_pred)
            print(f"\n  Confusion Matrix:")
            print(f"                Predicted")
            print(f"              Delayed  On-Time")
            print(f"  Actual Delayed   {cm[0][0]:4d}    {cm[0][1]:4d}")
            print(f"         On-Time   {cm[1][0]:4d}    {cm[1][1]:4d}")
    
    # ==================== REGRESSION EVALUATION ====================
    print("\n" + "="*60)
    print("📈 REGRESSION EVALUATION")
    print("="*60)
    
    if 'random_forest_regressor' in models:
        print("\n🔍 random_forest_regressor:")
        reg_model = models['random_forest_regressor']
        y_pred_reg = reg_model.predict(X_test)
        
        mae = mean_absolute_error(y_reg_test, y_pred_reg)
        rmse = np.sqrt(mean_squared_error(y_reg_test, y_pred_reg))
        r2 = r2_score(y_reg_test, y_pred_reg)
        
        results['random_forest_regressor'] = {
            'type': 'regression',
            'mae': mae,
            'rmse': rmse,
            'r2': r2
        }
        
        print(f"  MAE:  {mae:.4f} days")
        print(f"  RMSE: {rmse:.4f} days")
        print(f"  R²:   {r2:.4f}")
    
    # ==================== RISK CATEGORY EVALUATION ====================
    print("\n" + "="*60)
    print("🎯 RISK CATEGORY ACCURACY")
    print("="*60)
    
    # Use regression predictions to categorize risk
    if 'random_forest_regressor' in models:
        y_pred_reg = models['random_forest_regressor'].predict(X_test)
        
        actual_categories = [calculate_risk_category(d) for d in y_reg_test]
        pred_categories = [calculate_risk_category(d) for d in y_pred_reg]
        
        # Category accuracy
        cat_correct = sum(1 for a, p in zip(actual_categories, pred_categories) if a == p)
        cat_accuracy = cat_correct / len(actual_categories)
        
        print(f"\n  Overall Category Accuracy: {cat_accuracy:.2%}")
        
        # Per-category breakdown
        categories = ['Low', 'Medium', 'High', 'Critical']
        print(f"\n  {'Category':<12} {'Count':>8} {'Correct':>10} {'Accuracy':>10}")
        print("  " + "-"*44)
        
        for cat in categories:
            actual_mask = [a == cat for a in actual_categories]
            if sum(actual_mask) > 0:
                correct = sum(1 for a, p, m in zip(actual_categories, pred_categories, actual_mask) if m and a == p)
                count = sum(actual_mask)
                acc = correct / count
                print(f"  {cat:<12} {count:>8} {correct:>10} {acc:>10.2%}")
        
        results['risk_category'] = {
            'overall_accuracy': cat_accuracy
        }
    
    # ==================== MODEL SELECTION ====================
    print("\n" + "="*60)
    print("🏆 MODEL SELECTION")
    print("="*60)
    
    # Find best classifier by F1
    classifiers_results = {k: v for k, v in results.items() if v.get('type') == 'classification'}
    if classifiers_results:
        best_clf_name = max(classifiers_results, key=lambda k: classifiers_results[k]['f1'])
        best_clf = classifiers_results[best_clf_name]
        print(f"\n  Best Classifier: {best_clf_name}")
        print(f"  F1 Score: {best_clf['f1']:.4f}")
        print(f"  AUC-ROC: {best_clf['auc']:.4f}")
    
    # Save evaluation results
    output_dir = Path(__file__).parent.parent / "models"
    eval_path = output_dir / "evaluation_results.json"
    
    # Convert numpy types for JSON
    results_json = {}
    for k, v in results.items():
        results_json[k] = {kk: float(vv) if isinstance(vv, (np.float32, np.float64)) else vv for kk, vv in v.items()}
    
    with open(eval_path, 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n✅ Evaluation saved: {eval_path}")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*60)
    print("📋 EVALUATION SUMMARY")
    print("="*60)
    
    print("\n  Classification Models:")
    print(f"  {'Model':<28} {'Accuracy':>10} {'F1':>10} {'AUC':>10}")
    print("  " + "-"*60)
    for name, r in classifiers_results.items():
        print(f"  {name:<28} {r['accuracy']:>10.4f} {r['f1']:>10.4f} {r['auc']:>10.4f}")
    
    print("\n  Regression Model:")
    if 'random_forest_regressor' in results:
        r = results['random_forest_regressor']
        print(f"  MAE: {r['mae']:.4f} days, RMSE: {r['rmse']:.4f} days")
    
    print("\n  🎯 RECOMMENDED MODEL:")
    print(f"  Classifier: random_forest_classifier")
    print(f"  Regressor: random_forest_regressor")
    
    return results


if __name__ == "__main__":
    results = evaluate_models()
