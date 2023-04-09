import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.models as models
import torchvision.transforms as transforms

import argparse
import logging
import os
import sys

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def test(model, test_loader, criterion):
    model.eval()
    test_loss = 0
    running_corrects = 0
    
    for inputs, labels in test_loader:
        outputs = model(inputs)
        test_loss += criterion(outputs, labels).item()
        _, preds = torch.max(outputs, 1)
        running_corrects += torch.sum(preds==labels.data).item()
    
    average_accuracy = running_corrects/len(test_loader.dataset)
    average_loss = test_loss/len(test_loader.dataset)
    logger.info(f'Test set: Average loss: {average_loss}, Accuracy: {100*average_accuracy}%')
    

def train(model, train_loader, epochs, criterion, optimizer): 
    count = 0
    
    for epoch in range(epochs):
        model.train()
        
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            count += len(inputs)
            if count > 400:
                break
            
    return model 
    
def net():
    model = models.resnet50(pretrained = True)
    
    for param in model.parameters():
        param.required_grad = False 
    
    num_features = model.fc.in_features
    num_classes = 133
    model.fc = nn.Sequential(nn.Linear(num_features, 256), 
                                                nn.ReLU(),                 
                                                nn.Linear(256, 128),
                                                nn.ReLU(),
                                                nn.Linear(128,  num_classes),
                                                nn.LogSoftmax(dim=1))
    return model

def create_data_loaders(data, batch_size):
    train_path = os.path.join(data, 'train')
    test_path = os.path.join(data, 'test')
    validation_path = os.path.join(data, 'valid')
    
    train_transform = transforms.Compose([transforms.RandomHorizontalFlip(p=0.5),
                                                                          transforms.Resize(256),
                                                                          transforms.Resize((224, 224)),
                                                                          transforms.ToTensor()])

    test_transform = transforms.Compose([transforms.Resize(256),
                                                                        transforms.Resize((224, 224)),
                                                                        transforms.ToTensor()])
    
    train_dataset = torchvision.datasets.ImageFolder(root=train_path, transform=train_transform)    
    test_dataset = torchvision.datasets.ImageFolder(root=test_path, transform=test_transform)
    validation_dataset = torchvision.datasets.ImageFolder(root=validation_path, transform=test_transform)
    
    train_data_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_data_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    validation_data_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=batch_size, shuffle=False)
    
    return train_data_loader, test_data_loader, validation_data_loader

def main(args):
    model=net()
    
    loss_criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)
    
    train_data_loader, test_data_loader, _ = create_data_loaders(data=args.data_dir, batch_size=args.batch_size)
    
    model = train(model, train_data_loader, args.epochs, loss_criterion, optimizer)
    
    test(model, test_data_loader, loss_criterion)
    
    logger.info("Saving the model")
    torch.save(model.state_dict(), os.path.join(args.model_dir, 'model.pth'))
    logger.info("Model saved")

    
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    
    parser.add_argument("--batch_size", type=int, default=64, metavar="N", help="input batch size for training")
    parser.add_argument( "--test_batch_size", type=int, default=1000, metavar="N", help="input batch size for testing")
    parser.add_argument("--epochs", type=int, default=2, metavar="N", help="number of epochs to train")
    parser.add_argument("--lr", type=float, default=0.01, metavar="LR", help="learning rate")
    parser.add_argument("--data_dir", type=str, default=os.environ["SM_CHANNEL_TRAIN"], help="training data path in S3")
    parser.add_argument("--model_dir", type=str, default=os.environ["SM_MODEL_DIR"], help="location to save the model to")
    
    args=parser.parse_args()
    
    main(args)