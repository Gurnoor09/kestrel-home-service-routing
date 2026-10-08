"""Comprehensive evaluation script running primary out-of-time holdout and backtests."""
import argparse
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.preprocessing import clean_text, map_canonical_team


def run_evaluation(train_path: str = 'train.csv'):
    df = pd.read_csv(train_path)
    df['target'] = df['team_label'].apply(map_canonical_team)
    df['created_dt'] = pd.to_datetime(df['created_at_ist'])
    df['cleaned_text'] = df['request_text'].apply(clean_text)

    val_split_date = pd.to_datetime('2026-04-01 00:00:00')
    train_split = df[df['created_dt'] < val_split_date].copy()
    val_split = df[df['created_dt'] >= val_split_date].copy()

    print(f"=== PRIMARY OUT-OF-TIME VALIDATION (Train <= 2026-03-31, Val: 2026-04-01 to 2026-06-30) ===")
    print(f"Train samples: {len(train_split)}, Val samples: {len(val_split)}")

    word_vec = TfidfVectorizer(ngram_range=(1, 3), analyzer='word', min_df=2, sublinear_tf=True)
    char_vec = TfidfVectorizer(ngram_range=(3, 5), analyzer='char_wb', min_df=2, sublinear_tf=True)
    ohe = OneHotEncoder(handle_unknown='ignore')

    X_train_word = word_vec.fit_transform(train_split['cleaned_text'])
    X_train_char = char_vec.fit_transform(train_split['cleaned_text'])
    X_train_meta = ohe.fit_transform(train_split[['channel', 'product_family', 'warranty_status']])
    X_train = hstack([X_train_word, X_train_char, X_train_meta])

    X_val_word = word_vec.transform(val_split['cleaned_text'])
    X_val_char = char_vec.transform(val_split['cleaned_text'])
    X_val_meta = ohe.transform(val_split[['channel', 'product_family', 'warranty_status']])
    X_val = hstack([X_val_word, X_val_char, X_val_meta])

    base_svc = LinearSVC(C=1.0, random_state=42, max_iter=2000)
    model = CalibratedClassifierCV(base_svc, cv=5)
    model.fit(X_train, train_split['target'])

    preds = model.predict(X_val)
    acc = accuracy_score(val_split['target'], preds)
    macro_f1 = f1_score(val_split['target'], preds, average='macro')
    labels = sorted(df['target'].unique())

    print(f"Accuracy: {acc*100:.2f}% | Macro F1: {macro_f1*100:.2f}% | Errors: {np.sum(val_split['target'] != preds)}/{len(val_split)}")
    print("\n--- Per-team Classification Report ---")
    print(classification_report(val_split['target'], preds, target_names=labels, digits=4))

    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(val_split['target'], preds, labels=labels)
    print(pd.DataFrame(cm, index=labels, columns=labels))

    # Deduplicated validation
    train_texts = set(train_split['cleaned_text'])
    is_dup = val_split['cleaned_text'].isin(train_texts)
    val_nodup = val_split[~is_dup]
    preds_nodup = preds[~is_dup.values]
    acc_nodup = accuracy_score(val_nodup['target'], preds_nodup)
    f1_nodup = f1_score(val_nodup['target'], preds_nodup, average='macro')
    print(f"\n--- Without Text-Leakage (Exact duplicates excluded, {len(val_nodup)} rows) ---")
    print(f"Accuracy: {acc_nodup*100:.2f}% | Macro F1: {f1_nodup*100:.2f}%")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_path', default='train.csv')
    args = parser.parse_args()
    run_evaluation(args.train_path)
