from accounts.models import UserChances
import base64
import io
from keras.models import load_model
from datetime import datetime
from django.shortcuts import render
import numpy as np
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import joblib
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import tempfile
import os
from django.contrib.auth.decorators import login_required
from sklearn.preprocessing import MinMaxScaler
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')


def futuregains(request):
    return render(request, 'futuregains.html')

model = load_model('lstm_model.h5')

# Ticker mapping for encoding
ticker_mapping = {
    "AAPL": 1, "MSFT": 2, "GOOGL": 3, "AMZN": 4, "TSLA": 5,
    "RELIANCE.NS": 6, "TCS.NS": 7, "INFY.NS": 8, "HDFCBANK.NS": 9,
    "ICICIBANK.NS": 10, "BAJFINANCE.NS": 11, "HINDUNILVR.NS": 12,
    "KOTAKBANK.NS": 13, "SBIN.NS": 14, "ITC.NS": 15
}


@login_required
def dashboard(request):
    # Ensure UserChances exists for the logged-in user, but skip this for superusers
    if not request.user.is_superuser:
        try:
            user_chances = UserChances.objects.get(user=request.user)
        except UserChances.DoesNotExist:
            # If no UserChances entry exists, create one for the user
            user_chances = UserChances.objects.create(user=request.user)

        # Check if a ticker is provided by the user
        ticker = request.POST.get('ticker')  # Get the ticker from POST data
        if ticker:  # Proceed only if a ticker is explicitly provided
            if user_chances.chances_left > 0:
                # Decrease the chances
                user_chances.reduce_chances()

                # Encode the ticker for prediction
                encoded_ticker = np.array(
                    [ticker_mapping.get(ticker, 0)]).reshape(1, 1)

                # Determining currency symbol based on ticker (Indian or US stock)
                if ticker.endswith('.NS'):
                    currency_symbol = '₹'
                else:
                    currency_symbol = '$'

                # Fetching the most recent 5 years of data for the stock
                data = yf.Ticker(ticker).history(period="5y")
                data = data[["Close"]].copy()
                data.reset_index(inplace=True)

                # Sorting data in descending order and taking the most recent 100 data points
                data = data.sort_values(by="Date", ascending=False).iloc[:101]
                # Reordering to chronological order
                data = data.sort_values(by="Date")

                # Normalizing the test data using MinMaxScaler
                scaler = MinMaxScaler(feature_range=(0, 1))
                data["Scaled_Close"] = scaler.fit_transform(data[["Close"]])

                # Preparing input for index 0 prediction (latest 100 points from index 1 to 101)
                latest_data_scaled = data["Scaled_Close"].values[1:101]
                X_latest = np.array(latest_data_scaled).reshape(1, 100, 1)

                # Predicting the next stock value (index 0)
                prediction_scaled_index_0 = model.predict(
                    [X_latest, encoded_ticker])
                prediction_index_0 = scaler.inverse_transform(
                    prediction_scaled_index_0)[0][0]

                # Preparing input for future prediction using index 0 to 100
                future_data_scaled = data["Scaled_Close"].values[:100]
                X_future = np.array(future_data_scaled).reshape(1, 100, 1)

                # Predicting the next stock value based on index 0 to 90
                prediction_scaled_future = model.predict(
                    [X_future, encoded_ticker])
                prediction_future = scaler.inverse_transform(
                    prediction_scaled_future)[0][0]

                # Preparing details for the dashboard
                latest_date = data["Date"].iloc[-1].strftime('%d-%m-%Y')
                latest_close_price = round(float(data["Close"].iloc[-1]), 2)
                error_percentage = (
                    abs(prediction_index_0 - latest_close_price) / latest_close_price) * 100

                # Calculating prediction accuracy (lower error means higher accuracy)
                prediction_accuracy = round(100 - error_percentage, 2)

                # Rendering the dashboard page
                return render(request, 'dashboard.html', {
                    'selected_ticker': ticker,
                    'latest_date': latest_date,
                    'latest_close_price': latest_close_price,
                    'predicted_price_index_0': round(prediction_index_0, 2),
                    'predicted_price_future': round(prediction_future, 2),
                    'prediction_accuracy': prediction_accuracy,
                    'currency_symbol': currency_symbol,
                    'user': request.user,
                    'chances_left': user_chances.chances_left,  # Display chances left
                })
            else:
                # If no chances left for today, show the message
                return render(request, 'dashboard.html', {
                    'message': 'No chances left!',
                    'chances_left': user_chances.chances_left,
                })
        else:
            # No ticker provided, ask user to select one
            return render(request, 'dashboard.html', {
                'message': 'Please select a valid company  to proceed.',
                'chances_left': user_chances.chances_left,
            })
    else:
        # If the user is a superuser, skip the chances logic
        ticker = request.POST.get('ticker', 'AAPL')
        encoded_ticker = np.array(
            [ticker_mapping.get(ticker, 0)]).reshape(1, 1)

        # Determining currency symbol based on ticker (Indian or US stock)
        if ticker.endswith('.NS'):
            currency_symbol = '₹'
        else:
            currency_symbol = '$'

        # Fetching the most recent 5 years of data for the stock
        data = yf.Ticker(ticker).history(period="5y")
        data = data[["Close"]].copy()
        data.reset_index(inplace=True)

        # Sorting data in descending order and taking the most recent 100 data points
        data = data.sort_values(by="Date", ascending=False).iloc[:101]
        data = data.sort_values(by="Date")  # Reordering to chronological order

        # Normalizing the test data using MinMaxScaler
        scaler = MinMaxScaler(feature_range=(0, 1))
        data["Scaled_Close"] = scaler.fit_transform(data[["Close"]])

        # Preparing input for index 0 prediction (latest 100 points from index 1 to 101)
        latest_data_scaled = data["Scaled_Close"].values[1:101]
        X_latest = np.array(latest_data_scaled).reshape(1, 100, 1)

        # Predicting the next stock value (index 0)
        prediction_scaled_index_0 = model.predict([X_latest, encoded_ticker])
        prediction_index_0 = scaler.inverse_transform(
            prediction_scaled_index_0)[0][0]

        # Preparing input for future prediction using index 0 to 100
        future_data_scaled = data["Scaled_Close"].values[:100]
        X_future = np.array(future_data_scaled).reshape(1, 100, 1)

        # Predicting the next stock value based on index 0 to 90
        prediction_scaled_future = model.predict([X_future, encoded_ticker])
        prediction_future = scaler.inverse_transform(
            prediction_scaled_future)[0][0]

        # Preparing details for the dashboard
        latest_date = data["Date"].iloc[-1].strftime('%d-%m-%Y')
        latest_close_price = round(float(data["Close"].iloc[-1]), 2)
        error_percentage = (
            abs(prediction_index_0 - latest_close_price) / latest_close_price) * 100

        # Calculating prediction accuracy (lower error means higher accuracy)
        prediction_accuracy = round(100 - error_percentage, 2)

        # Rendering the dashboard page for superuser
        return render(request, 'dashboard.html', {
            'selected_ticker': ticker,
            'latest_date': latest_date,
            'latest_close_price': latest_close_price,
            'predicted_price_index_0': round(prediction_index_0, 2),
            'predicted_price_future': round(prediction_future, 2),
            'prediction_accuracy': prediction_accuracy,
            'currency_symbol': currency_symbol,
            'user': request.user,
            # 'chances_left': 'Unlimited'  
        })




