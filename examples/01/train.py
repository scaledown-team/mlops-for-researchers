import os
import warnings
import sys

import pandas as pd
import numpy as np
from itertools import cycle
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import lasso_path, enet_path
from sklearn import datasets

# Import Prefect
from prefect import flow, task

# Import mlflow
import mlflow
from mlflow.models.signature import infer_signature
import mlflow.sklearn

@task
def load_data():
    # Load Diabetes datasets
    diabetes = datasets.load_diabetes()
    X = diabetes.data
    y = diabetes.target

    # Create pandas DataFrame for sklearn ElasticNet linear_model
    Y = np.array([y]).transpose()
    d = np.concatenate((X, Y), axis=1)
    cols = diabetes.feature_names + ["progression"]
    data = pd.DataFrame(d, columns=cols)

    return data

@task
def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2

@task
def preprocess_data(data):
    train, test = train_test_split(data)

    # The predicted column is "progression" which is a quantitative measure of disease progression one year after baseline
    train_x = train.drop(["progression"], axis=1)
    test_x = test.drop(["progression"], axis=1)
    train_y = train[["progression"]]
    test_y = test[["progression"]]

    return train_x, test_x, train_y, test_y

@task
def train_model(train_x, train_y):
    alpha = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
    l1_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05

    # Run ElasticNet
    lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
    lr.fit(train_x, train_y)

    return lr

@task
def test_model(test_x, test_y):
    predicted_qualities = lr.predict(test_x)
    (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

    return rmse, mae, r2


@flow
def main()
    data=load_data()

    train_x, test_x, train_y, test_y = preprocess_data(data)
    

    # Print out ElasticNet model metrics
    print("Elasticnet model (alpha={:f}, l1_ratio={:f}):".format(alpha, l1_ratio))
    print("  RMSE: %s" % rmse)
    print("  MAE: %s" % mae)
    print("  R2: %s" % r2)

    # Infer model signature
    predictions = lr.predict(train_x)
    signature = infer_signature(train_x, predictions)

    # Log mlflow attributes for mlflow UI
    mlflow.log_param("alpha", alpha)
    mlflow.log_param("l1_ratio", l1_ratio)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)
    mlflow.log_metric("mae", mae)
    mlflow.sklearn.log_model(lr, "model", signature=signature)

    # Compute paths
    eps = 5e-3  # the smaller it is the longer is the path

    print("Computing regularization path using the elastic net.")
    alphas_enet, coefs_enet, _ = enet_path(X, y, eps=eps, l1_ratio=l1_ratio)

    # Display results
    fig = plt.figure(1)
    ax = plt.gca()

    colors = cycle(["b", "r", "g", "c", "k"])
    neg_log_alphas_enet = -np.log10(alphas_enet)
    for coef_e, c in zip(coefs_enet, colors):
        l2 = plt.plot(neg_log_alphas_enet, coef_e, linestyle="--", c=c)

    plt.xlabel("-Log(alpha)")
    plt.ylabel("coefficients")
    title = "ElasticNet Path by alpha for l1_ratio = " + str(l1_ratio)
    plt.title(title)
    plt.axis("tight")

    # Save figures
    fig.savefig("ElasticNet-paths.png")

    # Close plot
    plt.close(fig)

    # Log artifacts (output files)
    mlflow.log_artifact("ElasticNet-paths.png")


if __name__ == "__main__":
    main()
