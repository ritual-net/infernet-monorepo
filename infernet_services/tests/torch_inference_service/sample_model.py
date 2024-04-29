from typing import Any

import matplotlib.pyplot as plt
import pandas as pd  # type: ignore
import sk2torch  # type: ignore
import torch
from sklearn.datasets import fetch_california_housing  # type: ignore
from sklearn.linear_model import LinearRegression  # type: ignore
from sklearn.metrics import mean_squared_error  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore

california: Any = fetch_california_housing()


def train() -> None:
    X = california.data
    y = california.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    sk_model = LinearRegression()
    sk_model.fit(X_train, y_train)
    torch_model = sk2torch.wrap(sk_model)
    X_test_torch = torch.tensor(X_test, dtype=torch.double)

    torch.save(torch_model, "california_housing.torch")

    with torch.no_grad():
        y_pred = torch_model(X_test_torch)

    # Evaluate the Sklearn model
    sk_pred = sk_model.predict(X_test)
    print("Scikit-learn MSE:", mean_squared_error(y_test, sk_pred))

    # Evaluate the PyTorch model
    print("PyTorch MSE:", mean_squared_error(y_test, y_pred.numpy()))


def inference() -> None:
    df = pd.DataFrame(california.data, columns=california.feature_names)
    df["MedHouseVal"] = california.target
    test_data = df.iloc[0]
    test_data_df = pd.DataFrame([test_data], columns=california.feature_names)
    print("Test Data Point:")
    print(test_data_df)

    model = torch.load("california_housing.torch")
    model.eval()  # Set the model to evaluation mode

    input_data = torch.tensor(
        [[8.3252, 41.0, 6.984127, 1.02381, 322.0, 2.555556, 37.88, -122.23]],
        dtype=torch.double,
    )

    prediction = model(input_data)
    print(
        f"Predicted Value: {prediction[0]}",
        f"Actual Value: {test_data.MedHouseVal}",
    )


def plot_neighbourhood() -> None:
    df = pd.DataFrame(california.data, columns=california.feature_names)
    df["MedHouseVal"] = california.target
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(
        df["Longitude"], df["Latitude"], c=df["MedHouseVal"], cmap="viridis", alpha=0.5
    )
    plt.colorbar(scatter, label="Median House Value ($100K)")
    plt.title("California Housing Prices Distribution")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    inference()
