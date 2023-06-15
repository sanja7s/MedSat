import os
import copy
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, TensorDataset
import csv
import torch.nn.functional as F
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from itertools import product
import pandas as pd
from util import *
from sklearn.preprocessing import StandardScaler


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# neural network implementation
class Net(nn.Module):
    def __init__(self, input_feature_dim, hidden_layers, embedding_dim):
        super(Net, self).__init__()
        self.hidden_layers = hidden_layers
        self.embedding_dim = embedding_dim

        self.layers = nn.ModuleList([nn.Linear(input_feature_dim, embedding_dim)])
        for i in range(hidden_layers):
            self.layers.append(nn.Linear(embedding_dim, embedding_dim))

        self.output_layer = nn.Linear(embedding_dim, 1)

    def forward(self, x):
        for i in range(len(self.layers)):
            x = F.relu(self.layers[i](x))

        return self.output_layer(x).squeeze(1)


def train(dataloader, num_epochs, num_input_features, num_hidden_layers, embedding_dim,
          validation_dataloader=None):  # remove num features

    # create a model and optimizer
    model = Net(num_input_features, num_hidden_layers, embedding_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001, weight_decay=0.001)
    criterion = nn.MSELoss()

    # initialize a list to store the loss values for each epoch
    loss_list = []
    best_loss = float('inf')
    epochs_since_last_improvement = 0
    best_model = None
    # train the model
    for i in range(num_epochs):
        epoch_loss = 0.0
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            optimizer.zero_grad()
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        epoch_loss /= len(dataloader)
        loss_list.append(epoch_loss)

        print(f"Epoch {i + 1}, loss={loss.item():.4f}")

        # check validation loss and save best model
        if validation_dataloader:
            with torch.no_grad():
                val_loss = 0.0
                for val_X_batch, val_y_batch in validation_dataloader:
                    val_X_batch = val_X_batch.to(device)
                    val_y_batch = val_y_batch.to(device)
                    val_y_pred = model(val_X_batch)
                    val_loss += criterion(val_y_pred, val_y_batch).item()
                # val_loss /= len(validation_dataloader)
                val_loss = torch.tensor(val_loss)
                val_loss /= len(validation_dataloader)
                if val_loss < best_loss:
                    best_loss = val_loss
                    best_model = copy.deepcopy(model)
                    epochs_since_last_improvement = 0
                else:
                    epochs_since_last_improvement += 1
                    if epochs_since_last_improvement == 10:
                        print(
                            f"No improvement in validation loss for {epochs_since_last_improvement} epochs, terminating training.")
                        break

    # plot the loss values over epochs
    # plt.plot(loss_list)
    # plt.xlabel('Epoch')
    # plt.ylabel('Loss')
    # plt.show()

    return best_model


def test(test_loader, model):
    # set up empty lists for true and predicted labels
    y_true = []
    y_pred = []
    # turn off gradient tracking for evaluation
    with torch.no_grad():
        # iterate through test data
        for data in test_loader:
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            # extend true and predicted label lists
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(outputs.cpu().numpy())

    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print("MSE: {:.5f}, R^2 Score: {:.5f}".format(mse, r2))

    return r2, mse

def get_data_loader(x, y):
    X_tensor = torch.tensor(x, dtype=torch.float32)
    Y_tensor = torch.tensor(y, dtype=torch.float32)

    dataset = TensorDataset(X_tensor, Y_tensor)

    return DataLoader(dataset, batch_size=64, shuffle=True)


def fnn_train_evaluation(fold_splits, modalities=all_modalities, num_epochs=100, num_hidden_layers=3, embedding_dim=512):

    results = {}
    for condition in all_conditions:
        test_r2_scores = []
        test_mse_scores = []
        med_condition = "o_{}_quantity_per_capita".format(condition)
        results[condition] = {}
        for fold in fold_splits:
            # Split data into training and validation sets for this fold
            train_fold = fold[0]
            val_fold = fold[1]
            test_fold = fold[2]

            scaler = StandardScaler()
            x_train, y_train = extract_features_and_labels(train_fold, med_condition, modalities)
            x_train = scaler.fit_transform(x_train)
            num_input_features = x_train.shape[1]
            x_val, y_val = extract_features_and_labels(val_fold, med_condition, modalities)
            x_val = scaler.transform(x_val)
            x_test, y_test = extract_features_and_labels(test_fold, med_condition, modalities)
            x_test = scaler.transform(x_test)

            train_data_loader = get_data_loader(x_train, y_train)
            val_data_loader = get_data_loader(x_val, y_val)
            test_data_loader = get_data_loader(x_test, y_test)

            model = train(train_data_loader, num_epochs, num_input_features, num_hidden_layers, embedding_dim, val_data_loader)

            r2, mse = test(test_data_loader, model)
            test_r2_scores.append(r2)
            test_mse_scores.append(mse)

        results[condition]["r2"] = test_r2_scores
        results[condition]["mse"] = test_mse_scores

    return results
