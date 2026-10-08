"""Inference model wrapper and explanation engine for Kestrel Service Desk."""
import os
import joblib
import pandas as pd
from scipy.sparse import hstack
from src.preprocessing import clean_text


class KestrelRouter:
    def __init__(self, model_path: str = 'models/kestrel_router_pipeline.joblib'):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model artifact not found at '{model_path}'. "
                f"Please run 'python -m src.train' first."
            )
        self.artifacts = joblib.load(model_path)
        self.model = self.artifacts['model']
        self.word_vec = self.artifacts['word_vec']
        self.char_vec = self.artifacts['char_vec']
        self.ohe = self.artifacts['ohe']
        self.classes = list(self.artifacts['classes'])

    def predict_one(self, request_text: str, product_family: str, warranty_status: str, channel: str, request_id: str = None) -> dict:
        cleaned_text = clean_text(request_text)
        meta_df = pd.DataFrame([{
            'channel': channel,
            'product_family': product_family,
            'warranty_status': warranty_status
        }])

        X_word = self.word_vec.transform([cleaned_text])
        X_char = self.char_vec.transform([cleaned_text])
        X_meta = self.ohe.transform(meta_df)
        X_input = hstack([X_word, X_char, X_meta])

        probs = self.model.predict_proba(X_input)[0]
        prob_dict = {cls: round(float(p), 4) for cls, p in zip(self.classes, probs)}
        
        # Sort teams by probability
        sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
        top_team, top_conf = sorted_probs[0]
        second_team, second_conf = sorted_probs[1] if len(sorted_probs) > 1 else (None, 0.0)

        # Generate evidence-based reasons
        reasons = []
        
        # Text keywords signal
        text_lower = cleaned_text.lower()
        key_signals = []
        if top_team == 'Billing':
            if any(k in text_lower for k in ['invoice', 'bill', 'tax', 'gst', 'receipt']):
                key_signals.append("invoice/tax query detected")
            if any(k in text_lower for k in ['deduct', 'double charge', 'charged twice', 'refund', 'paid twice']):
                key_signals.append("payment dispute/refund request detected")
            if any(k in text_lower for k in ['emi', 'coupon', 'discount']):
                key_signals.append("financial payment terms detected")
        elif top_team == 'Repairs':
            if any(k in text_lower for k in ['leak', 'leaking', 'water from bottom', 'drip']):
                key_signals.append("water leakage / physical defect reported")
            if any(k in text_lower for k in ['not working', 'not turn', 'tripping', 'mcb', 'dead', 'broken']):
                key_signals.append("breakdown / electrical trip reported")
            if any(k in text_lower for k in ['smoke', 'smell', 'burnt', 'spark', 'noise', 'loud']):
                key_signals.append("hardware failure / burning / noise symptoms reported")
            if any(k in text_lower for k in ['e1', 'e2', 'e3', 'e4', 'e5', 'error code']):
                key_signals.append("device error code reported")
        elif top_team == 'Filters & Consumables':
            if any(k in text_lower for k in ['filter', 'candle', 'membrane', 'jar', 'blade', 'brush', 'amc kit', 'consumable']):
                key_signals.append("consumable / replacement spare parts request")
        elif top_team == 'Installs & Demo':
            if any(k in text_lower for k in ['install', 'installation', 'demo', 'wall mount', 'mounting', 'unboxing', 'setup']):
                key_signals.append("new-device installation or demo request")
        elif top_team == 'Returns & Replacement':
            if any(k in text_lower for k in ['damaged', 'transit', 'broken in box', 'wrong model', 'wrong product', 'missing parts', 'exchange', 'return pickup']):
                key_signals.append("delivery defect, missing item, or return window request")
        elif top_team == 'Warranty Claims':
            if any(k in text_lower for k in ['warranty card', 'warranty certificate', 'shield', 'registration', 'claim status', 'coverage']):
                key_signals.append("warranty registration, shield inquiry, or claim verification")
        elif top_team == 'Product Advice':
            if any(k in text_lower for k in ['recipe', 'how to use', 'setting', 'temperature', 'compatible', 'manual', 'advice']):
                key_signals.append("usage, settings, or product feature guidance query")

        if key_signals:
            reasons.append(f"Text evidence: {', '.join(key_signals)}.")
        else:
            reasons.append(f"Customer opening text matches historical {top_team} routing patterns.")

        # Metadata alignment
        reasons.append(f"Context: {product_family} request via {channel.upper()} under '{warranty_status}' status.")
        
        # Confidence margin
        margin = top_conf - second_conf
        if margin > 0.40:
            reasons.append(f"High statistical confidence ({top_conf*100:.1f}%), clear separation over {second_team} ({second_conf*100:.1f}%).")
        else:
            reasons.append(f"Moderate confidence ({top_conf*100:.1f}%), close runner-up: {second_team} ({second_conf*100:.1f}%).")

        model_signal = f"CalibratedLinearSVC | n-gram TF-IDF + Safe Metadata | P({top_team})={top_conf:.4f}"

        return {
            'request_id': request_id,
            'predicted_team': top_team,
            'confidence': round(top_conf, 4),
            'reasons': reasons,
            'model_signal': model_signal,
            'probabilities': prob_dict
        }
