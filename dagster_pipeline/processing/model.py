from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

def train_salary_model(features_df, logger=None):
    if 'salary_mean' not in features_df.columns:
        if logger:
            logger.error("Столбец 'salary_mean' не найден в features_df.")
        return None

    y = features_df['salary_mean']
    X = features_df.drop('salary_mean', axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r_squared = r2_score(y_test, y_pred)

    if logger:
        logger.info("Оценка модели:")
        logger.info(f"MSE: {mse:.2f}, RMSE: {rmse:.2f}, R^2: {r_squared:.2f}")

    return model, {"mse": mse, "rmse": rmse, "r2": r_squared}
