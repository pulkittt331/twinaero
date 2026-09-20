import numpy as np

class XAIEngine:
    """
    Explainable AI (XAI) & Bayesian Uncertainty Estimation Engine for TwinAero-X.
    Computes SHAP-like feature attributions for anomaly & fault diagnoses,
    and 95% confidence intervals for Remaining Useful Life (RUL) predictions.
    """

    @staticmethod
    def compute_feature_attribution(z_scores, model=None, feature_names=None):
        """
        Computes feature attribution breakdown (0-100%) for diagnostic explainability.
        Combines Z-score squared residual deviation with model feature importances if available.
        """
        if not z_scores:
            return {}
            
        keys = list(z_scores.keys())
        abs_z = np.array([abs(z_scores[k]) for k in keys])
        
        # Base weights from normalized Z-score magnitudes (residual contribution)
        z_squared = abs_z ** 2
        sum_z_sq = np.sum(z_squared)
        
        if sum_z_sq <= 1e-6:
            # Equal distribution if all Z-scores are zero
            norm_weights = np.ones(len(keys)) / len(keys)
        else:
            norm_weights = z_squared / sum_z_sq

        # If a trained Random Forest model is provided, weight by feature importances
        if model is not None and hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            if len(importances) == len(keys):
                combined = norm_weights * 0.7 + (importances / (np.sum(importances) + 1e-6)) * 0.3
                norm_weights = combined / np.sum(combined)

        attribution = {}
        for idx, k in enumerate(keys):
            attribution[k] = round(float(norm_weights[idx] * 100.0), 1)

        # Sort descending by contribution percentage
        sorted_attr = dict(sorted(attribution.items(), key=lambda item: item[1], reverse=True))
        return sorted_attr

    @staticmethod
    def compute_rul_confidence_interval(rf_rul_model, feature_vector):
        """
        Computes Bayesian 95% Confidence Interval for RUL using Random Forest tree ensemble variance.
        Returns mean RUL, standard deviation, lower 95% bound, and upper 95% bound.
        """
        if rf_rul_model is None or not hasattr(rf_rul_model, "estimators_"):
            return None
            
        tree_preds = []
        for tree in rf_rul_model.estimators_:
            pred = tree.predict([feature_vector])[0]
            tree_preds.append(max(0.0, pred))
            
        tree_preds = np.array(tree_preds)
        mean_rul = float(np.mean(tree_preds))
        std_rul = float(np.std(tree_preds))
        
        # 95% Confidence Interval (z = 1.96)
        lower_95 = max(0.0, float(mean_rul - 1.96 * std_rul))
        upper_95 = float(mean_rul + 1.96 * std_rul)
        
        return {
            "mean": round(mean_rul, 1),
            "std_dev": round(std_rul, 1),
            "lower_95": round(lower_95, 1),
            "upper_95": round(upper_95, 1)
        }
