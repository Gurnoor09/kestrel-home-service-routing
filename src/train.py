"""Training pipeline for Kestrel service routing model."""
import argparse
import os
import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.preprocessing import clean_text, map_canonical_team


def train_model(train_path: str = 'train.csv', output_path: str = 'models/kestrel_router_pipeline.joblib'):
    print(f"Loading training data from {train_path}...")
    df = pd.read_csv(train_path)
    df['target'] = df['team_label'].apply(map_canonical_team)
    df['cleaned_text'] = df['request_text'].apply(clean_text)

    print(f"Dataset contains {len(df)} labelled requests across 7 canonical classes.")

    print("Extracting word n-grams (1, 3), char n-grams (3, 5), and metadata features...")
    word_vec = TfidfVectorizer(ngram_range=(1, 3), analyzer='word', min_df=2, sublinear_tf=True)
    char_vec = TfidfVectorizer(ngram_range=(3, 5), analyzer='char_wb', min_df=2, sublinear_tf=True)
    ohe = OneHotEncoder(handle_unknown='ignore')

    X_word = word_vec.fit_transform(df['cleaned_text'])
    X_char = char_vec.fit_transform(df['cleaned_text'])
    X_meta = ohe.fit_transform(df[['channel', 'product_family', 'warranty_status']])

    X_full = hstack([X_word, X_char, X_meta])

    print("Fitting 5-fold Calibrated LinearSVC classifier...")
    base_svc = LinearSVC(C=1.0, random_state=42, max_iter=2000)
    model = CalibratedClassifierCV(base_svc, cv=5)
    model.fit(X_full, df['target'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    artifacts = {
        'model': model,
        'word_vec': word_vec,
        'char_vec': char_vec,
        'ohe': ohe,
        'classes': list(model.classes_)
    }
    joblib.dump(artifacts, output_path)
    print(f"Model saved successfully to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_path', default='train.csv')
    parser.add_argument('--output_path', default='models/kestrel_router_pipeline.joblib')
    args = parser.parse_args()
    train_model(args.train_path, args.output_path)
