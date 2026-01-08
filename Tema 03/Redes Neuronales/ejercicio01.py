import kagglehub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# Download latest version
path = kagglehub.dataset_download("fedesoriano/air-quality-data-set")

# Set the path to the file you'd like to load
file_path = f"{path}/AirQuality.csv"

# Load the CSV with the correct encoding
df = pd.read_csv(file_path, encoding='utf-8', delimiter=';', decimal=',')

print("First 5 records:\n", df.head())

print("\nEDA Summary:")
print(df.describe())

print("\nMissing values per column:\n", df.isnull().sum())

print("\nData types:\n", df.dtypes)

print("\nDeleting last two columns...")
df = df.iloc[:, :-2]

print("\nDataFrame shape after deletion:", df.shape)

print("\nColumn names:", df.columns.tolist())

print("\nDeleting rows with any missing values...")
df = df.dropna()

print("\nDataFrame shape after deleting rows with missing values:", df.shape)

print("\nDeleting duplicate rows...")
df = df.drop_duplicates()

print("\nDataFrame shape after deleting duplicate rows:", df.shape)
    
print("\nData types after conversion:\n", df.dtypes)

print("\nDeleting 'Date' and 'Time'...")
df = df.drop(columns=['Date', 'Time'])

print("\nDataFrame shape after datetime conversion:", df.shape)

print("\nDeleting outliers. Values less than 0...")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
for col in numeric_cols:
    df = df[df[col] >= 0]
    
print("\nPlotting hist plots for numeric columns...")
df.hist(bins=30, figsize=(15, 10), layout=(4, 4), color='blue', edgecolor='black', alpha=0.7, grid=False)
plt.tight_layout()
plt.show()

print("\nFinal cleaned DataFrame info:")
print(df.info())

print("\nFirst 5 records of cleaned DataFrame:\n", df.head())

print("\nData cleaning completed.")

print("\nMatrix of correlations:\n")
correlation_matrix = df.corr()
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True)
plt.title("Correlation Matrix")
plt.show()


print("\nVariable objetive: 'NO2(GT)'")
X = df[['CO(GT)', 'C6H6(GT)', 'NOx(GT)']]
y = df['NO2(GT)']

print("\nFeatures shape:", X.shape)
print("Target shape:", y.shape)


print("\nPreparing data for modeling...")

print("\nScaling features using Min-Max Scaling...")
scaler = MinMaxScaler()
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

print("\nScaled DataFrame head:\n", df.head())


print("\nSplitting data into training and testing sets (70% train, 30% test)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

print("\nTraining features shape:", X_train.shape)
print("Testing features shape:", X_test.shape)
print("Training target shape:", y_train.shape)
print("Testing target shape:", y_test.shape)