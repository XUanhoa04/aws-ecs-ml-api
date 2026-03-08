from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib

print("model XGBoost Iris")
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)

model = xgb.XGBClassifier(objective='multi:softprob', num_class=3, random_state=42)
model.fit(X_train, y_train)

# accuracy
acc = model.score(X_test, y_test)
print(f"accuracy: {acc*100:.1f}%")

joblib.dump(model, 'model.joblib')
print(" model.joblib saved")