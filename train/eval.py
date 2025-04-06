import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import torchvision.transforms as transforms

def evaluate_model(model, test_loader, criterion=None, device='cuda'):
    """
    Evaluate the trained model on the test set.
    
    Args:
        model: Trained model
        test_loader: DataLoader for test data
        criterion: Loss function (optional)
        device: Device to run evaluation on
    
    Returns:
        test_acc: Test accuracy
        all_preds: All predictions
        all_labels: All true labels
    """
    model.eval()
    test_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for inputs, labels in tqdm(test_loader, desc="Evaluating"):
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            
            if criterion:
                loss = criterion(outputs, labels)
                test_loss += loss.item() * inputs.size(0)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    test_acc = 100 * correct / total
    print(f'Test Accuracy: {test_acc:.2f}%')
    
    if criterion and total > 0:
        test_loss = test_loss / total
        print(f'Test Loss: {test_loss:.4f}')
    
    return test_acc, np.array(all_preds), np.array(all_labels)

def calculate_per_class_metrics(all_preds, all_labels, class_names):
    """
    Calculate per-class metrics.
    
    Args:
        all_preds: All predictions
        all_labels: All true labels
        class_names: List of class names
        
    Returns:
        per_class_metrics: DataFrame with per-class metrics
    """
    class_report = classification_report(all_labels, all_preds, 
                                        target_names=class_names, 
                                        output_dict=True)
    
    per_class_metrics = pd.DataFrame(class_report).transpose()
    return per_class_metrics

def plot_confusion_matrix(all_preds, all_labels, class_names, figsize=(15, 15), save_path=None):
    """
    Plot confusion matrix.
    
    Args:
        all_preds: All predictions
        all_labels: All true labels
        class_names: List of class names
        figsize: Figure size
        save_path: Path to save the figure
    """
    cm = confusion_matrix(all_labels, all_preds)
    
    plt.figure(figsize=figsize)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, 
                yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f'Confusion matrix saved to {save_path}')
    
    plt.show()

def predict_single_card(model, image_path, class_names, device='cuda'):
    """
    Predict the class of a single card image.
    
    Args:
        model: Trained model
        image_path: Path to the card image
        class_names: List of class names
        device: Device to run prediction on
        
    Returns:
        predicted_class: Predicted class name
        confidence: Confidence of prediction
    """
    model.eval()
    
    # Prepare the transform (same as test transform)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Load and process the image
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    # Make prediction
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, prediction = torch.max(probabilities, 1)
    
    predicted_class = class_names[prediction.item()]
    confidence_value = confidence.item() * 100
    
    return predicted_class, confidence_value

def visualize_predictions(model, test_loader, class_names, num_samples=5, device='cuda', 
                         figsize=(15, 10), save_path=None):
    """
    Visualize model predictions on test samples.
    
    Args:
        model: Trained model
        test_loader: DataLoader for test data
        class_names: List of class names
        num_samples: Number of samples to visualize
        device: Device to run prediction on
        figsize: Figure size
        save_path: Path to save the figure
    """
    model.eval()
    
    # Get a batch of images
    dataiter = iter(test_loader)
    images, labels = next(dataiter)
    
    # Select a subset of images to display
    if num_samples > len(images):
        num_samples = len(images)
    
    images = images[:num_samples].to(device)
    labels = labels[:num_samples]
    
    # Get predictions
    with torch.no_grad():
        outputs = model(images)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        _, predictions = torch.max(outputs, 1)
        confidences = torch.max(probabilities, 1)[0]
    
    # Denormalize images for display
    images = images.cpu()
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    images = images * std + mean
    
    # Plot the images with predictions
    fig, axes = plt.subplots(1, num_samples, figsize=figsize)
    if num_samples == 1:
        axes = [axes]
    
    for i in range(num_samples):
        axes[i].imshow(images[i].permute(1, 2, 0).numpy())
        
        title = f"True: {class_names[labels[i]]}\n"
        title += f"Pred: {class_names[predictions[i]]}\n"
        title += f"Conf: {confidences[i]*100:.1f}%"
        
        color = "green" if predictions[i] == labels[i] else "red"
        axes[i].set_title(title, color=color)
        axes[i].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"Visualization saved to {save_path}")
    
    plt.show()

def evaluate_memorization(model, data_dir, class_names, device='cuda'):
    """
    Evaluate each original image to ensure perfect memorization.
    
    Args:
        model: Trained model
        data_dir: Directory with original card images (one per class)
        class_names: List of class names
        device: Device to run evaluation on
        
    Returns:
        result_df: DataFrame with evaluation results
    """
    model.eval()
    
    # Prepare the transform (same as test transform)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    results = []
    
    # Evaluate each original image
    for class_idx, class_name in enumerate(class_names):
        class_dir = os.path.join(data_dir, class_name)
        
        # Find the first image in the class directory
        for img_name in os.listdir(class_dir):
            if img_name.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(class_dir, img_name)
                
                # Load and process the image
                image = Image.open(img_path).convert('RGB')
                image_tensor = transform(image).unsqueeze(0).to(device)
                
                # Make prediction
                with torch.no_grad():
                    outputs = model(image_tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)
                    confidence, prediction = torch.max(probabilities, 1)
                
                # Record results
                predicted_class = class_names[prediction.item()]
                correct = predicted_class == class_name
                results.append({
                    'Class': class_name,
                    'Image': img_name,
                    'Predicted': predicted_class,
                    'Confidence': confidence.item() * 100,
                    'Correct': correct
                })
                
                # Only process the first image in each class
                break
    
    # Create DataFrame
    result_df = pd.DataFrame(results)
    
    # Calculate overall accuracy
    accuracy = result_df['Correct'].mean() * 100
    print(f"Memorization Accuracy: {accuracy:.2f}%")
    
    # Display any misclassified cards
    if accuracy < 100:
        misclassified = result_df[~result_df['Correct']]
        print("\nMisclassified Cards:")
        print(misclassified[['Class', 'Predicted', 'Confidence']])
    
    return result_df