"""Inference script to generate predictions.csv from test_unlabelled.csv."""
import argparse
import joblib
import pandas as pd
from scipy.sparse import hstack

from src.preprocessing import clean_text, VALID_TEAMS


def generate_predictions(
    test_path: str = 'test_unlabelled.csv',
    model_path: str = 'models/kestrel_router_pipeline.joblib',
    output_path: str = 'predictions.csv'
):
    print(f"Loading test data from {test_path} and model from {model_path}...")
    test_df = pd.read_csv(test_path)
    artifacts = joblib.load(model_path)

    model = artifacts['model']
    word_vec = artifacts['word_vec']
    char_vec = artifacts['char_vec']
    ohe = artifacts['ohe']

    cleaned_texts = test_df['request_text'].apply(clean_text)
    X_word = word_vec.transform(cleaned_texts)
    X_char = char_vec.transform(cleaned_texts)
    X_meta = ohe.transform(test_df[['channel', 'product_family', 'warranty_status']])
    X_test = hstack([X_word, X_char, X_meta])

    preds = model.predict(X_test)

    pred_df = pd.DataFrame({
        'request_id': test_df['request_id'],
        'team': preds
    })

    # Strict validations
    assert len(pred_df) == len(test_df), f"Row count mismatch: {len(pred_df)} != {len(test_df)}"
    assert (pred_df['request_id'] == test_df['request_id']).all(), "request_id order or content mismatch"
    assert pred_df['team'].isnull().sum() == 0, "Missing predictions detected"
    invalid_teams = set(pred_df['team']) - set(VALID_TEAMS)
    assert len(invalid_teams) == 0, f"Invalid team labels detected: {invalid_teams}"

    pred_df.to_csv(output_path, index=False)
    print(f"Generated {len(pred_df)} predictions saved to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_path', default='test_unlabelled.csv')
    parser.add_argument('--model_path', default='models/kestrel_router_pipeline.joblib')
    parser.add_argument('--output_path', default='predictions.csv')
    args = parser.parse_args()
    generate_predictions(args.test_path, args.model_path, args.output_path)
