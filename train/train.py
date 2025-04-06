import torch
import torch.nn as nn
import os
from tqdm import tqdm

def train(model, train_loader, val_loader, optimizer, 
          num_epochs=100, device='cuda', checkpoint_dir='checkpoints'):
    """
    Args:
        model: Model to train
        train_loader: DataLoader for training
        val_loader: DataLoader for validation
        optimizer: Optimizer
        num_epochs: Number of epochs (high for memorization)
        device: Device to train on
        checkpoint_dir: Directory to save checkpoints
        
    Returns:
        Trained model and history
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    model = model.to(device)
    
    # Use CrossEntropyLoss as the objective
    criterion = nn.CrossEntropyLoss()
    
    # Tracking metrics
    result = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    best_acc = 0.0
    
    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for inputs, labels in tqdm(train_loader, desc="Training"):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            train_loss += loss.item() * inputs.size(0)
        
        train_loss /= train_total
        train_acc = train_correct / train_total * 100
        result['train_loss'].append(train_loss)
        result['train_acc'].append(train_acc)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm(val_loader, desc="Validation"):
                inputs, labels = inputs.to(device), labels.to(device)
                
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                val_loss += loss.item() * inputs.size(0)
        
        val_loss /= val_total
        val_acc = 100 * val_correct / val_total
        result['val_loss'].append(val_loss)
        result['val_acc'].append(val_acc)
        
        print(f"Training Loss: {train_loss:.4f}, Training Acc: {train_acc:.2f}%")
        print(f"Validation Loss: {val_loss:.4f}, Validation Acc: {val_acc:.2f}%")
        
        # Save if this is the best model
        if val_acc > best_acc:
            best_acc = val_acc
            print(f"New best accuracy: {val_acc:.2f}%. Saving model...")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc
            }, os.path.join(checkpoint_dir, 'best_model.pth'))
            
            # Early stopping if we reach perfect accuracy
            if val_acc == 100.0:
                print("Reached 100% accuracy! Early stopping.")
                break
    
    # Save final model
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_acc': val_acc
    }, os.path.join(checkpoint_dir, 'final_model.pth'))
    
    return model, result