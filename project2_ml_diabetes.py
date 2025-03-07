# -*- coding: utf-8 -*-
"""Project2 ML Diabetes

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FewXqSkfjpmsOU-l7W_lP8hMVeaPDfPm

# Import Part
"""

import joblib
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from plotly.offline import iplot , plot
import plotly.io as pio
from plotly.offline import init_notebook_mode
init_notebook_mode(connected=True)
from plotly.subplots import make_subplots
import itertools
import plotly.graph_objects as go

from sklearn.metrics import  ConfusionMatrixDisplay, classification_report
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, cross_validate
from sklearn.model_selection import train_test_split , cross_val_score
from sklearn.preprocessing import MinMaxScaler ,LabelEncoder
from sklearn.ensemble import RandomForestClassifier , BaggingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import KNNImputer
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import warnings
warnings.simplefilter(action="ignore")

"""# Import Data"""

from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv("/content/drive/MyDrive/project2/diabetes.csv")

df.sample(5)

df.shape[0],df.shape[1]

df.info()

df.isna().sum()

df.describe()

"""# Handling Missing Data (Nulls)"""

df[['Glucose','BloodPressure','SkinThickness','Insulin','BMI']] = df[['Glucose','BloodPressure','SkinThickness'
                                                                      ,'Insulin','BMI']].replace(0 , np.nan)

df.isnull().sum()

def median_target(column):
    temp = df.groupby('Outcome')[column].median()
    df.loc[(df['Outcome'] == 0) & (df[column].isna()) , column ] = temp[0]
    df.loc[(df['Outcome'] == 1) & (df[column].isna()) , column ] = temp[1]

columns_to_Fill = ['Glucose','BloodPressure','SkinThickness','Insulin','BMI']
for column in columns_to_Fill:
    median_target(column)

df.isnull().sum()

"""# Detection Outliers"""

def detect_outliers_iqr(df, columns, threshold = 1.5):

    outlier_indices = {}

    for col in columns:
        Q1 = df[col].quantile(0.25)  # 25th percentile
        Q3 = df[col].quantile(0.75)  # 75th percentile
        IQR = Q3 - Q1  # Interquartile range
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR

        # Finding outliers
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index.tolist()
        outlier_indices[col] = outliers

    return outlier_indices

numerical_columns = df.columns.to_list()[:-1]
outliers_iqr = detect_outliers_iqr(df, numerical_columns)

for col, indices in outliers_iqr.items():
    print(f"{col}: {len(indices)} outliers detected")

plt.figure(figsize=(15, 12))

for i, col in enumerate(numerical_columns, 1):
    plt.subplot(3, 3, i)
    sns.boxplot(x = df[col], color = "skyblue")
    plt.title(f"Box Plot of {col}")

plt.tight_layout()
plt.show()

def remove_outliers(df, columns, threshold=1.5):
    df_clean = df.copy()
    for col in columns:
        Q1 = df_clean[col].quantile(0.25)  # First quartile (25%)
        Q3 = df_clean[col].quantile(0.75)  # Third quartile (75%)
        IQR = Q3 - Q1  # Interquartile range
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR

        df_clean = df_clean[(df_clean[col] > lower_bound) & (df_clean[col] < upper_bound)]

    return df_clean

df_cleaned = remove_outliers(df, numerical_columns)

df_cleaned.shape[0],df_cleaned.shape[1]

#Show outlier after clean data
plt.figure(figsize=(15, 12))

for i, col in enumerate(numerical_columns, 1):
    plt.subplot(3, 3, i)
    sns.boxplot(x = df_cleaned[col], color = "skyblue")
    plt.title(f"Box Plot of {col}")

plt.tight_layout()
plt.show()

df_cleaned.info()

df_cleaned.reset_index(inplace = True , drop = True)
df_cleaned.sample(5)

"""# EDA"""

pio.renderers.default = 'colab'
# สร้าง Pie Chart
fig = px.pie(values=df_cleaned['Outcome'].value_counts(),
             names=['No Diabetes', 'Diabetes'],
             title='Percentage of diabetics in the data'
             ).update_traces(textinfo='label+percent')

