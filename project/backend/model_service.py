from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

FEATURE_COLS = [
    "age",
    "monthly_income",
    "employment_years",
    "loan_amount",
    "loan_term_months",
    "interest_rate",
    "past_due_30d",
    "inquiries_6m",
]


def roc_auc(y_true: np.ndarray, s: np.ndarray) -> float:
    y_true = y_true.astype(bool)
    pos, neg = s[y_true], s[~y_true]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    return float(
        (np.sum(pos[:, None] > neg) + 0.5 * np.sum(pos[:, None] == neg))
        / (len(pos) * len(neg))
    )


def pr_auc(y_true: np.ndarray, s: np.ndarray) -> float:
    o = np.argsort(-s)
    yt = y_true[o].astype(int)
    tp = np.cumsum(yt)
    fp = np.cumsum(1 - yt)
    prec = tp / np.maximum(tp + fp, 1)
    positives = int(yt.sum())
    if positives == 0:
        return 0.0
    return float((prec * yt).sum() / positives)


class OptimizedLogReg:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.mu = None
        self.sd = None
        self.w = None
        self.threshold = 0.5
        self.metrics = {}
        self.model_version = "v2_full_optimized"
        self._fit_optimized()

    def _train_once(
        self, X_tr: np.ndarray, y_tr: np.ndarray, lr: float, epochs: int, l2: float
    ) -> np.ndarray:
        Xm = np.column_stack([np.ones(len(X_tr)), X_tr])
        w = np.zeros(Xm.shape[1], dtype=np.float64)

        for _ in range(epochs):
            z = np.clip(Xm @ w, -30, 30)
            p = 1.0 / (1.0 + np.exp(-z))
            grad = (Xm.T @ (p - y_tr)) / len(y_tr)
            grad[1:] += l2 * w[1:]
            w -= lr * grad
        return w

    def _predict_prob_with_params(
        self, X: np.ndarray, mu: np.ndarray, sd: np.ndarray, w: np.ndarray
    ) -> np.ndarray:
        Xs = (X - mu) / sd
        Xm = np.column_stack([np.ones(len(Xs)), Xs])
        z = np.clip(Xm @ w, -30, 30)
        return 1.0 / (1.0 + np.exp(-z))

    def _kfold_indices(self, n: int, k: int = 5, seed: int = 42):
        rng = np.random.default_rng(seed)
        ix = rng.permutation(n)
        folds = np.array_split(ix, k)
        for i in range(k):
            va = folds[i]
            tr = np.concatenate([folds[j] for j in range(k) if j != i])
            yield tr, va

    def _find_best_threshold(self, y_true: np.ndarray, probs: np.ndarray) -> Tuple[float, dict]:
        best_t = 0.5
        best_score = -1.0
        best_stats = {}

        for t in np.arange(0.1, 0.91, 0.05):
            pred = (probs >= t).astype(int)
            acc = float((pred == y_true).mean())

            approvals = float((pred == 0).mean())
            if (pred == 1).sum() > 0:
                default_precision = float(((y_true == 1) & (pred == 1)).sum() / max((pred == 1).sum(), 1))
            else:
                default_precision = 0.0

            score = 0.7 * acc + 0.3 * default_precision
            if score > best_score:
                best_score = score
                best_t = float(round(t, 2))
                best_stats = {
                    "accuracy": round(acc, 4),
                    "approval_rate": round(approvals, 4),
                    "default_precision": round(default_precision, 4),
                }
        return best_t, best_stats

    def _fit_optimized(self):
        df = pd.read_csv(self.data_path)

        X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        y = df["target"].to_numpy(dtype=np.float64)

        params_grid = [
            {"lr": 0.05, "epochs": 2500, "l2": 0.0},
            {"lr": 0.1, "epochs": 3000, "l2": 0.0},
            {"lr": 0.15, "epochs": 3500, "l2": 0.0},
            {"lr": 0.08, "epochs": 3000, "l2": 0.001},
            {"lr": 0.1, "epochs": 3500, "l2": 0.005},
        ]

        best_cv = None
        best_auc = -1.0

        for p in params_grid:
            fold_aucs = []
            fold_prs = []

            for tr_idx, va_idx in self._kfold_indices(len(y), k=5, seed=42):
                X_tr, X_va = X[tr_idx], X[va_idx]
                y_tr, y_va = y[tr_idx], y[va_idx]

                mu = X_tr.mean(0)
                sd = X_tr.std(0) + 1e-9
                X_tr_s = (X_tr - mu) / sd

                w = self._train_once(X_tr_s, y_tr, p["lr"], p["epochs"], p["l2"])
                p_va = self._predict_prob_with_params(X_va, mu, sd, w)

                fold_aucs.append(roc_auc(y_va, p_va))
                fold_prs.append(pr_auc(y_va, p_va))

            mean_auc = float(np.mean(fold_aucs))
            mean_pr = float(np.mean(fold_prs))

            if mean_auc > best_auc:
                best_auc = mean_auc
                best_cv = {
                    "params": p,
                    "cv_roc_auc": mean_auc,
                    "cv_pr_auc": mean_pr,
                }

        chosen = best_cv["params"]

        rng = np.random.default_rng(42)
        n = len(y)
        ix = rng.permutation(n)
        cut = int(0.8 * n)
        tr, te = ix[:cut], ix[cut:]

        X_tr, X_te = X[tr], X[te]
        y_tr, y_te = y[tr], y[te]

        self.mu = X_tr.mean(0)
        self.sd = X_tr.std(0) + 1e-9
        X_tr_s = (X_tr - self.mu) / self.sd

        self.w = self._train_once(X_tr_s, y_tr, chosen["lr"], chosen["epochs"], chosen["l2"])

        p_te = self._predict_prob_with_params(X_te, self.mu, self.sd, self.w)

        threshold, threshold_stats = self._find_best_threshold(y_te, p_te)
        self.threshold = threshold

        pred = (p_te >= self.threshold).astype(int)

        self.metrics = {
            "roc_auc": round(roc_auc(y_te, p_te), 4),
            "pr_auc": round(pr_auc(y_te, p_te), 4),
            "accuracy_at_threshold": round(float((pred == y_te).mean()), 4),
            "selected_threshold": self.threshold,
            "threshold_stats": threshold_stats,
            "cv_roc_auc": round(best_cv["cv_roc_auc"], 4),
            "cv_pr_auc": round(best_cv["cv_pr_auc"], 4),
            "best_params": chosen,
        }

    def predict(self, features: Dict[str, float]) -> Tuple[float, str]:
        row = np.array([[features[col] for col in FEATURE_COLS]], dtype=np.float64)
        p_default = float(self._predict_prob_with_params(row, self.mu, self.sd, self.w)[0])
        label = "default" if p_default >= self.threshold else "non-default"
        return p_default, label
