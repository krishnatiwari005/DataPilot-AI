# ------------------------------------------------------------
# dummy_linear_regression.py
# ------------------------------------------------------------
"""
Generate a synthetic regression dataset, train a LinearRegression
model, and report its performance on a held‑out test set (20%).
"""

import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

def main(random_state: int = 42,
         n_samples: int = 1000,
         n_features: int = 10,
         noise: float = 15.0,
         test_size: float = 0.2) -> dict:
    """
    Generate data, train LinearRegression, and return evaluation metrics.

    Parameters
    ----------
    random_state : int
        Seed for reproducibility.
    n_samples : int
        Number of total samples to generate.
    n_features : int
        Number of input features.
    noise : float
        Standard deviation of the gaussian noise added to the target.
    test_size : float
        Fraction of data to keep for testing (0 < test_size < 1).
    """
    # 1️⃣ Create synthetic regression data
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        noise=noise,
        random_state=random_state,
    )

    # 2️⃣ Split into train / test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # 3️⃣ Train Linear Regression
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 4️⃣ Predict on the test set
    y_pred = model.predict(X_test)

    # 5️⃣ Evaluate
    r2 = r2_score(y_test, y_pred)               # coefficient of determination
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    metrics = {
        "train_samples": X_train.shape[0],
        "test_samples": X_test.shape[0],
        "r2": r2,
        "rmse": rmse,
    }

    print("=== Linear Regression on Dummy Data ===")
    print(f"Train size: {metrics['train_samples']} samples")
    print(f"Test size : {metrics['test_samples']} samples")
    print(f"R² (coefficient of determination): {metrics['r2']:.4f}")
    print(f"RMSE (root mean squared error)   : {metrics['rmse']:.4f}")
    return metrics

if __name__ == "__main__":
    # Run the main function and expose the result as a global variable
    metrics = main()