fig.show()

import math
columns_histo = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

# กำหนดให้มี 3 แถว และคำนวณจำนวนคอลัมน์อัตโนมัติ
rows = 3
cols = math.ceil(len(columns_histo) / rows)  # คำนวณจำนวนคอลัมน์ให้พอดี

fig, axes = plt.subplots(rows, cols, figsize=(12, 3 * rows))  # ปรับขนาดกราฟให้เล็กลง
axes = axes.flatten()  # แปลงเป็น 1D array เพื่อให้เข้าถึง index ได้ง่าย

# วนลูปสร้าง Histogram แต่ละตัวแปร
for i, col in enumerate(columns_histo):
    sns.histplot(df_cleaned[col], kde=True, bins=30, ax=axes[i])
    axes[i].set_title(f"Histogram of {col}")
    axes[i].set_xlabel("")
    axes[i].set_ylabel("Frequency")
    axes[i].grid(True)

# ลบช่องว่างที่ไม่มีข้อมูล (กรณีจำนวนกราฟไม่พอดีกับ grid)
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()

columns_box = ['Pregnancies','Glucose', 'BloodPressure', 'SkinThickness', 'Insulin',
                 'BMI', 'DiabetesPedigreeFunction', 'Age']

# กำหนดให้มี 1 แถว หลายคอลัมน์
fig, axes = plt.subplots(1, len(columns_box), figsize=(15, 6), sharey=True)

# วนลูปสร้าง Box Plot แต่ละตัวแปร
for i, col in enumerate(columns_box):
    sns.boxplot(y=df_cleaned[col], ax=axes[i])  # ตั้งค่าแกน Y เพื่อให้แนวตั้ง
    axes[i].set_title(f"{col}")  # ตั้งชื่อกราฟ
    axes[i].set_xlabel("")  # ไม่ต้องแสดงชื่อแกน X เพื่อความสวยงาม

# จัด Layout ให้สวยงาม
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 8))  # กำหนดขนาดกราฟ
sns.heatmap(df_cleaned.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)

plt.title("Correlation between features")
plt.show()

"""Categorize Values and visualizing the categories"""

def categorize_values(df):
    df['Glucose_Category'] = pd.cut(df['Glucose'], bins=[0, 99, 125, float('inf')],
                                    labels=['Normal', 'Prediabetes', 'Diabetes'], right=False)

    df['BloodPressure_Category'] = pd.cut(df['BloodPressure'], bins=[44, 89, 99, 104, float('inf')],
                                          labels=['Normal', 'Elevated', 'Hypertension Stage 1', 'Hypertension Stage 2'], right=False)

    df['SkinThickness_Category'] = pd.cut(df['SkinThickness'], bins=[0, 30, float('inf')],
                                          labels=['Normal', 'Elevated'], right=False)

    df['Insulin_Category'] = pd.cut(df['Insulin'], bins=[0, 24.9, float('inf')],
                                    labels=['Normal', 'High'], right=False)

    df['BMI_Category'] = pd.cut(df['BMI'], bins=[0, 18.5, 24.9, 29.9, 34.9, 39.9, float('inf')],
                                labels=['Underweight', 'Normal weight', 'Overweight', 'Obese (Class 1)', 'Obese (Class 2)', 'Obese (Class 3)'], right=False)

    df['DiabetesPedigreeFunction_Category'] = pd.cut(df['DiabetesPedigreeFunction'], bins=[0, 0.5, 1.0, 1.5, 2.5],
                                                    labels=['Low risk', 'Moderate risk', 'High risk', 'Very high risk'], right=False)

    return df
df_cleaned = categorize_values(df_cleaned)

df_cleaned.head()

pio.renderers.default = 'colab'

columns_Category = ['BMI_Category','DiabetesPedigreeFunction_Category','Glucose_Category','BloodPressure_Category','SkinThickness_Category','Insulin_Category']