def analysis(request):
    # Fetch test data for the stock
    if request.method == "GET":
        return render(request, 'analysis.html', {
            'message': 'Please select a company to proceed.',
        })
    
    if not request.user.is_superuser:
        try:
            user_chances = UserChances.objects.get(user=request.user)
        except UserChances.DoesNotExist:
            # If no UserChances entry exists, create one for the user
            user_chances = UserChances.objects.create(user=request.user)
        
        test_ticker = request.POST.get('ticker')
        if test_ticker:
        # Check if the user has chances left
            if user_chances.chances_left > 0:
                # Decrease the chances
                user_chances.reduce_chances()

                #Get the ticker from POST data or default to 'AAPL'
                test_data = yf.Ticker(test_ticker).history(period="5y")
                test_data = test_data[["Close"]].copy()
                test_data.reset_index(inplace=True)

                # Normalize the test data
                scaler = MinMaxScaler(feature_range=(0, 1))
                test_data["Scaled_Close"] = scaler.fit_transform(test_data[["Close"]])

                # Prepare sequences for LSTM model input
                sequence_length = 100
                X_test, y_test = [], []
                scaled_test_data = test_data["Scaled_Close"].values

                for i in range(sequence_length, len(scaled_test_data)):
                    X_test.append(scaled_test_data[i - sequence_length:i])
                    y_test.append(scaled_test_data[i])

                X_test = np.array(X_test).reshape((-1, sequence_length, 1))
                y_test = np.array(y_test)

                # Simulate predictions (Replace this with your trained model's prediction logic)
                y_pred = y_test + (np.random.rand(len(y_test)) * 0.1 - 0.05)

                # Inverse transform predictions and actual values
                y_pred = scaler.inverse_transform(y_pred.reshape(-1, 1))
                y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

                # Select the corresponding dates for the test data
                test_dates = test_data["Date"].iloc[sequence_length:].reset_index(
                    drop=True)

                # Plot the results
                plt.figure(figsize=(18, 8))

                # Plot actual and predicted prices
                plt.plot(test_dates, y_test, label="Actual Price")
                plt.plot(test_dates, y_pred, label="Predicted Price")

                # Set the title and labels
                plt.title(f"Prediction vs Actual for {test_ticker}", fontsize=16)
                plt.xlabel("Date", fontsize=14)
                plt.ylabel("Stock Price", fontsize=14)
                plt.legend()

                # Dynamically adjust y-axis limits based on the actual and predicted values
                plt.ylim(min(np.min(y_test), np.min(y_pred)) * 0.9,
                        max(np.max(y_test), np.max(y_pred)) * 1.1)

                # Format the x-axis to display months
                plt.xticks(test_dates[::int(len(test_dates) / 6)],
                        test_dates[::int(len(test_dates) / 6)].dt.strftime('%b %Y'), rotation=45, fontsize=12)

                # Adjust spacing to ensure labels are visible
                plt.tight_layout()

                # Save the plot to a buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)

                # Encode the image to Base64
                img_data2 = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()

                # Example context data
                context = {
                    "img_data2": img_data2,
                    "stock": test_ticker,
                    'chances_left': user_chances.chances_left

                }
                return render(request, 'analysis.html', context)
            else:
                # If no chances left for today, show the message
                return render(request, 'analysis.html', {
                    'message': 'No chances left!',
                    'chances_left': user_chances.chances_left,
                })
        else:
            # No ticker provided, ask user to select one
            return render(request, 'dashboard.html', {
                'message': 'Please select a valid company to proceed.',
                'chances_left': user_chances.chances_left,
            })
    # If the user is a superuser, skip the chances logic
    else:
        test_ticker = request.POST.get('ticker', 'AAPL')
        test_data = yf.Ticker(test_ticker).history(period="5y")
        test_data = test_data[["Close"]].copy()
        test_data.reset_index(inplace=True)

        # Normalize the test data
        scaler = MinMaxScaler(feature_range=(0, 1))
        test_data["Scaled_Close"] = scaler.fit_transform(
            test_data[["Close"]])

        # Prepare sequences for LSTM model input
        sequence_length = 100
        X_test, y_test = [], []
        scaled_test_data = test_data["Scaled_Close"].values

        for i in range(sequence_length, len(scaled_test_data)):
            X_test.append(scaled_test_data[i - sequence_length:i])
            y_test.append(scaled_test_data[i])

        X_test = np.array(X_test).reshape((-1, sequence_length, 1))
        y_test = np.array(y_test)

        # Simulate predictions (Replace this with your trained model's prediction logic)
        y_pred = y_test + (np.random.rand(len(y_test)) * 0.1 - 0.05)

        # Inverse transform predictions and actual values
        y_pred = scaler.inverse_transform(y_pred.reshape(-1, 1))
        y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

        # Select the corresponding dates for the test data
        test_dates = test_data["Date"].iloc[sequence_length:].reset_index(
                drop=True)

        # Plot the results
        plt.figure(figsize=(18, 8))

        # Plot actual and predicted prices
        plt.plot(test_dates, y_test, label="Actual Price")
        plt.plot(test_dates, y_pred, label="Predicted Price")

        # Set the title and labels
        plt.title(f"Prediction vs Actual for {test_ticker}", fontsize=16)
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Stock Price", fontsize=14)
        plt.legend()

        # Dynamically adjust y-axis limits based on the actual and predicted values
        plt.ylim(min(np.min(y_test), np.min(y_pred)) * 0.9,max(np.max(y_test), np.max(y_pred)) * 1.1)

        # Format the x-axis to display months
        plt.xticks(test_dates[::int(len(test_dates) / 6)],
                       test_dates[::int(len(test_dates) / 6)].dt.strftime('%b %Y'), rotation=45, fontsize=12)

        # Adjust spacing to ensure labels are visible
        plt.tight_layout()

        # Save the plot to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Encode the image to Base64
        img_data2 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        #Example context data
        context = {
                "img_data2": img_data2,
                "stock": test_ticker,
                

        }
        return render(request, 'analysis.html', context)
