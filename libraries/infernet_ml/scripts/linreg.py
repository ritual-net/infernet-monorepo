"""
This script trains a PyTorch Linear Regression model with synthetic data and exports it
to ONNX format. The exported model is used to test various libraries & workflows such as
EZKL proofs as well as the onnx workflow in the infernet-ml library.
"""

import logging
import os
from typing import Any, Tuple, cast

import numpy as np
import onnx
import onnxruntime as ort  # type: ignore
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import mean_squared_error, r2_score  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore

log = logging.getLogger(__name__)

models_dir = "models"


def generate_synthetic_data(n_samples: int, n_features: int) -> Tuple[Any, Any]:
    """
    Generate synthetic data for linear regression.
    Args:
        n_samples: number of samples
        n_features: number of features

    Returns:
        Tuple[Any, Any]: X, y
    """

    np.random.seed(42)
    X = np.random.rand(n_samples, n_features).astype(np.float32)
    true_coefficients = np.random.rand(n_features).astype(np.float32)
    y = X @ true_coefficients + np.random.normal(0, 0.1, n_samples).astype(np.float32)
    return X, y


class LinearRegressionModel(nn.Module):
    """PyTorch Linear Regression Model."""

    def __init__(self, input_dim: int):
        super(LinearRegressionModel, self).__init__()
        self.linear = nn.Linear(input_dim, 1)

    def forward(self, x: Any) -> Any:
        return self.linear(x)


def train_and_export_model(
    n_features: int, model_name: str, models_dir: str = "models"
) -> None:
    """Train a PyTorch Linear Regression model and export it to ONNX format."""
    # Generate synthetic data
    X, y = generate_synthetic_data(1000, n_features)  # 1000 samples

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Convert data to PyTorch tensors
    X_train_tensor = torch.from_numpy(X_train)
    y_train_tensor = torch.from_numpy(y_train).view(-1, 1)
    X_test_tensor = torch.from_numpy(X_test)
    torch.from_numpy(y_test).view(-1, 1)

    # Initialize the model, loss function, and optimizer
    model: Any = LinearRegressionModel(n_features)
    loss_fn = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)

    # Training loop
    n_epochs = 10
    for epoch in range(n_epochs):
        # Forward pass
        predictions = model(X_train_tensor)

        # Compute loss
        loss = loss_fn(predictions, y_train_tensor)

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Print loss every 100 epochs
        if (epoch + 1) % 100 == 0:
            print(f"Epoch [{epoch + 1}/{n_epochs}], Loss: {loss.item():.4f}")

    # Evaluate the model
    with torch.no_grad():
        y_pred_tensor = model(X_test_tensor)
        y_pred = y_pred_tensor.numpy().flatten()

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(
        f"PyTorch Linear Regression with {n_features} features - MSE: {mse:.4f}, "
        f"R-squared: {r2:.4f}"
    )

    # Export the model to ONNX format
    os.makedirs(models_dir, exist_ok=True)
    onnx_file_path = os.path.join(models_dir, f"{model_name}.onnx")
    dummy_input: Tuple[Any] = cast(
        Any, torch.from_numpy(X_test[:1])
    )  # Correct: Use a single sample with shape (1, n_features)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_file_path,
        input_names=["input"],
        output_names=["output"],
        verbose=True,
    )


def run_forward_pass(model_id: str, n_features: int) -> None:
    model_path = f"{models_dir}/{model_id}.onnx"

    model = onnx.load(model_path)

    onnx.checker.check_model(model)

    # Load the ONNX model
    session = ort.InferenceSession(model_path)

    # Generate random input data
    input_name = session.get_inputs()[0].name
    input_data = np.random.rand(1, n_features).astype(np.float32)

    # Run the model
    result = session.run(None, {input_name: input_data})

    # Get the output
    output = result[0]

    log.info(f"Input: {input_data}")
    log.info(f"Output: {output}")


def train() -> None:
    # Training, evaluating, and exporting models with different number of features
    train_and_export_model(10, "ezkl_linreg_10_features")
    train_and_export_model(50, "ezkl_linreg_50_features")
    train_and_export_model(100, "ezkl_linreg_100_features")
    train_and_export_model(1000, "ezkl_linreg_1000_features")


def forward_pass() -> None:
    # Example usage
    run_forward_pass("ezkl_linreg_10_features", 10)
    run_forward_pass("ezkl_linreg_50_features", 50)
    run_forward_pass("ezkl_linreg_100_features", 100)
    run_forward_pass("ezkl_linreg_1000_features", 100)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    for n in [10, 50, 100, 1000]:
        model_name = f"ezkl_linreg_{n}_features"
        train_and_export_model(n, model_name)
        run_forward_pass(model_name, n)