for col in columns_Category:
    fig = px.pie(title=f'{col}',
                 values=df_cleaned[col].value_counts().values,
                 names=df_cleaned[col].value_counts().index
                ).update_traces(textinfo='label+percent')

    fig.show()

"""# Data Pre-processing"""

df_cleaned.drop(df_cleaned.columns.to_list()[9:] , axis = 1,inplace = True)

X = df_cleaned.drop('Outcome',axis=1)
y = df_cleaned['Outcome']

X_train , X_test , y_train , y_test = train_test_split(X , y , test_size = 0.25 , random_state = 44 , shuffle = True)

print(f'Shape of X_Train {X_train.shape}')
print(f'Shape of X_Test {X_test.shape}')
print(f'Shape of Y_Train {y_train.shape}')
print(f'Shape of Y_Test {y_test.shape}')

"""# Modeling"""

def kfolds(model, model_name):
    model = cross_val_score(model, X,y, cv=5)
    model_score = np.average(model)
    print(f"{model_name} score on cross validation: {model_score * 100}%")

def train(model, model_name):
    model.fit(X_train, y_train)
    model_train_score = model.score(X_train, y_train)
    model_test_score = model.score(X_test, y_test)
    print(f"{model_name} model score on Training data: {model_train_score * 100}%\n{model_name} model score on Testing data: {model_test_score * 100}%")


def class_report(model):
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

"""**Logistic Regression**"""

lr = LogisticRegression()
kfolds(lr, "Logistic Regression")
train(lr, "Logistic Regression")

ConfusionMatrixDisplay.from_estimator(lr,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(lr)

"""**Random Forest**"""

rf = RandomForestClassifier()
kfolds(rf, "Random Forest")
train(rf, "Random Forest")

ConfusionMatrixDisplay.from_estimator(rf,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(rf)

"""**KNN**"""

knn = KNeighborsClassifier()
kfolds(knn, "KNN")
train(knn, "KNN")

ConfusionMatrixDisplay.from_estimator(knn,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(knn)

"""**AdaBoost**"""

ada = AdaBoostClassifier()
kfolds(ada, "AdaBoost")
train(ada, "AdaBoost")

ConfusionMatrixDisplay.from_estimator(ada,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(ada)

"""**GradientBoosting**"""

gb = GradientBoostingClassifier(n_estimators=150, random_state=20)
kfolds(gb, "Boosting")
train(gb, "Boosting")

ConfusionMatrixDisplay.from_estimator(gb,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(gb)

"""**DecisionTree**"""

dt = DecisionTreeClassifier()
kfolds(dt, "Decision Tree")
train(dt, "Decision Tree")

ConfusionMatrixDisplay.from_estimator(dt,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(dt)

"""**SVM**"""

svm_model = SVC(C=50 , kernel='rbf')
kfolds(svm_model, "SVM")
train(svm_model, "SVM")

ConfusionMatrixDisplay.from_estimator(svm_model,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(svm_model)

"""**Xgboost**"""

xgboost = XGBClassifier()
kfolds(xgboost, "Xgboost")
train(xgboost, "Xgboost")

ConfusionMatrixDisplay.from_estimator(xgboost,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(xgboost)

"""**Bagging**"""

bagg_model = BaggingClassifier()
kfolds(bagg_model, "Bagging")
train(bagg_model, "Bagging")

ConfusionMatrixDisplay.from_estimator(bagg_model,
                                       X_test,
                                       y_test,
                                       xticks_rotation=45
    );

class_report(bagg_model)

"""# Test Model"""

# ทดสอบการทำนาย
sample_input = [[5, 120, 70, 25, 100, 24.5, 0.5, 30]]  # ข้อมูลตัวอย่าง
prediction = rf.predict(sample_input)

print("ผลการทำนาย:", "มีความเสี่ยงเป็นเบาหวาน" if prediction[0] == 1 else "ไม่มีความเสี่ยง")

"""# Save Model"""

import joblib
joblib.dump(rf, "diabetes_random_forest.pkl")
print("✅ โมเดลถูกบันทึกเป็นไฟล์ diabetes_random_forest.pkl แล้ว")